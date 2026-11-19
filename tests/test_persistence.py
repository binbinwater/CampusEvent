from campusevent import create_app


def test_c10_activities_registrations_and_messages_survive_restart(
    db_path, student_a, create_activity, fetch_one
):
    activity_id = create_activity(title="重启后仍存在的活动", policy_type="review")
    student_a.post(f"/activities/{activity_id}/register")
    registration = fetch_one("SELECT id, status FROM registrations WHERE activity_id = ?", (activity_id,))
    assert registration["status"] == "pending"

    restarted = create_app(
        {
            "TESTING": True,
            "DATABASE": str(db_path),
            "SECRET_KEY": "test-secret",
            "NOW_OVERRIDE": "2026-11-19T10:00:00",
        }
    )
    client = restarted.test_client()
    client.post(
        "/login",
        data={"username": "student_a", "password": "student123"},
        follow_redirects=True,
    )

    activity_page = client.get(f"/activities/{activity_id}").get_data(as_text=True)
    assert "重启后仍存在的活动" in activity_page
    assert "待审核" in activity_page

    messages_page = client.get("/messages").get_data(as_text=True)
    assert "报名已提交" in messages_page
    assert "迎新志愿活动" not in messages_page
    assert "重启后仍存在的活动" in messages_page

    my_page = client.get("/my/registrations").get_data(as_text=True)
    assert "重启后仍存在的活动" in my_page
    assert "待审核" in my_page