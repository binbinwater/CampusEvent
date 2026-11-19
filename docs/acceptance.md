# CampusEvent 验收记录

## 1. 环境与命令

| 项目 | 值 |
| --- | --- |
| 日期 | 2026-11-19 |
| 系统 | Windows |
| Python | 3.12.14 |
| Flask | 3.1.3 |
| pytest | 9.2.0 |
| 数据库 | SQLite（WAL） |
| 测试命令 | 在 `CampusEvent/` 下执行 `..\.venv\Scripts\python.exe -m pytest -q` |
| 结果 | **37 passed** |

所有测试使用独立临时数据库和固定基准时间 `2026-11-19T10:00:00`，不修改运行库。测试目录使用工作区 `tests/_runtime`，测试结束清理数据库文件。

## 2. C1–C10 验收

| 用例 | 操作 | 预期 | 实际 | 自动化证据 |
| --- | --- | --- | --- | --- |
| C1 | 管理员创建直接报名活动，容量 2 | 创建成功，可被学生浏览 | 通过 | `test_admin_can_create_activity_and_see_it` |
| C2 | 学生 A 报名直接报名活动 | 变为“已通过”并通知 | 通过；消息写入 | `test_c2_direct_registration_is_approved_and_notifies` |
| C3 | 学生 A 再次提交相同活动 | 拒绝重复有效报名 | 通过；报名仍 1 条 | `test_c3_duplicate_active_registration_is_rejected` |
| C4 | 学生 B 报满后学生 C 再报 | B 通过；C 名额不足失败 | 通过；approved=2，C 无记录 | `test_c4_capacity_counts_only_approved_and_blocks_after_full` |
| C5 | 审核型活动，学生 A 申请 | 状态待审核 | 通过；不占 approved | `test_c5_review_registration_is_pending_and_not_counted_as_approved` |
| C6 | 管理员批准 A | 变为已通过并通知 | 通过；消息新增 | `test_c6_admin_approval_changes_status_and_notifies` |
| C7 | 管理员拒绝另一待审核报名 | 变为已拒绝并通知 | 通过；消息新增 | `test_c7_admin_rejection_changes_status_and_notifies` |
| C8 | 批准操作时容量已满 | 批准失败，不超上限 | 通过；第二条保持 pending | `test_c8_approval_rechecks_capacity_and_does_not_overflow` |
| C9 | 取消待审核或已通过报名 | 已取消，统计同步 | 通过；可重新申请，历史保留 | `test_c9_student_can_cancel_pending_and_reapply`、`test_c9_student_can_cancel_approved_and_statistics_update` |
| C10 | 重启服务后查询 | 活动、报名、通知仍一致 | 通过；同一 SQLite 文件重建 app 后仍可查询 | `test_c10_activities_registrations_and_messages_survive_restart` |

## 3. 补充验收

| 检查项 | 结果 | 证据 |
| --- | --- | --- |
| 固定演示账号登录/退出、错误密码 | 通过 | `test_login_required_redirects_to_login`、`test_login_and_logout`、`test_wrong_password_does_not_create_session` |
| Student/Admin 角色隔离 | 通过 | `test_student_cannot_open_admin_pages`、`test_admin_cannot_open_student_pages` |
| 活动标题/容量/时间校验 | 通过 | `test_validation_rejects_empty_title`、`test_validation_rejects_invalid_capacity_and_time` |
| 按名称筛选 | 通过 | `test_search_filters_by_title` |
| 编辑活动持久化 | 通过 | `test_edit_activity_persists_changes` |
| 容量不能低于已通过人数 | 通过 | `test_capacity_cannot_be_lowered_below_approved` |
| 活动开始后禁止报名 | 通过 | `test_activity_start_blocks_new_registration` |
| 非本人不能取消报名 | 通过 | `test_student_cannot_cancel_another_students_registration` |
| 已拒绝后可重新申请 | 通过 | `test_reapply_after_rejection_creates_new_history_row` |
| 无报名活动可删除，有报名活动拒绝删除 | 通过 | `test_activity_without_registrations_can_be_deleted`、`test_activity_with_registrations_cannot_be_deleted` |
| 通知失败不回滚报名并留痕 | 通过 | `test_notification_failure_does_not_rollback_registration` |
| 重复审批不重复通知 | 通过 | `test_reapproval_does_not_publish_a_duplicate_notification` |
| 学生消息隔离与已读 | 通过 | `test_only_current_students_messages_are_visible`、`test_mark_all_messages_read` |
| `/campusevent` 前缀下的路由/静态资源 | 通过 | `test_application_works_under_campusevent_prefix` |
| 公网前缀部署 | 通过 | 公网 `/campusevent/` 返回 200，静态 CSS 200，登录和新建表单路径均带前缀 |

## 4. 手工验收流程

1. 以 `admin/admin123` 登录，创建“直接报名”活动（容量 2）和“管理员审核”活动。
2. 以 `student_a/student123` 登录，分别报名两个活动：直接活动显示“已通过”，审核活动显示“待审核”；站内消息各出现一条。
3. 以 `admin` 登录，在审批中心批准审核报名；学生消息新增“报名成功”记录。
4. 制造容量已满的审核场景，批准另一条待审核报名，页面提示名额已满，不更新为已通过。
5. 学生取消待审核/已通过报名，状态变“已取消”，统计减少；重新申请同一活动成功。
6. 停止并重启应用后，活动、报名、消息仍可查询。

## 5. 当前版本与 CR

- 当前版本：`baseline-v1`。
- 教师 CR 未在附件中提供，因此没有创建 `change-v2`，也没有虚构变更后 UML、回归结果或变更耗时。
- 未来 CR 到位后，按 `docs/change-impact.md` 模板补充影响分析、变更实现、回归和新标签。

## 6. 已知限制

- 固定演示账号，无注册、复杂权限和 CSRF 防护。
- 通知为同步进程内观察者；失败留痕但不自动重试。
- 没有活动软删除、备份、分页；删除有报名活动的请求会被拒绝。
- 无外部邮件/短信或第三方日历。
- SQLite 适合单机演示，不适合高并发多实例。

## 7. 结论

C1–C10 初版验收用例全部通过；核心业务、权限、校验、通知失败、消息隔离和重启持久化均有可复现的自动化证据。公网演示地址为 http://116.62.141.168/campusevent/。变更版本等待教师正式 CR。