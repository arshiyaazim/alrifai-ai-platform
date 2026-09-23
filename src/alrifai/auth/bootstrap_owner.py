"""Interactive local Owner bootstrap; never accepts a password argument."""

from __future__ import annotations

import getpass
import os

import psycopg

from .service import create_owner


def main() -> None:
    database_url = os.environ["ALRIFAI_DATABASE_URL"]
    password = getpass.getpass("Temporary Owner password (input hidden): ")
    confirmation = getpass.getpass("Confirm temporary Owner password: ")
    if password != confirmation:
        raise SystemExit("Passwords did not match; no account was created.")
    with psycopg.connect(database_url) as connection:
        create_owner(connection, "azimpolcu", password)
    print("Owner bootstrap completed for username azimpolcu; password was not displayed.")


if __name__ == "__main__":
    main()
