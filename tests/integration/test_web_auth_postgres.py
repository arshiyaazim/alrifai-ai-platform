"""Local-only integration coverage for the approved web authentication foundation."""

from __future__ import annotations

import os
from uuid import uuid4

import pytest

psycopg = pytest.importorskip("psycopg")
from fastapi.testclient import TestClient  # noqa: E402

from src.alrifai.auth.service import create_owner, create_pending_account  # noqa: E402
from src.alrifai.web.app import app  # noqa: E402


pytestmark = pytest.mark.skipif(
    os.getenv("ALRIFAI_TEST_DATABASE_URL") is None
    or os.getenv("ALRIFAI_TEST_DATABASE_ISOLATED") != "1",
    reason="isolated local PostgreSQL test database is not configured",
)


@pytest.fixture
def database_url() -> str:
    return os.environ["ALRIFAI_TEST_DATABASE_URL"]


@pytest.fixture
def isolated_auth_data(database_url: str):
    with psycopg.connect(database_url) as connection:
        with connection.transaction():
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM auth_sessions")
                cursor.execute("DELETE FROM auth_password_resets")
                cursor.execute("DELETE FROM auth_password_credentials")
                cursor.execute("DELETE FROM auth_principal_roles")
                cursor.execute("DELETE FROM audit_log WHERE entity_type='AUTHENTICATION'")
                cursor.execute("DELETE FROM auth_principals")
    yield
    with psycopg.connect(database_url) as connection:
        with connection.transaction():
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM auth_sessions")
                cursor.execute("DELETE FROM auth_password_resets")
                cursor.execute("DELETE FROM auth_password_credentials")
                cursor.execute("DELETE FROM auth_principal_roles")
                cursor.execute("DELETE FROM audit_log WHERE entity_type='AUTHENTICATION'")
                cursor.execute("DELETE FROM auth_principals")


def test_owner_bootstrap_is_unique_and_password_is_argon2(database_url: str, isolated_auth_data):
    password = "development-" + uuid4().hex + "!"
    with psycopg.connect(database_url) as connection:
        owner_id = create_owner(connection, "azimpolcu", password)
        with pytest.raises(ValueError, match="already exists"):
            create_owner(connection, "azimpolcu", "other-" + uuid4().hex + "!")
        row = connection.execute(
            "SELECT principal_type, status, must_change_password, password_hash FROM auth_principals p JOIN auth_password_credentials c USING (principal_id) WHERE p.principal_id=%s",
            (owner_id,),
        ).fetchone()
        assert row[:3] == ("OWNER", "active", True)
        assert row[3].startswith("$argon2id$")


def test_web_login_owner_dashboard_and_logout(database_url: str, isolated_auth_data, monkeypatch: pytest.MonkeyPatch):
    password = "development-" + uuid4().hex + "!"
    with psycopg.connect(database_url) as connection:
        create_owner(connection, "azimpolcu", password)
    monkeypatch.setenv("ALRIFAI_DATABASE_URL", database_url)
    monkeypatch.setenv("ALRIFAI_OPEN_WEBUI_URL", "/open-webui/")
    with TestClient(app) as client:
        assert client.get("/owner", follow_redirects=False).status_code == 303
        bad = client.post("/login", data={"username": "azimpolcu", "password": "wrong-" + uuid4().hex})
        assert bad.status_code == 200
        assert "Invalid username or password" in bad.text
        good = client.post("/login", data={"username": "azimpolcu", "password": password}, follow_redirects=False)
        assert good.status_code == 303
        assert good.headers["location"] == "/change-password"
        csrf = client.cookies.get("alrifai_csrf")
        changed_password = "changed-" + uuid4().hex + "!"
        changed = client.post("/change-password", data={"password": changed_password, "confirmation": changed_password, "csrf_token": csrf}, follow_redirects=False)
        assert changed.status_code == 303
        assert changed.headers["location"] == "/home"
        dashboard = client.get("/home")
        assert dashboard.status_code == 200
        assert "Open WebUI AI Chat" in dashboard.text
        assert "src='/open-webui/'" in dashboard.text
        assert "href='/admin'" in dashboard.text
        logged_out = client.post("/logout", data={"csrf_token": csrf}, follow_redirects=False)
        assert logged_out.status_code == 303
    assert client.get("/owner", follow_redirects=False).status_code == 303


def test_signup_cannot_create_privileged_principal(database_url: str, isolated_auth_data, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ALRIFAI_DATABASE_URL", database_url)
    username = "public-" + uuid4().hex[:10]
    with TestClient(app) as client:
        response = client.post("/signup", data={"username": username, "password": "public-" + uuid4().hex + "!"})
        assert response.status_code == 200
    with psycopg.connect(database_url) as connection:
        row = connection.execute("SELECT principal_type, status FROM auth_principals p JOIN auth_password_credentials c USING (principal_id) WHERE c.username=%s", (username,)).fetchone()
        assert row == ("APPLICANT", "pending")


def test_owner_account_management_and_other_user_reset(database_url: str, isolated_auth_data, monkeypatch: pytest.MonkeyPatch):
    owner_password = "owner-" + uuid4().hex + "!"
    owner_new_password = "owner-new-" + uuid4().hex + "!"
    owner_final_password = "owner-final-" + uuid4().hex + "!"
    other_password = "other-" + uuid4().hex + "!"
    other_new_password = "other-new-" + uuid4().hex + "!"
    with psycopg.connect(database_url) as connection:
        create_owner(connection, "azimpolcu", owner_password)
        other_id = create_pending_account(connection, "ordinary-user", other_password)
        connection.execute("UPDATE auth_principals SET status='active', must_change_password=false WHERE principal_id=%s", (other_id,))
        connection.commit()
    monkeypatch.setenv("ALRIFAI_DATABASE_URL", database_url)
    with TestClient(app) as first_owner, TestClient(app) as second_owner:
        first_owner.post("/login", data={"username": "azimpolcu", "password": owner_password}, follow_redirects=False)
        csrf = first_owner.cookies.get("alrifai_csrf")
        first_owner.post("/change-password", data={"password": owner_new_password, "confirmation": owner_new_password, "csrf_token": csrf}, follow_redirects=False)
        second_owner.post("/login", data={"username": "azimpolcu", "password": owner_new_password}, follow_redirects=False)
        second_csrf = second_owner.cookies.get("alrifai_csrf")

        dashboard = second_owner.get("/owner")
        assert "View account" in dashboard.text
        assert "Edit account" in dashboard.text
        assert "Change password" in dashboard.text

        wrong = second_owner.post("/owner/account/password", data={"current_password": owner_password, "new_password": owner_new_password, "confirmation": owner_new_password, "csrf_token": second_csrf})
        assert "current password is incorrect" in wrong.text
        changed = second_owner.post("/owner/account/password", data={"current_password": owner_new_password, "new_password": owner_final_password, "confirmation": owner_final_password, "csrf_token": second_csrf}, follow_redirects=False)
        assert changed.status_code == 303
        renamed = second_owner.post("/owner/account/edit", data={"username": "owner-renamed", "csrf_token": second_csrf}, follow_redirects=False)
        assert renamed.status_code == 303
        reset = second_owner.post(f"/owner/users/{other_id}/password", data={"new_password": other_new_password, "confirmation": other_new_password, "csrf_token": second_csrf}, follow_redirects=False)
        assert reset.status_code == 303

        # The first Owner session is revoked by the password change.
        assert first_owner.get("/owner", follow_redirects=False).status_code == 303

    with psycopg.connect(database_url) as connection:
        owner_row = connection.execute("SELECT principal_type, username FROM auth_principals p JOIN auth_password_credentials c USING (principal_id) WHERE p.principal_type='OWNER'").fetchone()
        assert owner_row == ("OWNER", "owner-renamed")
        other_row = connection.execute("SELECT principal_id FROM auth_principals WHERE principal_id=%s", (other_id,)).fetchone()
        assert other_row is not None
    with TestClient(app) as client:
        monkeypatch.setenv("ALRIFAI_DATABASE_URL", database_url)
        old_username = client.post("/login", data={"username": "azimpolcu", "password": owner_final_password})
        assert old_username.status_code == 200
        assert "Invalid username or password" in old_username.text
        old_owner_password = client.post("/login", data={"username": "owner-renamed", "password": owner_new_password})
        assert old_owner_password.status_code == 200
        assert "Invalid username or password" in old_owner_password.text
        assert client.post("/login", data={"username": "owner-renamed", "password": owner_final_password}, follow_redirects=False).status_code == 303
    with TestClient(app) as ordinary:
        old_other = ordinary.post("/login", data={"username": "ordinary-user", "password": other_password})
        assert old_other.status_code == 200
        assert "Invalid username or password" in old_other.text
        reset_other = ordinary.post("/login", data={"username": "ordinary-user", "password": other_new_password}, follow_redirects=False)
        assert reset_other.status_code == 303
        assert reset_other.headers["location"] == "/change-password"
        assert ordinary.get("/owner", follow_redirects=False).status_code == 303
        assert ordinary.get("/admin", follow_redirects=False).status_code == 303
