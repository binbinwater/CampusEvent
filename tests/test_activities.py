def test_admin_can_create_activity_and_see_it(admin_client, create_activity):
    activity_id = create_activity(title="校园歌手大赛", category="文体", capacity=3)
    page = admin_client.get("/").get_data(as_text=True)
    assert "校园歌手大赛" in page
    assert "文体" in page
    assert "直接报名" in page

    detail = admin_client.get(f"/activities/{activity_id}").get_data(as_text=True)
    assert "校园歌手大赛" in detail
    assert "已通过" in detail
    assert "报名与审批" in detail


def test_new_activity_form_requires_admin_and_shows_policy_choices(admin_client):
    page = admin_client.get("/activities/new").get_data(as_text=True)
    assert "活动名称" in page
    assert "直接报名" in page
    assert "管理员审核" in page


def test_validation_rejects_empty_title(admin_client, count_rows):
    response = admin_client.post(
        "/activities/new",
        data={
            "title": "   ",
            "category": "讲座",
            "start_at": "2026-11-21T14:00",
            "location": "报告厅",
            "capacity": "2",
            "policy_type": "direct",
        },
    )
    assert response.status_code == 400
    assert "活动名称不能为空" in response.get_data(as_text=True)
    assert count_rows("activities") == 0


def test_validation_rejects_invalid_capacity_and_time(admin_client, count_rows):
    response = admin_client.post(
        "/activities/new",
        data={
            "title": "测试活动",
            "category": "讲座",
            "start_at": "2026/11/21 14:00",
            "location": "报告厅",
            "capacity": "0",
            "policy_type": "direct",
        },
    )
    page = response.get_data(as_text=True)
    assert response.status_code == 400
    assert "活动开始时间格式不正确" in page
    assert "人数上限必须大于 0" in page
    assert count_rows("activities") == 0


def test_search_filters_by_title(admin_client, create_activity):
    create_activity(title="迎新志愿活动")
    create_activity(title="数据库讲座")
    response = admin_client.get("/?q=迎新")
    page = response.get_data(as_text=True)
    assert "迎新志愿活动" in page
    assert "数据库讲座" not in page


def test_edit_activity_persists_changes(admin_client, create_activity):
    activity_id = create_activity(title="旧活动", capacity=2)
    response = admin_client.post(
        f"/activities/{activity_id}/edit",
        data={
            "title": "新活动名称",
            "category": "讲座",
            "start_at": "2026-11-25T09:30",
            "location": "新地点",
            "capacity": "5",
            "policy_type": "review",
        },
    )
    assert response.status_code == 303
    page = admin_client.get(f"/activities/{activity_id}").get_data(as_text=True)
    assert "新活动名称" in page
    assert "2026-11-25 09:30" in page
    assert "新地点" in page
    assert "5 人" in page


def test_capacity_cannot_be_lowered_below_approved(
    admin_client, create_activity, student_a, student_b, fetch_one
):
    activity_id = create_activity(capacity=2, policy_type="direct")
    student_a.post(f"/activities/{activity_id}/register")
    student_b.post(f"/activities/{activity_id}/register")

    response = admin_client.post(
        f"/activities/{activity_id}/edit",
        data={
            "title": "容量冲突活动",
            "category": "讲座",
            "start_at": "2026-11-21T14:00",
            "location": "报告厅",
            "capacity": "1",
            "policy_type": "direct",
        },
    )
    assert response.status_code == 400
    assert "人数上限不能低于当前已通过人数" in response.get_data(as_text=True)
    row = fetch_one("SELECT capacity FROM activities WHERE id = ?", (activity_id,))
    assert row["capacity"] == 2


def test_activity_without_registrations_can_be_deleted(admin_client, create_activity, count_rows):
    activity_id = create_activity()
    confirm = admin_client.get(f"/activities/{activity_id}/delete")
    assert confirm.status_code == 200
    assert "确认删除活动" in confirm.get_data(as_text=True)

    response = admin_client.post(f"/activities/{activity_id}/delete")
    assert response.status_code == 303
    assert count_rows("activities") == 0


def test_activity_with_registrations_cannot_be_deleted(
    admin_client, create_activity, student_a, count_rows
):
    activity_id = create_activity()
    student_a.post(f"/activities/{activity_id}/register")

    confirm = admin_client.get(f"/activities/{activity_id}/delete")
    page = confirm.get_data(as_text=True)
    assert "已有 1 条报名记录" in page
    assert 'type="submit">确认删除' not in page

    response = admin_client.post(f"/activities/{activity_id}/delete", follow_redirects=True)
    assert "不能删除" in response.get_data(as_text=True)
    assert count_rows("activities") == 1


def test_admin_dashboard_shows_pending_approval(admin_client, create_activity, student_a):
    activity_id = create_activity(policy_type="review")
    student_a.post(f"/activities/{activity_id}/register")
    page = admin_client.get("/admin").get_data(as_text=True)
    assert "待审核报名" in page
    assert "张同学" in page
    assert "迎新志愿活动" in page