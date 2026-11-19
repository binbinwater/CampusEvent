def test_login_required_redirects_to_login(app):
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_login_page_lists_fixed_demo_accounts(app):
    page = app.test_client().get("/login").get_data(as_text=True)
    for username in ("student_a", "student_b", "student_c", "admin"):
        assert username in page
    assert "student123" in page
    assert "admin123" in page


def test_wrong_password_does_not_create_session(app):
    client = app.test_client()
    response = client.post(
        "/login",
        data={"username": "student_a", "password": "wrong"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "用户名或密码错误" in response.get_data(as_text=True)
    assert client.get("/").status_code == 302


def test_login_and_logout(app):
    client = app.test_client()
    response = client.post(
        "/login",
        data={"username": "student_a", "password": "student123"},
        follow_redirects=True,
    )
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "张同学" in page
    assert "登录成功" in page

    response = client.post("/logout", follow_redirects=True)
    assert "已退出登录" in response.get_data(as_text=True)
    assert client.get("/").status_code == 302


def test_student_cannot_open_admin_pages(student_a):
    assert student_a.get("/admin").status_code == 403
    assert student_a.get("/activities/new").status_code == 403


def test_admin_cannot_open_student_pages(admin_client, create_activity):
    activity_id = create_activity()
    assert admin_client.get("/my/registrations").status_code == 403
    assert admin_client.get("/messages").status_code == 403
    response = admin_client.post(f"/activities/{activity_id}/register")
    assert response.status_code == 403


def test_unauthenticated_admin_page_redirects_to_login(app):
    response = app.test_client().get("/admin")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")