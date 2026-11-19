def test_c2_direct_registration_is_approved_and_notifies(
    student_a, create_activity, fetch_one, count_rows
):
    activity_id = create_activity(policy_type="direct")
    response = student_a.post(
        f"/activities/{activity_id}/register", follow_redirects=True
    )
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "报名成功，已直接通过" in page

    registration = fetch_one(
        "SELECT * FROM registrations WHERE activity_id = ? AND student_id = 'S001'",
        (activity_id,),
    )
    assert registration["status"] == "approved"
    assert count_rows("messages", "student_id = ?", ("S001",)) == 1
    message = fetch_one("SELECT content FROM messages WHERE student_id = 'S001'")
    assert "报名成功" in message["content"]


def test_c3_duplicate_active_registration_is_rejected(
    student_a, create_activity, count_rows, fetch_one
):
    activity_id = create_activity(policy_type="direct")
    student_a.post(f"/activities/{activity_id}/register")
    response = student_a.post(
        f"/activities/{activity_id}/register", follow_redirects=True
    )
    assert "不能重复提交" in response.get_data(as_text=True)
    assert count_rows("registrations", "activity_id = ?", (activity_id,)) == 1
    assert count_rows("messages", "student_id = ?", ("S001",)) == 1


def test_c4_capacity_counts_only_approved_and_blocks_after_full(
    student_a, student_b, student_c, create_activity, count_rows, fetch_one
):
    activity_id = create_activity(capacity=2, policy_type="direct")
    assert "报名成功" in student_a.post(
        f"/activities/{activity_id}/register", follow_redirects=True
    ).get_data(as_text=True)
    assert "报名成功" in student_b.post(
        f"/activities/{activity_id}/register", follow_redirects=True
    ).get_data(as_text=True)
    denied = student_c.post(
        f"/activities/{activity_id}/register", follow_redirects=True
    )
    assert "名额已满，无法报名" in denied.get_data(as_text=True)

    activity = fetch_one("SELECT capacity FROM activities WHERE id = ?", (activity_id,))
    approved = fetch_one(
        "SELECT COUNT(*) AS n FROM registrations WHERE activity_id = ? AND status = 'approved'",
        (activity_id,),
    )["n"]
    assert activity["capacity"] == 2
    assert approved == 2
    assert count_rows(
        "registrations", "activity_id = ? AND student_id = 'S003'", (activity_id,)
    ) == 0


def test_c5_review_registration_is_pending_and_not_counted_as_approved(
    student_a, create_activity, fetch_one, count_rows
):
    activity_id = create_activity(capacity=1, policy_type="review")
    response = student_a.post(
        f"/activities/{activity_id}/register", follow_redirects=True
    )
    assert "报名已提交，等待管理员审核" in response.get_data(as_text=True)

    registration = fetch_one(
        "SELECT status FROM registrations WHERE activity_id = ? AND student_id = 'S001'",
        (activity_id,),
    )
    assert registration["status"] == "pending"
    assert count_rows(
        "registrations", "activity_id = ? AND status = 'approved'", (activity_id,)
    ) == 0
    assert count_rows("messages", "student_id = ?", ("S001",)) == 1


def test_c6_admin_approval_changes_status_and_notifies(
    admin_client, student_a, create_activity, fetch_one, count_rows
):
    activity_id = create_activity(policy_type="review")
    student_a.post(f"/activities/{activity_id}/register")
    registration = fetch_one("SELECT id FROM registrations WHERE activity_id = ?", (activity_id,))

    response = admin_client.post(
        f"/registrations/{registration['id']}/approve",
        data={"next": f"/activities/{activity_id}"},
        follow_redirects=True,
    )
    assert "报名已批准" in response.get_data(as_text=True)
    row = fetch_one("SELECT status FROM registrations WHERE id = ?", (registration["id"],))
    assert row["status"] == "approved"
    messages = count_rows("messages", "student_id = ?", ("S001",))
    assert messages == 2
    approved_message = fetch_one(
        "SELECT content FROM messages WHERE student_id = 'S001' ORDER BY id DESC LIMIT 1"
    )
    assert "报名成功" in approved_message["content"]


def test_c7_admin_rejection_changes_status_and_notifies(
    admin_client, student_a, create_activity, fetch_one, count_rows
):
    activity_id = create_activity(policy_type="review")
    student_a.post(f"/activities/{activity_id}/register")
    registration = fetch_one("SELECT id FROM registrations WHERE activity_id = ?", (activity_id,))

    response = admin_client.post(
        f"/registrations/{registration['id']}/reject",
        data={"next": f"/activities/{activity_id}"},
        follow_redirects=True,
    )
    assert "报名已拒绝" in response.get_data(as_text=True)
    row = fetch_one("SELECT status FROM registrations WHERE id = ?", (registration["id"],))
    assert row["status"] == "rejected"
    message = fetch_one(
        "SELECT content FROM messages WHERE student_id = 'S001' ORDER BY id DESC LIMIT 1"
    )
    assert "报名未通过" in message["content"]
    assert count_rows("messages", "student_id = ?", ("S001",)) == 2


def test_c8_approval_rechecks_capacity_and_does_not_overflow(
    admin_client, student_a, student_b, create_activity, fetch_one, count_rows
):
    activity_id = create_activity(capacity=1, policy_type="review")
    student_a.post(f"/activities/{activity_id}/register")
    student_b.post(f"/activities/{activity_id}/register")
    first = fetch_one(
        "SELECT id FROM registrations WHERE activity_id = ? AND student_id = 'S001'",
        (activity_id,),
    )
    second = fetch_one(
        "SELECT id FROM registrations WHERE activity_id = ? AND student_id = 'S002'",
        (activity_id,),
    )

    admin_client.post(f"/registrations/{first['id']}/approve")
    response = admin_client.post(
        f"/registrations/{second['id']}/approve", follow_redirects=True
    )
    assert "名额已满，无法批准" in response.get_data(as_text=True)

    approved = count_rows(
        "registrations", "activity_id = ? AND status = 'approved'", (activity_id,)
    )
    still_pending = fetch_one(
        "SELECT status FROM registrations WHERE id = ?", (second["id"],)
    )
    assert approved == 1
    assert still_pending["status"] == "pending"


def test_c9_student_can_cancel_pending_and_reapply(
    student_a, create_activity, fetch_one, count_rows
):
    activity_id = create_activity(policy_type="review")
    student_a.post(f"/activities/{activity_id}/register")
    registration = fetch_one("SELECT id FROM registrations WHERE activity_id = ?", (activity_id,))

    response = student_a.post(
        f"/registrations/{registration['id']}/cancel", follow_redirects=True
    )
    assert "报名已取消" in response.get_data(as_text=True)
    cancelled = fetch_one("SELECT status FROM registrations WHERE id = ?", (registration["id"],))
    assert cancelled["status"] == "cancelled"

    reapply = student_a.post(
        f"/activities/{activity_id}/register", follow_redirects=True
    )
    assert "报名已提交" in reapply.get_data(as_text=True)
    assert count_rows("registrations", "activity_id = ?", (activity_id,)) == 2
    active = fetch_one(
        "SELECT status FROM registrations WHERE activity_id = ? AND student_id = 'S001' ORDER BY id DESC LIMIT 1",
        (activity_id,),
    )
    assert active["status"] == "pending"


def test_c9_student_can_cancel_approved_and_statistics_update(
    admin_client, student_a, create_activity, fetch_one
):
    activity_id = create_activity(capacity=1, policy_type="direct")
    student_a.post(f"/activities/{activity_id}/register")
    registration = fetch_one("SELECT id FROM registrations WHERE activity_id = ?", (activity_id,))

    before = admin_client.get("/").get_data(as_text=True)
    assert "名额已满" in before
    student_a.post(f"/registrations/{registration['id']}/cancel")
    after = admin_client.get("/").get_data(as_text=True)
    assert "剩余 1 个名额" in after


def test_student_cannot_cancel_another_students_registration(
    student_a, student_b, create_activity, fetch_one
):
    activity_id = create_activity(policy_type="direct")
    student_a.post(f"/activities/{activity_id}/register")
    registration = fetch_one("SELECT id FROM registrations WHERE activity_id = ?", (activity_id,))

    response = student_b.post(
        f"/registrations/{registration['id']}/cancel", follow_redirects=True
    )
    assert "只能取消自己的报名" in response.get_data(as_text=True)
    row = fetch_one("SELECT status FROM registrations WHERE id = ?", (registration["id"],))
    assert row["status"] == "approved"


def test_activity_start_blocks_new_registration(
    student_a, create_activity, count_rows
):
    activity_id = create_activity(start_at="2026-11-18T09:00")
    response = student_a.post(
        f"/activities/{activity_id}/register", follow_redirects=True
    )
    assert "活动已经开始，不能报名" in response.get_data(as_text=True)
    assert count_rows("registrations", "activity_id = ?", (activity_id,)) == 0


def test_reapply_after_rejection_creates_new_history_row(
    admin_client, student_a, create_activity, fetch_one, count_rows
):
    activity_id = create_activity(policy_type="review")
    student_a.post(f"/activities/{activity_id}/register")
    registration = fetch_one("SELECT id FROM registrations WHERE activity_id = ?", (activity_id,))
    admin_client.post(f"/registrations/{registration['id']}/reject")
    response = student_a.post(
        f"/activities/{activity_id}/register", follow_redirects=True
    )
    assert "报名已提交" in response.get_data(as_text=True)
    assert count_rows("registrations", "activity_id = ?", (activity_id,)) == 2