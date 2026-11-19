from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.test import Client
from werkzeug.wrappers import Response

from campusevent import create_app


def test_application_works_under_campusevent_prefix(db_path):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(db_path),
            "SECRET_KEY": "prefix-test",
            "NOW_OVERRIDE": "2026-11-19T10:00:00",
        }
    )
    application = DispatcherMiddleware(
        lambda environ, start_response: Response("Not Found", status=404)(
            environ, start_response
        ),
        {"/campusevent": app},
    )
    client = Client(application, Response)

    login_page = client.get("/campusevent/login")
    assert login_page.status_code == 200
    html = login_page.get_data(as_text=True)
    assert 'action="/campusevent/login"' in html
    assert 'href="/campusevent/static/style.css"' in html

    response = client.post(
        "/campusevent/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "活动列表" in response.get_data(as_text=True)
    assert 'action="/campusevent/logout"' in response.get_data(as_text=True)

    new_form = client.get("/campusevent/activities/new")
    assert new_form.status_code == 200
    assert 'action="/campusevent/activities/new"' in new_form.get_data(as_text=True)