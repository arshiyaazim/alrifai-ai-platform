"""Development-only application launcher with server-side ``.env`` loading."""

from __future__ import annotations

import os
import sys
import argparse

from .dev_env import load_repo_development_env


def main() -> None:
    if os.getenv("ALRIFAI_ENV", "development").lower() not in {"local", "development", "dev"}:
        raise SystemExit("dev-start.sh refuses non-development ALRIFAI_ENV")
    load_repo_development_env()
    import uvicorn

    parser = argparse.ArgumentParser(description="Start the AL-RIFAI development web app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args(sys.argv[1:])
    uvicorn.run("src.alrifai.web.app:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
