# CampusEvent 设计说明（baseline-v1）

## 1. 系统结构

```text
浏览器（Jinja2 页面）
        ↓
Flask 路由 / 固定演示账号会话
        ↓
ActivityService / RegistrationService
        ↓                         ↘
Repository（SQLite）          RegistrationPolicy（策略）
        ↓                         
SQLite 活动、报名、消息表
        ↓
EventPublisher → MessageNotificationObserver → messages
```

- 应用工厂：`create_app()`，便于测试注入临时数据库和固定时钟。
- 数据访问：`ActivityRepository`、`RegistrationRepository`、`MessageRepository`、`NotificationFailureRepository`。
- 业务服务：`ActivityService`、`RegistrationService`。
- SQL 参数化；写操作使用显式事务；审批使用 `BEGIN IMMEDIATE` 防止并发超额。
- 当前状态：仅初版 `baseline-v1`；没有教师 CR，因此未创建 `change-v2`。

## 2. 职责划分

| 对象 | 职责 |
| --- | --- |
| Student | 学生身份，只读展示；不包含权限逻辑 |
| Activity | 活动数据、容量、报名方式和统计派生值 |
| Registration | 一条报名及其状态、历史记录 |
| Message | 站内通知 |
| ActivityService | 活动创建、编辑、删除，及容量不可低于已通过人数 |
| RegistrationService | 报名、取消、批准、拒绝；公共规则和事务边界 |
| RegistrationPolicy | 稳定策略接口，只决定新报名初始状态 |
| DirectRegistrationPolicy | 初始状态 approved |
| ReviewRegistrationPolicy | 初始状态 pending |
| EventPublisher | 向订阅者发布已提交的报名事件，隔离通知失败 |
| MessageNotificationObserver | 将报名事件写入站内消息 |
| Repository | 封装 SQL 与模型转换，不负责业务决策 |

## 3. 策略模式

```text
RegistrationPolicy (interface)
    ├── DirectRegistrationPolicy : initial_status = approved
    └── ReviewRegistrationPolicy : initial_status = pending
```

### 为什么采用

1. 直接报名和审核报名的差异只在“初始状态”，将其抽为稳定接口后，`RegistrationService` 不需要写 `if policy_type == 'direct'` 或 `if policy_type == 'review'`。
2. 新增报名规则时增加一个策略类并在注册表登记，避免修改核心报名流程。
3. 策略对象通过 `policy_for(activity.policy_type)` 选择，非法类型在服务层被拒绝。

### 名额检查的位置

**名额检查作为公共规则由 `RegistrationService` 执行，而不是由策略承担。** 理由：

- 直接报名、审核型报名提交、管理员批准都要检查容量。
- 批准时也没有“策略”参与；如果把容量检查放进策略，会让审批路径依赖某个策略对象，职责反而混乱。
- 策略保持无状态、只回答“新报名初始状态”，容易单独测试；容量规则集中在一处，便于事务和并发控制。

## 4. 观察者模式与通知事务

```text
RegistrationService
   └─(commit)─> EventPublisher.publish(event)
                    └─> MessageNotificationObserver.handle(event)
                            └─> MessageRepository.add(...)
```

- 报名/审批/取消先提交数据库事务，再发布事件。通知失败不会回滚已合法提交的报名。
- `EventPublisher` 捕获每个订阅者异常，记录应用日志，并写入 `notification_failures` 表。
- 只有状态成功转换后才发布事件；重复点击审批时状态已不是 pending，服务拒绝，因此不会重复写入同一条审核消息。
- 通知内容由事件类型决定：approved / pending / rejected / cancelled。
- 设计取舍：没有引入消息队列或 outbox 重试框架；本实验是单机演示，使用数据库留痕已足以解释事务边界。生产环境应使用 outbox + 重试。

## 5. 数据模型与约束

| 表 | 关键字段 | 约束 |
| --- | --- | --- |
| students | student_id, name | student_id 主键 |
| activities | title, category, start_at, location, capacity, policy_type | capacity 1–10000；policy_type 限 direct/review |
| registrations | activity_id, student_id, status, created_at, updated_at | status 限四种；部分唯一索引限制有效报名 |
| messages | student_id, activity_id, content, is_read | 学生/活动通知 |
| notification_failures | event_type, error, IDs, created_at | 通知失败留痕 |

关键索引：

```sql
CREATE UNIQUE INDEX uq_registration_active
ON registrations (activity_id, student_id)
WHERE status IN ('pending', 'approved');
```

数据库约束是第二层防线；正常用户输入由 Flask 表单/服务层先校验并给出中文错误。

## 6. 关键事务与并发

- 报名：`BEGIN IMMEDIATE` → 读取活动、有效报名、已通过人数 → 插入 → `COMMIT`。
- 审批：`BEGIN IMMEDIATE` → 读取并确认 `pending` → 统计 `approved` → 复核容量 → 更新 → `COMMIT`。
- SQLite 开启 WAL 和 `busy_timeout`，减少短写锁冲突。
- 部分唯一索引使并发重复报名也无法插入第二条有效记录。
- 通知写入在事务提交之后，有自己的短事务。

## 7. 设计取舍

| 取舍 | 选择 | 代价 |
| --- | --- | --- |
| 删除已有报名活动 | 拒绝物理删除 | 没有活动归档/软删除；需要保留历史 |
| 权限 | 固定演示账号 + Session | 不是生产级认证，没有 CSRF/审计 |
| 状态表示 | 字符串枚举 | 直观、易查；缺少数据库枚举类型 |
| 通知 | 进程内观察者 | 简单可测；没有重试和外部投递 |
| 容量 | 公共规则 | 策略保持纯粹；容量逻辑不随策略变化 |
| 活动规则 | 无报名截止时间，以活动开始时间为截止 | 初始需求没有额外字段 |

## 8. 测试设计

- 路由级测试使用 Flask `test_client`，每个测试独立 SQLite 临时库。
- 固定 `NOW_OVERRIDE = 2026-11-19T10:00:00`，确保“已开始/未开始”可重复。
- 覆盖固定角色权限、活动校验、C1–C10、容量边界、重复和重新申请、通知失败、重复审批、消息隔离、标记已读、前缀部署、重启持久化。
- 当前结果：**37 passed**。

## 9. 扩展点与 change-v2

教师 CR 尚未发布，因此没有变更版本。未来如果 CR 为“取消活动”“报名截止时间”或“候补队列”，现有扩展点为：

1. 新增策略类实现 `RegistrationPolicy` 并注册，不改现有报名流程。
2. 新增事件类型和观察者订阅；`EventPublisher` 已隔离通知失败。
3. 新增活动/报名字段和迁移 SQL，再补回归测试。
4. 保持容量公共规则和 `BEGIN IMMEDIATE` 审批事务，避免变更破坏边界。

详见 [change-impact.md](change-impact.md)。

## 10. UML

- [用例图](uml/use-case.png)
- [类图](uml/class.png)
- [报名时序图](uml/sequence-register.png)
- [审批时序图](uml/sequence-approve.png)

图片由 `uml/render_diagrams.py` 生成，便于后续 CR 变更时更新。