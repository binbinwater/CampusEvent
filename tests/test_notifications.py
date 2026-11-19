from campusevent.events import MessageNotificationObserver


def test_pending_and_approved_messages_appear_in_student_inbox(
    admin_client, student_a, create_activity, fetch_one
):
    activity_id = create_activity(policy_type="review")
    student_a.post(f"/activities/{activity_id}/register")
    registration = fetch_one("SELECT id FROM registrations WHERE activity_id = ?", (activity_id,))
    admin_client.post(f"/registrations/{registration['id']}/approve")

    page = student_a.get("/messages").get_data(as_text=True)
    assert "报名已提交" in page
    assert "报名成功" in page
    assert "未读" in page
    assert "迎新志愿活动" in page


def test_only_current_students_messages_are_visible(
    admin_client, student_a, student_b, create_activity, count_rows
):
    activity_id = create_activity(policy_type="direct")
    student_a.post(f"/activities/{activity_id}/register")
    page = student_b.get("/messages").get_data(as_text=True)
    assert "报名成功" not in page
    assert "还没有站内消息" in page
    assert count_rows("messages", "student_id = ?", ("S001",)) == 1
    assert count_rows("messages", "student_id = ?", ("S002",)) == 0


def test_mark_all_messages_read(student_a, create_activity, fetch_one):
    activity_id = create_activity(policy_type="direct")
    student_a.post(f"/activities/{activity_id}/register")
    assert student_a.get("/messages").get_data(as_text=True).count("未读") >= 1

    response = student_a.post("/messages/read", follow_redirects=True)
    assert "已标记为已读" in response.get_data(as_text=True)
    row = fetch_one("SELECT is_read FROM messages WHERE student_id = 'S001'")
    assert row["is_read"] == 1


def test_notification_failure_does_not_rollback_registration(
    student_a, create_activity, fetch_one, count_rows, monkeypatch
):
    activity_id = create_activity(policy_type="direct")

    def fail_notification(self, event):
        raise RuntimeError("模拟通知故障")

    monkeypatch.setattr(MessageNotificationObserver, "handle", fail_notification)
    response = student_a.post(
        f"/activities/{activity_id}/register", follow_redirects=True
    )
    page = response.get_data(as_text=True)
    assert "报名成功，已直接通过" in page

    registration = fetch_one(
        "SELECT status FROM registrations WHERE activity_id = ? AND student_id = 'S001'",
        (activity_id,),
    )
    assert registration["status"] == "approved"
    assert count_rows("messages", "student_id = ?", ("S001",)) == 0
    failure = fetch_one(
        "SELECT * FROM notification_failures WHERE activity_id = ?", (activity_id,)
    )
    assert failure is not None
    assert "模拟通知故障" in failure["error"]


def test_reapproval_does_not_publish_a_duplicate_notification(
    admin_client, student_a, create_activity, fetch_one, count_rows
):
    activity_id = create_activity(policy_type="review")
    student_a.post(f"/activities/{activity_id}/register")
    registration = fetch_one("SELECT id FROM registrations WHERE activity_id = ?", (activity_id,))
    admin_client.post(f"/registrations/{registration['id']}/approve")
    second = admin_client.post(
        f"/registrations/{registration['id']}/approve", follow_redirects=True
    )
    assert "只有待审核报名可以批准" in second.get_data(as_text=True)
    assert count_rows("messages", "student_id = ?", ("S001",)) == 2


def test_cancelling_approved_registration_writes_cancellation_message(
    student_a, create_activity, fetch_one
):
    activity_id = create_activity(policy_type="direct")
    student_a.post(f"/activities/{activity_id}/register")
    registration = fetch_one("SELECT id FROM registrations WHERE activity_id = ?", (activity_id,))
    student_a.post(f"/registrations/{registration['id']}/cancel")

    message = fetch_one(
        "SELECT content FROM messages WHERE student_id = 'S001' ORDER BY id DESC LIMIT 1"
    )
    assert "报名已取消" in message["content"]