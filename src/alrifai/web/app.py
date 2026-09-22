"""Small local web entrypoint for the first AL-RIFAI authenticated workflow."""

from __future__ import annotations

import html
import os
import threading
import time
from contextlib import contextmanager
from typing import Iterator
from urllib.parse import quote, urlsplit
from uuid import UUID

import psycopg
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from src.alrifai.ai_runtime.config import (
    AiConfigError,
    GatewayAuthMode,
    GatewayConfig,
    GatewayType,
)
from src.alrifai.ai_runtime.secrets import SecretResolver
from src.alrifai.ai_runtime.service import AiRuntimeService
from src.alrifai.ai_runtime.stores import InMemoryAiRuntimeStore, PostgresAiRuntimeStore
from src.alrifai.auth.service import (
    AuthenticationError,
    create_pending_account,
    authenticate,
    change_password,
    load_session,
    normalize_username,
    revoke_session,
    reset_user_password,
    update_username,
    _audit,
    _hash_token,
)
from src.alrifai.authorization.policy import PrincipalType, require_capability, Capability


app = FastAPI(title="AL-RIFAI AI Operations Platform")
_LOGIN_ATTEMPTS: dict[str, list[float]] = {}
_LOGIN_LOCK = threading.Lock()
_MAX_ATTEMPTS = 10
_WINDOW_SECONDS = 900


@contextmanager
def database() -> Iterator[psycopg.Connection]:
    url = os.getenv("ALRIFAI_DATABASE_URL")
    if not url:
        raise RuntimeError("ALRIFAI_DATABASE_URL is not configured")
    with psycopg.connect(url) as connection:
        yield connection


def page(title: str, body: str, message: str = "") -> HTMLResponse:
    notice = f'<div class="notice">{html.escape(message)}</div>' if message else ""
    return HTMLResponse(
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{html.escape(title)} · AL-RIFAI</title><style>{CSS}</style></head>"
        f"<body><main class='shell'>{notice}{body}</main></body></html>"
    )


def _attempt_allowed(key: str) -> bool:
    now = time.monotonic()
    with _LOGIN_LOCK:
        attempts = [stamp for stamp in _LOGIN_ATTEMPTS.get(key, []) if now - stamp < _WINDOW_SECONDS]
        if len(attempts) >= _MAX_ATTEMPTS:
            _LOGIN_ATTEMPTS[key] = attempts
            return False
        attempts.append(now)
        _LOGIN_ATTEMPTS[key] = attempts
        return True


def _session(request: Request):
    token = request.cookies.get("alrifai_session")
    if not token:
        return None
    try:
        with database() as connection:
            return load_session(connection, token)
    except (RuntimeError, psycopg.Error):
        return None


def _owner(request: Request):
    session = _session(request)
    if session is None:
        return None
    principal, csrf_hash = session
    if principal.principal_type is not PrincipalType.OWNER:
        return None
    require_capability(principal, Capability.MANAGE_USERS)
    return principal, csrf_hash


def _admin(request: Request):
    session = _session(request)
    if session is None:
        return None
    principal, csrf_hash = session
    if principal.principal_type not in {PrincipalType.OWNER, PrincipalType.ADMIN}:
        return None
    return principal, csrf_hash


def _owner_token(request: Request) -> tuple[str, str] | None:
    if _owner(request) is None:
        return None
    return request.cookies.get("alrifai_session", ""), request.cookies.get("alrifai_csrf", "")


def _cookie_domain() -> str | None:
    value = os.getenv("ALRIFAI_COOKIE_DOMAIN", "").strip()
    if value and value != ".alrifai.iamazim.com":
        raise RuntimeError("ALRIFAI_COOKIE_DOMAIN must be .alrifai.iamazim.com")
    return value or None


def _safe_return_url(value: str) -> str | None:
    if not value:
        return None
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme != "https" or parsed.hostname not in {"alrifai.iamazim.com", "ai.alrifai.iamazim.com"}:
            return None
        if parsed.username or parsed.password or parsed.fragment:
            return None
        return value
    if not value.startswith("/") or value.startswith("//") or parsed.fragment:
        return None
    return value


def _return_field(value: str) -> str:
    target = _safe_return_url(value)
    return f"<input type='hidden' name='return_to' value='{html.escape(target, quote=True)}'>" if target else ""


def _return_query(value: str) -> str:
    target = _safe_return_url(value)
    return f"?return_to={quote(target, safe='')}" if target else ""


@app.get("/internal/auth-check", include_in_schema=False)
def auth_check(request: Request) -> Response:
    return Response(status_code=204 if _session(request) is not None else 401)


@app.get("/health", response_class=HTMLResponse)
def health() -> HTMLResponse:
    try:
        with database() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        return HTMLResponse("ok")
    except (RuntimeError, psycopg.Error):
        return HTMLResponse("database unavailable", status_code=503)


@app.get("/", response_class=HTMLResponse)
def home(message: str = "", return_to: str = "") -> HTMLResponse:
    target = _safe_return_url(return_to)
    if return_to and target is None:
        message = "Invalid return destination."
    return page("Sign in", f"""
        <section class='card narrow'><div class='brand'>AL-RIFAI</div>
        <p class='muted'>AI Operations Platform</p><h1>Sign in</h1>
        <form method='post' action='/login'>
          {_return_field(target or '')}
          <label>Username<input name='username' autocomplete='username' required></label>
          <label>Password<input id='password' name='password' type='password' autocomplete='current-password' required></label>
          <label class='check'><input type='checkbox' onclick="document.getElementById('password').type=this.checked?'text':'password'"> Show password</label>
          <button type='submit'>Sign in</button>
        </form><nav><a href='/signup'>Create account</a><a href='/forgot-password'>Forgot password?</a></nav></section>
    """, message)


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), return_to: str = Form("")) -> HTMLResponse:
    target = _safe_return_url(return_to)
    if return_to and target is None:
        return home("Invalid return destination.")
    key = f"{request.client.host if request.client else 'unknown'}:{username.strip().casefold()}"
    if not _attempt_allowed(key):
        return home("Too many attempts. Try again later.", target or "")
    try:
        with database() as connection:
            result = authenticate(connection, username, password)
    except AuthenticationError:
        return home("Invalid username or password.", target or "")
    except (RuntimeError, psycopg.Error):
        return home("Authentication is temporarily unavailable.", target or "")
    response_target = "/change-password" + _return_query(target or "") if result.must_change_password else (target or "/home")
    response = RedirectResponse(response_target, status_code=303)
    secure = os.getenv("ALRIFAI_ENV", "local").lower() not in {"local", "development", "dev"}
    response.set_cookie("alrifai_session", result.session_token, domain=_cookie_domain(), httponly=True, secure=secure, samesite="lax", max_age=28800)
    response.set_cookie("alrifai_csrf", result.csrf_token, domain=_cookie_domain(), httponly=True, secure=secure, samesite="lax", max_age=28800)
    return response


@app.get("/change-password", response_class=HTMLResponse)
def change_password_form(request: Request, message: str = "", return_to: str = "") -> HTMLResponse:
    if _session(request) is None:
        return RedirectResponse("/", status_code=303)
    target = _safe_return_url(return_to)
    return page("Change password", f"""
        <section class='card narrow'><div class='brand'>AL-RIFAI</div><h1>Change temporary password</h1>
        <p class='muted'>Choose a new password before entering the Owner workspace.</p>
        <form method='post' action='/change-password'>{_return_field(target or '')}<label>New password<input name='password' type='password' autocomplete='new-password' required></label>
        <label>Confirm password<input name='confirmation' type='password' autocomplete='new-password' required></label>
        <input type='hidden' name='csrf_token' value='""" + html.escape(request.cookies.get("alrifai_csrf", "")) + """'>
        <button type='submit'>Save new password</button></form></section>
    """, message)


@app.post("/change-password")
def change_password_submit(request: Request, password: str = Form(...), confirmation: str = Form(...), csrf_token: str = Form(...), return_to: str = Form("")) -> HTMLResponse:
    token = request.cookies.get("alrifai_session", "")
    target = _safe_return_url(return_to)
    if return_to and target is None:
        return RedirectResponse("/", status_code=303)
    if password != confirmation:
        return change_password_form(request, "Passwords did not match.", target or "")
    try:
        with database() as connection:
            change_password(connection, token, csrf_token, password)
    except ValueError as exc:
        return change_password_form(request, str(exc), target or "")
    except (AuthenticationError, RuntimeError, psycopg.Error):
        return RedirectResponse("/", status_code=303)
    return RedirectResponse(target or "/home", status_code=303)


@app.get("/home", response_class=HTMLResponse)
def authenticated_home(request: Request) -> HTMLResponse:
    session = _session(request)
    if session is None:
        return RedirectResponse("/", status_code=303)
    principal, _ = session
    admin_link = "<a class='admin-link' href='/admin'>Admin</a>" if principal.principal_type in {PrincipalType.OWNER, PrincipalType.ADMIN} else ""
    webui_url = html.escape(os.getenv("ALRIFAI_OPEN_WEBUI_URL", "http://127.0.0.1:8502/"), quote=True)
    return page("Home", f"""
      <div class='app-shell'>
        <header class='app-bar'><div class='brand'>AL-RIFAI</div><nav class='app-nav'><a href='/home'>Home</a>{admin_link}
          <form method='post' action='/logout'><input type='hidden' name='csrf_token' value='{html.escape(request.cookies.get('alrifai_csrf',''))}'><button class='secondary'>Log out</button></form>
        </nav></header>
        <main class='webui-frame-wrap'><iframe class='webui-frame' src='{webui_url}' title='Open WebUI AI Chat'></iframe></main>
      </div>
    """)


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request) -> HTMLResponse:
    session = _admin(request)
    if session is None:
        return RedirectResponse("/", status_code=303)
    principal, _ = session
    owner_link = "<a href='/owner'>Open Owner Dashboard</a>" if principal.principal_type is PrincipalType.OWNER else ""
    user_management = "<p><a href='/owner'>User Management</a> is Owner-only.</p>" if principal.principal_type is not PrincipalType.OWNER else ""
    return page("Admin", f"""
      <div class='dashboard'><aside><div class='brand'>AL-RIFAI</div><p class='muted'>Admin workspace</p>
        <nav><a href='/home'>Home / AI Chat</a>{owner_link}</nav></aside>
      <section class='content'><header><div><p class='eyebrow'>ADMINISTRATION</p><h1>Admin</h1></div>
        <form method='post' action='/logout'><input type='hidden' name='csrf_token' value='{html.escape(request.cookies.get('alrifai_csrf',''))}'><button class='secondary'>Log out</button></form></header>
        <article class='card'><h2>Administrative workspace</h2><p>Signed in as {html.escape(principal.principal_type.value)}. Domain administration will appear here as services are connected.</p>{user_management}</article>
      </section></div>
    """)


@app.get("/owner/account", response_class=HTMLResponse)
def account_view(request: Request) -> HTMLResponse:
    if _owner_token(request) is None:
        return RedirectResponse("/", status_code=303)
    with database() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT username, status, principal_type, created_at FROM auth_password_credentials c JOIN auth_principals p USING (principal_id) WHERE p.principal_type='OWNER'")
            row = cursor.fetchone()
    if row is None:
        return RedirectResponse("/", status_code=303)
    return page("View Account", f"""
        <section class='card narrow'><div class='brand'>AL-RIFAI</div><h1>View Account</h1>
        <dl><dt>Username</dt><dd>{html.escape(row[0])}</dd><dt>Principal</dt><dd>{html.escape(row[2])}</dd><dt>Status</dt><dd>{html.escape(row[1])}</dd></dl>
        <nav><a href='/owner/account/edit'>Edit Account</a><a href='/owner/account/password'>Change Password</a><a href='/owner'>Back to dashboard</a></nav></section>
    """)


@app.get("/owner/account/edit", response_class=HTMLResponse)
def account_edit(request: Request, message: str = "") -> HTMLResponse:
    if _owner_token(request) is None:
        return RedirectResponse("/", status_code=303)
    with database() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT username FROM auth_password_credentials c JOIN auth_principals p USING (principal_id) WHERE p.principal_type='OWNER'")
            row = cursor.fetchone()
    return page("Edit Account", f"""
        <section class='card narrow'><div class='brand'>AL-RIFAI</div><h1>Edit Account</h1>
        <form method='post' action='/owner/account/edit'><label>Username<input name='username' value='{html.escape(row[0] if row else '')}' autocomplete='username' required></label>
        <input type='hidden' name='csrf_token' value='{html.escape(request.cookies.get('alrifai_csrf',''))}'><button type='submit'>Save Changes</button></form>
        <nav><a href='/owner/account'>View Account</a><a href='/owner'>Back to dashboard</a></nav></section>
    """, message)


@app.post("/owner/account/edit")
def account_edit_submit(request: Request, username: str = Form(...), csrf_token: str = Form(...)) -> HTMLResponse:
    tokens = _owner_token(request)
    if tokens is None:
        return RedirectResponse("/", status_code=303)
    try:
        with database() as connection:
            update_username(connection, tokens[0], csrf_token, username)
    except ValueError as exc:
        return account_edit(request, str(exc))
    except psycopg.errors.UniqueViolation:
        return account_edit(request, "That username is already registered.")
    except (AuthenticationError, RuntimeError, psycopg.Error):
        return RedirectResponse("/", status_code=303)
    return RedirectResponse("/owner/account", status_code=303)


@app.get("/owner/account/password", response_class=HTMLResponse)
def account_password_form(request: Request, message: str = "") -> HTMLResponse:
    if _owner_token(request) is None:
        return RedirectResponse("/", status_code=303)
    return page("Change Password", """
        <section class='card narrow'><div class='brand'>AL-RIFAI</div><h1>Change Password</h1>
        <p class='muted'>Your current password is required. Other active sessions will be revoked.</p>
        <form method='post' action='/owner/account/password'><label>Current password<input name='current_password' type='password' autocomplete='current-password' required></label>
        <label>New password<input name='new_password' type='password' autocomplete='new-password' required></label>
        <label>Confirm new password<input name='confirmation' type='password' autocomplete='new-password' required></label>
        <input type='hidden' name='csrf_token' value='""" + html.escape(request.cookies.get("alrifai_csrf", "")) + """'><button type='submit'>Change Password</button></form>
        <nav><a href='/owner/account'>View Account</a><a href='/owner'>Back to dashboard</a></nav></section>
    """, message)


@app.post("/owner/account/password")
def account_password_submit(request: Request, current_password: str = Form(...), new_password: str = Form(...), confirmation: str = Form(...), csrf_token: str = Form(...)) -> HTMLResponse:
    tokens = _owner_token(request)
    if tokens is None:
        return RedirectResponse("/", status_code=303)
    if new_password != confirmation:
        return account_password_form(request, "Passwords did not match.")
    try:
        with database() as connection:
            change_password(connection, tokens[0], csrf_token, new_password, current_password=current_password)
    except AuthenticationError as exc:
        return account_password_form(request, str(exc))
    except ValueError as exc:
        return account_password_form(request, str(exc))
    return RedirectResponse("/owner/account", status_code=303)


@app.get("/signup", response_class=HTMLResponse)
def signup_form(message: str = "") -> HTMLResponse:
    return page("Create account", """
        <section class='card narrow'><div class='brand'>AL-RIFAI</div><h1>Create account</h1>
        <p class='muted'>New accounts remain pending until approved. Signup can never create Owner or Admin access.</p>
        <form method='post' action='/signup'><label>Username<input name='username' autocomplete='username' required></label>
        <label>Password<input name='password' type='password' autocomplete='new-password' required></label>
        <button type='submit'>Submit registration</button></form><nav><a href='/'>Back to sign in</a></nav></section>
    """, message)


@app.post("/signup")
def signup(username: str = Form(...), password: str = Form(...)) -> HTMLResponse:
    try:
        with database() as connection:
            create_pending_account(connection, username, password)
    except ValueError as exc:
        return signup_form(str(exc))
    except psycopg.errors.UniqueViolation:
        return signup_form("That username is already registered.")
    except (RuntimeError, psycopg.Error):
        return signup_form("Registration is temporarily unavailable.")
    return page("Registration received", "<section class='card narrow'><h1>Registration received</h1><p>Your account is pending Owner approval.</p><nav><a href='/'>Return to sign in</a></nav></section>")


@app.get("/forgot-password", response_class=HTMLResponse)
def forgot_form(message: str = "") -> HTMLResponse:
    return page("Forgot password", """
        <section class='card narrow'><div class='brand'>AL-RIFAI</div><h1>Forgot password</h1>
        <p class='muted'>Email/SMS delivery is not configured. For local development, the machine owner can use the secure terminal recovery command.</p>
        <form method='post' action='/forgot-password'><label>Username<input name='username' autocomplete='username' required></label>
        <button type='submit'>Request recovery</button></form><nav><a href='/'>Back to sign in</a></nav></section>
    """, message)


@app.post("/forgot-password")
def forgot_password(username: str = Form(...)) -> HTMLResponse:
    del username
    return forgot_form("If the account exists, follow the local recovery procedure. No message was sent.")


@app.get("/owner", response_class=HTMLResponse)
def owner_dashboard(request: Request) -> HTMLResponse:
    session = _owner(request)
    if session is None:
        return RedirectResponse("/", status_code=303)
    principal, csrf_hash = session
    try:
        with database() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT p.principal_id, username, status, principal_type FROM auth_password_credentials c JOIN auth_principals p USING (principal_id) ORDER BY username")
                users = cursor.fetchall()
    except (RuntimeError, psycopg.Error):
        users = []
    user_rows = "".join(
        f"<tr><td>{html.escape(row[1])}</td><td>{html.escape(row[2])}</td><td>{html.escape(row[3])}</td>"
        f"<td class='actions'><a title='View account' aria-label='View account' href='/owner/users/{row[0]}'>🔍</a> "
        f"<a title='Edit account' aria-label='Edit account' href='/owner/users/{row[0]}/edit'>✎</a> "
        f"<a title='Change password' aria-label='Change password' href='/owner/users/{row[0]}/password'>🔑</a></td></tr>"
        for row in users
    )
    nav = ["Overview", "Conversations", "Applicants", "Employees", "Attendance", "Escort Programs", "Clients", "Payroll", "Cash Transactions", "Billing", "Reports", "User Management", "Roles and Permissions", "Approvals", "Business Documentation", "AI / MCP Administration", "Settings", "Audit Logs"]
    nav_html = "".join(f"<li>{html.escape(item)}<span>planned</span></li>" for item in nav)
    return page("Owner Dashboard", f"""
      <div class='dashboard'><aside><div class='brand'>AL-RIFAI</div><p class='muted'>Owner workspace</p><ul>{nav_html}</ul></aside>
      <section class='content'><header><div><p class='eyebrow'>OWNER DASHBOARD</p><h1>Welcome, azimpolcu</h1></div>
      <form method='post' action='/logout'><input type='hidden' name='csrf_token' value='{html.escape(request.cookies.get('alrifai_csrf',''))}'><button class='secondary'>Log out</button></form></header>
      <div class='grid'><article class='card'><h2>Authority</h2><p>Owner authority is enforced server-side through the trusted principal policy.</p></article>
      <article class='card'><h2>User Management</h2><p>Registered accounts: {len(users)}</p><table><thead><tr><th>Username</th><th>Status</th><th>Type</th><th>Actions</th></tr></thead><tbody>{user_rows or '<tr><td colspan="4">No accounts</td></tr>'}</tbody></table></article>
      <article class='card'><h2>Development status</h2><p>Business modules are intentionally placeholders until their domain services are connected. No fabricated metrics are shown.</p></article></div></section></div>
    """)


def _target_user(request: Request, principal_id: UUID):
    tokens = _owner_token(request)
    if tokens is None:
        return None
    with database() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT p.principal_id, username, status, principal_type FROM auth_password_credentials c JOIN auth_principals p USING (principal_id) WHERE p.principal_id=%s", (principal_id,))
            return cursor.fetchone()


@app.get("/owner/users/{principal_id}", response_class=HTMLResponse)
def user_view(request: Request, principal_id: UUID) -> HTMLResponse:
    row = _target_user(request, principal_id)
    if row is None:
        return RedirectResponse("/", status_code=303)
    return page("View User", f"<section class='card narrow'><div class='brand'>AL-RIFAI</div><h1>View User</h1><dl><dt>Username</dt><dd>{html.escape(row[1])}</dd><dt>Status</dt><dd>{html.escape(row[2])}</dd><dt>Principal</dt><dd>{html.escape(row[3])}</dd></dl><nav><a href='/owner/users/{principal_id}/edit'>Edit</a><a href='/owner/users/{principal_id}/password'>Reset Password</a><a href='/owner'>Back</a></nav></section>")


@app.get("/owner/users/{principal_id}/edit", response_class=HTMLResponse)
def user_edit(request: Request, principal_id: UUID, message: str = "") -> HTMLResponse:
    row = _target_user(request, principal_id)
    if row is None:
        return RedirectResponse("/", status_code=303)
    return page("Edit User", f"<section class='card narrow'><div class='brand'>AL-RIFAI</div><h1>Edit User</h1><form method='post' action='/owner/users/{principal_id}/edit'><label>Username<input name='username' value='{html.escape(row[1])}' required></label><input type='hidden' name='csrf_token' value='{html.escape(request.cookies.get('alrifai_csrf',''))}'><button type='submit'>Update Username</button></form><nav><a href='/owner/users/{principal_id}'>View</a><a href='/owner'>Back</a></nav></section>", message)


@app.post("/owner/users/{principal_id}/edit")
def user_edit_submit(request: Request, principal_id: UUID, username: str = Form(...), csrf_token: str = Form(...)) -> HTMLResponse:
    tokens = _owner_token(request)
    if tokens is None:
        return RedirectResponse("/", status_code=303)
    try:
        with database() as connection:
            update_username(connection, tokens[0], csrf_token, username) if principal_id == _owner(request)[0].principal_id else _update_other_username(connection, tokens[0], csrf_token, principal_id, username)
    except (AuthenticationError, ValueError) as exc:
        return user_edit(request, principal_id, str(exc))
    except psycopg.errors.UniqueViolation:
        return user_edit(request, principal_id, "That username is already registered.")
    return RedirectResponse(f"/owner/users/{principal_id}", status_code=303)


def _update_other_username(connection, token: str, csrf_token: str, target_principal_id: UUID, username: str) -> None:
    normalized = normalize_username(username)
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute("SELECT s.principal_id FROM auth_sessions s JOIN auth_principals p USING (principal_id) WHERE s.token_hash=%s AND s.csrf_token_hash=%s AND s.revoked_at IS NULL AND s.expires_at>NOW() AND p.principal_type='OWNER' FOR UPDATE", (_hash_token(token), _hash_token(csrf_token)))
            actor = cursor.fetchone()
            if actor is None:
                raise AuthenticationError("Owner session required")
            cursor.execute("SELECT principal_type FROM auth_principals WHERE principal_id=%s FOR UPDATE", (target_principal_id,))
            target = cursor.fetchone()
            if target is None or target[0] == 'OWNER':
                raise AuthenticationError("Owner username requires self-service edit")
            cursor.execute("UPDATE auth_password_credentials SET username=%s, updated_at=NOW() WHERE principal_id=%s", (normalized, target_principal_id))
            _audit(connection, entity_id=target_principal_id, action='UPDATE', actor_principal_id=actor[0], after={'event':'username_changed_by_owner'})


@app.get("/owner/users/{principal_id}/password", response_class=HTMLResponse)
def user_password_form(request: Request, principal_id: UUID, message: str = "") -> HTMLResponse:
    row = _target_user(request, principal_id)
    if row is None:
        return RedirectResponse("/", status_code=303)
    if row[3] == "OWNER":
        return RedirectResponse("/owner/account/password", status_code=303)
    return page("Reset Password", f"<section class='card narrow'><div class='brand'>AL-RIFAI</div><h1>Reset Password</h1><p class='muted'>A fresh Owner session is required. The target user's other sessions will be revoked.</p><form method='post' action='/owner/users/{principal_id}/password'><label>New password<input name='new_password' type='password' autocomplete='new-password' required></label><label>Confirm password<input name='confirmation' type='password' autocomplete='new-password' required></label><input type='hidden' name='csrf_token' value='{html.escape(request.cookies.get('alrifai_csrf',''))}'><button type='submit'>Reset Password</button></form><nav><a href='/owner/users/{principal_id}'>View</a><a href='/owner'>Back</a></nav></section>", message)


@app.post("/owner/users/{principal_id}/password")
def user_password_submit(request: Request, principal_id: UUID, new_password: str = Form(...), confirmation: str = Form(...), csrf_token: str = Form(...)) -> HTMLResponse:
    tokens = _owner_token(request)
    if tokens is None:
        return RedirectResponse("/", status_code=303)
    if new_password != confirmation:
        return user_password_form(request, principal_id, "Passwords did not match.")
    try:
        with database() as connection:
            reset_user_password(connection, tokens[0], csrf_token, principal_id, new_password)
    except (AuthenticationError, ValueError) as exc:
        return user_password_form(request, principal_id, str(exc))
    return RedirectResponse(f"/owner/users/{principal_id}", status_code=303)


@app.post("/logout")
def logout(request: Request, csrf_token: str = Form(...)) -> RedirectResponse:
    token = request.cookies.get("alrifai_session", "")
    with database() as connection:
        revoke_session(connection, token, csrf_token)
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("alrifai_session", domain=_cookie_domain())
    response.delete_cookie("alrifai_csrf", domain=_cookie_domain())
    return response


def _config_admin(request: Request):
    session = _admin(request)
    if session is None:
        return None
    principal, _ = session
    try:
        require_capability(principal, Capability.MANAGE_CONFIGURATION)
    except Exception:
        return None
    return session


def _valid_csrf(request: Request, csrf_token: str) -> bool:
    session = _session(request)
    if session is None:
        return False
    _, csrf_hash = session
    return bool(csrf_token) and _hash_token(csrf_token) == csrf_hash


def _ai_service(connection) -> tuple[AiRuntimeService, str | None]:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM ai_gateway_configs LIMIT 1")
    except Exception:
        connection.rollback()
        note = "AI runtime persistence is unavailable: migration V010 is not applied to this database. Changes are kept in memory only."
        return AiRuntimeService(store=InMemoryAiRuntimeStore(), secrets=SecretResolver()), note
    return AiRuntimeService(store=PostgresAiRuntimeStore(connection), secrets=SecretResolver()), None


def _ai_settings_body(request: Request, view, note: str = "", extra: str = "") -> str:
    csrf = html.escape(request.cookies.get("alrifai_csrf", ""), quote=True)
    rows = ""
    for gateway in view.gateways:
        marker = "active" if gateway.is_active else ("enabled" if gateway.enabled else "disabled")
        cred = "yes" if gateway.credential_configured else "no"
        tested = "untested" if gateway.last_test_ok is None else ("ok" if gateway.last_test_ok else "failed")
        rows += (
            f"<tr><td>{html.escape(gateway.gateway_id)}</td><td>{html.escape(gateway.display_name)}</td>"
            f"<td>{html.escape(gateway.gateway_type.value)}</td><td>{html.escape(gateway.endpoint)}</td>"
            f"<td>{html.escape(gateway.route)}</td><td>{marker}</td><td>{cred}</td><td>{tested}</td>"
            f"<td><form method='post' action='/admin/ai-settings/set-active'>"
            f"<input type='hidden' name='csrf_token' value='{csrf}'>"
            f"<input type='hidden' name='gateway_id' value='{html.escape(gateway.gateway_id, quote=True)}'>"
            f"<button class='secondary' type='submit'>Activate</button></form>"
            f"<form method='post' action='/admin/ai-settings/test'>"
            f"<input type='hidden' name='csrf_token' value='{csrf}'>"
            f"<input type='hidden' name='gateway_id' value='{html.escape(gateway.gateway_id, quote=True)}'>"
            f"<button class='secondary' type='submit'>Test</button></form>"
            f"<form method='post' action='/admin/ai-settings/discover'>"
            f"<input type='hidden' name='csrf_token' value='{csrf}'>"
            f"<input type='hidden' name='gateway_id' value='{html.escape(gateway.gateway_id, quote=True)}'>"
            f"<button class='secondary' type='submit'>Discover</button></form></td></tr>"
        )
    type_options = "".join(f"<option value='{item.value}'>{html.escape(item.value)}</option>" for item in GatewayType)
    auth_options = "".join(f"<option value='{item.value}'>{html.escape(item.value)}</option>" for item in GatewayAuthMode)
    persist = f"<p class='muted'>{html.escape(note)}</p>" if note else ""
    active = html.escape(view.active_gateway_id or "none")
    return f"""
      <div class='dashboard'><aside><div class='brand'>AL-RIFAI</div><p class='muted'>AI runtime settings</p>
        <nav><a href='/home'>Home / AI Chat</a><a href='/admin'>Admin</a></nav></aside>
      <section class='content'><header><div><p class='eyebrow'>ADMINISTRATION</p><h1>AI / Model Settings</h1>
        <p class='muted'>Active gateway: {active}. This backend state controls the actual AI runtime.</p>{persist}</div></header>
      <article class='card'><h2>Gateways</h2><table><thead><tr><th>ID</th><th>Name</th><th>Type</th><th>Endpoint</th><th>Route</th><th>State</th><th>Credential</th><th>Last test</th><th>Actions</th></tr></thead>
        <tbody>{rows or '<tr><td colspan="9">No gateways configured</td></tr>'}</tbody></table></article>
      {extra}
      <article class='card'><h2>Save gateway</h2>
        <form method='post' action='/admin/ai-settings/save'>
        <label>Gateway ID<input name='gateway_id' required></label>
        <label>Display name<input name='display_name' required></label>
        <label>Type<select name='gateway_type'>{type_options}</select></label>
        <label>Endpoint<input name='endpoint' placeholder='http://127.0.0.1:20129/v1' required></label>
        <label>Auth mode<select name='auth_mode'>{auth_options}</select></label>
        <label>Secret reference (env:NAME or file:/path; required for api_key)<input name='secret_ref'></label>
        <label>Route / model<input name='route' required></label>
        <label>Fallback gateway ID (optional)<input name='fallback_gateway_id'></label>
        <label class='check'><input type='checkbox' name='enabled' checked> Enabled</label>
        <label class='check'><input type='checkbox' name='is_local'> Local endpoint</label>
        <input type='hidden' name='csrf_token' value='{csrf}'><button type='submit'>Save gateway</button></form>
        <p class='muted'>Saving never exposes credentials. Enabling a gateway never activates it; use Activate explicitly. Invalid configuration cannot become active.</p></article>
      </section></div>
    """


@app.get("/admin/ai-settings", response_class=HTMLResponse)
def ai_settings_view(request: Request, message: str = "") -> HTMLResponse:
    if _config_admin(request) is None:
        return RedirectResponse("/", status_code=303)
    try:
        with database() as connection:
            service, note = _ai_service(connection)
            view = service.current()
    except (RuntimeError, psycopg.Error):
        return page("AI Settings", "<section class='card narrow'><h1>AI Settings</h1><p>Configuration is temporarily unavailable.</p></section>")
    body = _ai_settings_body(request, view, note or "")
    return page("AI Settings", body, message)


def _ai_settings_action(request: Request, csrf_token: str):
    """Return (principal, None) when allowed, else (None, denial response)."""
    session = _config_admin(request)
    if session is None:
        return None, RedirectResponse("/", status_code=303)
    if not _valid_csrf(request, csrf_token):
        return None, ai_settings_view(request, "Invalid session token. Please retry.")
    return session[0], None


@app.post("/admin/ai-settings/save")
def ai_settings_save(
    request: Request,
    gateway_id: str = Form(...),
    display_name: str = Form(...),
    gateway_type: str = Form(...),
    endpoint: str = Form(...),
    auth_mode: str = Form(...),
    route: str = Form(...),
    secret_ref: str = Form(""),
    fallback_gateway_id: str = Form(""),
    enabled: str = Form(""),
    is_local: str = Form(""),
    csrf_token: str = Form(...),
) -> HTMLResponse:
    principal, denied = _ai_settings_action(request, csrf_token)
    if denied is not None:
        return denied
    try:
        config = GatewayConfig(
            gateway_id=gateway_id.strip(),
            display_name=display_name.strip(),
            gateway_type=GatewayType(gateway_type),
            endpoint=endpoint.strip(),
            auth_mode=GatewayAuthMode(auth_mode),
            secret_ref=secret_ref.strip() or None,
            route=route.strip(),
            enabled=bool(enabled),
            is_local=bool(is_local),
            fallback_gateway_id=fallback_gateway_id.strip() or None,
        )
    except ValueError:
        return ai_settings_view(request, "Unsupported gateway type or auth mode.")
    try:
        with database() as connection:
            service, _ = _ai_service(connection)
            service.save_gateway(principal, config)
    except AiConfigError as exc:
        return ai_settings_view(request, f"Configuration rejected: {exc}")
    except (RuntimeError, psycopg.Error):
        return ai_settings_view(request, "Configuration store is temporarily unavailable.")
    return RedirectResponse("/admin/ai-settings", status_code=303)


@app.post("/admin/ai-settings/set-active")
def ai_settings_activate(request: Request, gateway_id: str = Form(...), csrf_token: str = Form(...)) -> HTMLResponse:
    principal, denied = _ai_settings_action(request, csrf_token)
    if denied is not None:
        return denied
    try:
        with database() as connection:
            service, _ = _ai_service(connection)
            service.set_active(principal, gateway_id.strip())
    except AiConfigError as exc:
        return ai_settings_view(request, f"Activation rejected: {exc}")
    except (RuntimeError, psycopg.Error):
        return ai_settings_view(request, "Configuration store is temporarily unavailable.")
    return RedirectResponse("/admin/ai-settings", status_code=303)


@app.post("/admin/ai-settings/test")
def ai_settings_test(request: Request, gateway_id: str = Form(...), csrf_token: str = Form(...)) -> HTMLResponse:
    principal, denied = _ai_settings_action(request, csrf_token)
    if denied is not None:
        return denied
    try:
        with database() as connection:
            service, note = _ai_service(connection)
            result = service.test_connection(principal, gateway_id.strip())
            view = service.current()
    except AiConfigError as exc:
        return ai_settings_view(request, f"Connection test rejected: {exc}")
    except (RuntimeError, psycopg.Error):
        return ai_settings_view(request, "Configuration store is temporarily unavailable.")
    outcome = "reachable" if result.ok else f"failed ({result.error_code})"
    extra = f"<article class='card'><h2>Connection test</h2><p>Gateway {html.escape(result.gateway_id)}: {html.escape(outcome)}.</p></article>"
    return page("AI Settings", _ai_settings_body(request, view, note or "", extra))


@app.post("/admin/ai-settings/discover")
def ai_settings_discover(request: Request, gateway_id: str = Form(...), csrf_token: str = Form(...)) -> HTMLResponse:
    principal, denied = _ai_settings_action(request, csrf_token)
    if denied is not None:
        return denied
    try:
        with database() as connection:
            service, note = _ai_service(connection)
            models = service.discover_models(principal, gateway_id.strip())
            view = service.current()
    except AiConfigError as exc:
        return ai_settings_view(request, f"Discovery rejected: {exc}")
    except (RuntimeError, psycopg.Error):
        return ai_settings_view(request, "Configuration store is temporarily unavailable.")
    items = "".join(f"<li>{html.escape(item.model_id)}</li>" for item in models) or "<li>no models advertised</li>"
    extra = f"<article class='card'><h2>Discovered routes/models</h2><ul>{items}</ul></article>"
    return page("AI Settings", _ai_settings_body(request, view, note or "", extra))


CSS = """
:root{font-family:Inter,Segoe UI,sans-serif;color:#132238;background:#eef3f7}*{box-sizing:border-box}body{margin:0}.shell{min-height:100vh;padding:28px}.card{background:white;border:1px solid #dfe7ef;border-radius:18px;padding:28px;box-shadow:0 8px 24px #19324d12}.narrow{max-width:480px;margin:7vh auto}.brand{font-weight:800;letter-spacing:.14em;color:#147d87}.muted{color:#64748b}.eyebrow{font-size:12px;letter-spacing:.12em;color:#147d87}h1{margin-top:8px}label{display:block;font-weight:600;margin:16px 0}input{display:block;width:100%;margin-top:7px;border:1px solid #cbd5e1;border-radius:9px;padding:12px;font:inherit}.check{font-weight:400;font-size:14px}.check input{display:inline;width:auto;margin-right:6px}button{border:0;border-radius:9px;padding:12px 18px;background:#147d87;color:white;font-weight:700;cursor:pointer}.secondary{background:#e6eef2;color:#143044}nav{display:flex;gap:18px;margin-top:22px}a{color:#147d87}.notice{max-width:480px;margin:18px auto;background:#fff4d6;padding:14px;border-radius:10px}.dashboard{display:grid;grid-template-columns:265px 1fr;min-height:calc(100vh - 56px);gap:26px;max-width:1500px;margin:auto}.dashboard aside{background:#102b40;color:white;border-radius:18px;padding:24px}.dashboard aside .muted{color:#b4cad5}.dashboard ul{padding:0;list-style:none}.dashboard li{padding:9px 0;font-size:14px;border-bottom:1px solid #ffffff18}.dashboard li span{float:right;color:#8fb4bf;font-size:11px}.content header{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px}.grid{display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}.grid .card{min-height:150px}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;border-bottom:1px solid #e2e8f0;padding:9px 4px}@media(max-width:800px){.dashboard{display:block}.dashboard aside{margin-bottom:18px}.dashboard ul{display:grid;grid-template-columns:1fr 1fr;gap:4px 18px}.content header{align-items:flex-start}}
 .app-shell{min-height:calc(100vh - 56px);margin:-28px}.app-bar{height:58px;background:#102b40;color:white;display:flex;align-items:center;justify-content:space-between;padding:0 22px;gap:20px}.app-bar .brand{color:white}.app-nav{display:flex;align-items:center;gap:20px;margin:0}.app-nav a{color:white}.app-nav form{margin:0}.webui-frame-wrap{height:calc(100vh - 58px);background:#fff}.webui-frame{display:block;width:100%;height:100%;border:0}
"""
