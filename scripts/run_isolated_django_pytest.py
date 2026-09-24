from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run pytest-django against a LevelUpDiag-owned isolated PostgreSQL test database."
    )
    parser.add_argument("--db-name", required=True)
    parser.add_argument("--settings", default="config.settings.test")
    parser.add_argument("--admin-host", default="")
    parser.add_argument("--project-root", default="")
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    return parser


def _normalize_pytest_args(values: list[str]) -> list[str]:
    args = list(values)
    if args and args[0] == "--":
        args = args[1:]

    # The target project currently injects --reuse-db from pyproject.toml.
    # LevelUpDiag must own the complete lifecycle instead, so explicitly strip
    # persistence flags from configured commands and override addopts below.
    args = [arg for arg in args if arg not in {"--reuse-db", "--create-db"}]
    return args


def _connection_kwargs(database: dict[str, Any], *, admin_host: str = "") -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    mapping = {
        "NAME": "dbname",
        "USER": "user",
        "PASSWORD": "password",
        "HOST": "host",
        "PORT": "port",
    }
    for source, target in mapping.items():
        value = database.get(source)
        if value not in (None, ""):
            kwargs[target] = value
    if admin_host:
        kwargs["host"] = admin_host

    options = database.get("OPTIONS", {})
    if isinstance(options, dict):
        # psycopg accepts normal libpq connection parameters such as sslmode
        # and channel_binding. Django-only options are intentionally excluded.
        for key in ("sslmode", "channel_binding", "connect_timeout", "application_name"):
            value = options.get(key)
            if value not in (None, ""):
                kwargs[key] = value
    return kwargs


def _drop_database(database: dict[str, Any], test_db_name: str, *, admin_host: str = "") -> None:
    import psycopg
    from psycopg import sql

    kwargs = _connection_kwargs(database, admin_host=admin_host)
    if not kwargs.get("dbname"):
        raise RuntimeError("default database NAME is empty; cannot open an administrative connection")

    with psycopg.connect(**kwargs, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = %s
                  AND pid <> pg_backend_pid()
                """,
                (test_db_name,),
            )
            cursor.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(test_db_name))
            )


def _activate_project_root(value: str) -> Path:
    """Make the target Django project importable before importing settings.

    Python sets sys.path[0] to this wrapper's scripts directory when executed
    by filename, not to subprocess cwd.  LevelUpDiag runs this wrapper from the
    Konnaxion backend, so make that backend explicit on sys.path/PYTHONPATH.
    """
    project_root = Path(value).expanduser().resolve() if value else Path.cwd().resolve()
    os.chdir(project_root)
    root_text = str(project_root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    existing = os.environ.get("PYTHONPATH", "")
    parts = [part for part in existing.split(os.pathsep) if part]
    if root_text not in parts:
        os.environ["PYTHONPATH"] = os.pathsep.join([root_text, *parts])
    return project_root


def main() -> int:
    args = _parser().parse_args()
    pytest_args = _normalize_pytest_args(args.pytest_args)
    _activate_project_root(args.project_root)

    os.environ["DJANGO_SETTINGS_MODULE"] = args.settings
    os.environ["LEVELUPDIAG_TEST_DB_NAME"] = args.db_name

    from django.conf import settings
    from django.db import connections

    database = dict(settings.DATABASES["default"])
    database["OPTIONS"] = dict(database.get("OPTIONS", {}))

    # Remove a database left behind by an interrupted run that reused the same
    # run/probe identifier. This is expected to be a no-op normally.
    try:
        _drop_database(database, args.db_name, admin_host=args.admin_host)
    except Exception as exc:  # noqa: BLE001 - diagnostic wrapper must surface infra errors.
        print(f"LEVELUPDIAG_DB_PRE_CLEANUP_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 86

    settings.DATABASES["default"].setdefault("TEST", {})["NAME"] = args.db_name

    # Override target-project addopts so --reuse-db from pyproject.toml cannot
    # silently defeat LevelUpDiag isolation. Keep the canonical Konnaxion
    # settings module and import mode explicit.
    effective_pytest_args = [
        "-o",
        f"addopts=--ds={args.settings} --import-mode=importlib",
        "--create-db",
        *pytest_args,
    ]

    pytest_code = 1
    cleanup_error: Exception | None = None
    try:
        import pytest

        pytest_code = int(pytest.main(effective_pytest_args))
    finally:
        try:
            connections.close_all()
        finally:
            try:
                _drop_database(database, args.db_name, admin_host=args.admin_host)
            except Exception as exc:  # noqa: BLE001 - report deterministic cleanup failure.
                cleanup_error = exc

    if cleanup_error is not None:
        print(
            f"LEVELUPDIAG_DB_CLEANUP_FAILED: {type(cleanup_error).__name__}: {cleanup_error}",
            file=sys.stderr,
        )
        return 86 if pytest_code == 0 else pytest_code

    return pytest_code


if __name__ == "__main__":
    raise SystemExit(main())
