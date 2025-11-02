#!/usr/bin/env python3
"""Apply Alembic migrations via the Aurora Data API.

This script renders the upgrade SQL in offline mode and executes each
statement against the Aurora Serverless cluster using boto3's
rds-data client. It lets us keep Alembic revision history without
opening the database to the public internet.
"""

from __future__ import annotations

import os
import sys
import textwrap
from io import StringIO
from pathlib import Path
from typing import Iterable

import boto3
from alembic import command
from alembic.config import Config

ROOT_DIR = Path(__file__).resolve().parent.parent
ALEMBIC_INI = ROOT_DIR / "alembic.ini"


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(
            f"Environment variable {name} is required for Data API migrations."
        )
    return value


def _iter_sql_statements(sql_blob: str) -> Iterable[str]:
    buffer: list[str] = []
    for line in sql_blob.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        buffer.append(line)
        if stripped.endswith(";"):
            statement = "\n".join(buffer).rstrip()
            if statement.endswith(";"):
                statement = statement[:-1]
            yield statement.strip()
            buffer.clear()
    if buffer:
        statement = "\n".join(buffer).rstrip()
        if statement.endswith(";"):
            statement = statement[:-1]
        yield statement.strip()


def main(target_revision: str = "head") -> int:
    cluster_arn = require_env("DB_CLUSTER_ARN")
    secret_arn = require_env("DB_SECRET_ARN")
    database = os.environ.get("DB_NAME", "aleenascuisine")
    region = (
        os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or "ap-south-1"
    )

    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", "alembic")

    buffer = StringIO()

    def capture(text: str, *args: object) -> None:
        buffer.write(text)
        if args:
            buffer.write(" ".join(str(a) for a in args))
        if not text.endswith("\n"):
            buffer.write("\n")

    cfg.print_stdout = capture

    # Ensure env.py does not try to resolve Secrets Manager when rendering SQL.
    os.environ.setdefault("DATABASE_URL", "mysql://")

    command.upgrade(cfg, target_revision, sql=True)
    sql_blob = buffer.getvalue()

    client = boto3.client("rds-data", region_name=region)
    statements = list(_iter_sql_statements(sql_blob))
    if not statements:
        print("No SQL statements generated; database is already up to date.")
        return 0

    print(f"Executing {len(statements)} statements against {database} via Data API...")
    for idx, statement in enumerate(statements, start=1):
        print(f"[{idx}/{len(statements)}] {statement.splitlines()[0][:80]}...")
        client.execute_statement(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database=database,
            sql=statement,
        )

    print("Migration complete.")
    return 0


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "head"
    try:
        raise SystemExit(main(target))
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - operational script
        message = textwrap.dedent(
            f"""
            Migration failed: {exc}
            Ensure DB_CLUSTER_ARN, DB_SECRET_ARN, DB_NAME, and AWS_REGION are set and the secret grants rds-data access.
            """
        ).strip()
        print(message, file=sys.stderr)
        raise SystemExit(1)
