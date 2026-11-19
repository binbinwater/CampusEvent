# CampusEvent 校园活动报名与管理系统

CampusEvent 是《软件工程》实验二的校园活动报名与管理系统。管理员发布活动并处理审核型报名，学生浏览活动、报名、取消报名并接收站内消息。

- GitHub 仓库：<https://github.com/binbinwater/CampusEvent>
- 公网 Web 地址：<http://116.62.141.168/campusevent/>
- 本地 Web 地址：<http://127.0.0.1:5001>
- 当前版本：`baseline-v1`（教师 CR 尚未发布，未创建 `change-v2`）

## 1. 技术栈与设计模式

- Python 3.12 / Flask 3.1 / SQLite（WAL）
- Jinja2 + 原生 CSS，无外部 CDN
- pytest
- **策略模式**：`RegistrationPolicy` 抽象下有直接报名和审核报名两种实现。
- **观察者模式**：报名事务提交后发布 `RegistrationEvent`，`MessageNotificationObserver` 写站内消息；通知失败不回滚报名，并记录到 `notification_failures`。
- 容量检查作为公共规则放在 `RegistrationService`，审批使用 `BEGIN IMMEDIATE` 事务复核，防止超额批准。
- 唯一部分索引保证同一活动/学生最多一条待审核或已通过报名。

## 2. 从零开始运行

### Windows PowerShell

```powershell
cd CampusEvent
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app run.py init-db
.\.venv\Scripts\python.exe run.py
```

### macOS / Linux

```bash
cd CampusEvent
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m flask --app run.py init-db
.venv/bin/python run.py
```

访问 <http://127.0.0.1:5001>。数据库位于 `instance/campusevent.sqlite3`，首次启动也会自动创建表和演示学生。`init-db` 可安全重复执行。

### 固定演示账号

| 用户名 | 密码 | 身份 |
| --- | --- | --- |
| student_a | student123 | 学生 A（张同学 / S001） |
| student_b | student123 | 学生 B（李同学 / S002） |
| student_c | student123 | 学生 C（王同学 / S003） |
| admin | admin123 | 管理员 |

这是课程演示系统，密码仅用于本地/课堂验收；生产使用需要替换认证方案。

## 3. 运行测试

```powershell
cd CampusEvent
..\.venv\Scripts\python.exe -m pytest -q
```

若使用项目自己的虚拟环境：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

当前结果：**37 passed**。覆盖 C1–C10、角色权限、表单校验、容量边界、通知失败、重复通知、消息隔离、前缀部署和重启持久化。测试使用独立临时数据库，不修改运行库。

### 公网部署

公网演示：<http://116.62.141.168/campusevent/>

部署在 Ubuntu 24.04 云服务器，使用 Nginx 反向代理到 Gunicorn。应用目录为 `/opt/campusevent`，systemd 服务名为 `campusevent`，端口 `127.0.0.1:8001`，公网前缀 `/campusevent/`；SQLite 位于 `/opt/campusevent/instance/campusevent.sqlite3`，服务器时区为 `Asia/Shanghai`。StudyTask 实验一仍保留在同服务器根路径。

```bash
systemctl status campusevent
systemctl restart campusevent
nginx -t
systemctl reload nginx
```

公网演示使用固定账号，登录页公开展示演示密码，只适合课程验收，不应存放真实个人信息。

## 4. 功能范围

| 需求 | 实现 |
| --- | --- |
| 活动管理 | 管理员创建、编辑、删除确认；删除已有报名活动被拒绝 |
| 活动浏览 | 列表、详情、按名称筛选 |
| 报名方式 | 直接报名 / 管理员审核 |
| 报名与取消 | 学生报名；只能取消自己的待审核/已通过报名 |
| 审批 | 管理员批准/拒绝待审核；批准时复核名额 |
| 状态 | pending / approved / rejected / cancelled |
| 站内通知 | 报名、审核、取消结果写入学生消息列表 |
| 统计 | 已通过、待审核、剩余名额 |

**范围外**：账号注册、复杂权限、真实邮件/短信、第三方登录、签到、支付、移动 App、第三方日历。

## 5. 项目结构

```text
CampusEvent/
├── run.py
├── wsgi.py                       # 支持 /campusevent 前缀部署
├── requirements.txt
├── requirements-deploy.txt
├── pytest.ini
├── README.md
├── AI_DEV_LOG.md
├── docs/
│   ├── requirements-analysis.md
│   ├── design.md
│   ├── acceptance.md
│   ├── change-impact.md
│   ├── report/                   # 项目总结报告
│   └── uml/                      # 用例图、类图、两张时序图
├── deploy/                       # systemd 与 Nginx 前缀配置参考
├── campusevent/
│   ├── auth.py
│   ├── db.py
│   ├── events.py
│   ├── forms.py
│   ├── models.py
│   ├── policies.py
│   ├── repositories.py
│   ├── routes.py
│   ├── services.py
│   ├── schema.sql
│   ├── templates/
│   └── static/style.css
└── tests/
```

## 6. 关键设计

- **策略选择**：报名方式字段为 `direct`/`review`，由 `policy_for()` 选择策略；服务只调用 `initial_status()`。
- **容量公共规则**：直接报名和审核申请都检查当前 `approved` 数；审批在立即事务中再次检查。
- **通知失败边界**：报名/审批/取消事务提交后发布事件；失败仅留痕。
- **删除策略**：有报名历史的活动拒绝物理删除，保留历史。
- **重复通知**：只有状态从 pending 成功转换才发布审批事件；再次审批会失败。
- **权限**：固定账号 + Session；管理员和学生的路由分别校验角色。

详细说明见 [设计文档](docs/design.md) 和 [需求分析](docs/requirements-analysis.md)。

## 7. 提交材料

- [需求分析](docs/requirements-analysis.md)
- [设计说明](docs/design.md)
- [UML 图](docs/uml/)
- [验收记录 C1–C10](docs/acceptance.md)
- [变更影响分析（CR 待发布）](docs/change-impact.md)
- [AI 协作记录](AI_DEV_LOG.md)
- [项目总结报告 PDF](docs/report/CampusEvent项目总结.pdf)、[DOCX](docs/report/CampusEvent项目总结.docx)
- [演示 PPT](docs/report/CampusEvent演示.pptx)
- 自动化测试：`tests/`

## 8. 当前版本与已知限制

- 当前只有 `baseline-v1`；附件没有教师 CR，因此没有 `change-v2`，也没有伪造变更后指标。
- 固定演示账号，无注册、复杂权限、CSRF、防暴力破解和 HTTPS。
- 通知为同步观察者，失败留痕但不自动重试。
- SQLite 适合单机演示；无分页、备份和软删除。
- 公开部署时必须自行增加访问控制，避免把演示系统当成生产系统使用。