"""Interactive local recovery command controlled by the machine owner."""

from __future__ import annotations

import getpass
import os
import sys

import psycopg

from .service import _audit, hash_password, normalize_username


def main() -> None:
    username = normalize_username(sys.argv[1]) if len(sys.argv) == 2 else normalize_username(input("Username: "))
    if input("Type RESET to continue: ") != "RESET":
        raise SystemExit("Reset cancelled.")
    password = getpass.getpass("New password (input hidden): ")
    confirmation = getpass.getpass("Confirm new password: ")
    if password != confirmation:
        raise SystemExit("Passwords did not match; no change was made.")
    with psycopg.connect(os.environ["ALRIFAI_DATABASE_URL"]) as connection:
        with connection.transaction():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE auth_password_credentials c SET password_hash=%s, password_changed_at=NOW(), updated_at=NOW()
                    FROM auth_principals p WHERE p.principal_id=c.principal_id AND c.username=%s
                    RETURNING c.principal_id
                    """,
                    (hash_password(password), username),
                )
                row = cursor.fetchone()
                if row is None:
                    raise SystemExit("Account not found; no change was made.")
                cursor.execute("UPDATE auth_principals SET must_change_password=true, updated_at=NOW() WHERE principal_id=%s", (row[0],))
                _audit(connection, entity_id=row[0], action="RESET", actor_principal_id=None, after={"event": "local_password_reset"})
    print("Password reset completed; password was not displayed.")


if __name__ == "__main__":
    main()
