import os
import json
import boto3
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# --- This code is now UPDATED ---


def get_db_credentials():
    """Fetches database credentials from AWS Secrets Manager."""
    secret_arn = os.environ.get("DB_SECRET_ARN")
    # --- THIS IS THE FIX ---
    # Read the host and dbname from new, separate env vars
    db_host = os.environ.get("DB_HOST")
    db_name = os.environ.get("DB_NAME", "aleenascuisine")  # Default
    # --- END OF FIX ---

    if not secret_arn:
        raise ValueError("DB_SECRET_ARN environment variable not set.")
    if not db_host:
        raise ValueError("DB_HOST environment variable not set.")

    client = boto3.client("secretsmanager")

    try:
        response = client.get_secret_value(SecretId=secret_arn)
        secret = json.loads(response["SecretString"])

        # Return the combined credentials
        return {
            "user": secret["username"],
            "pass": secret["password"],
            "host": db_host,
            "db": db_name,
        }
    except Exception as e:
        print(f"Error fetching/combining credentials: {e}")
        raise


# --- End of update ---


def get_database_url():
    """Returns the SQLAlchemy URL, respecting DATABASE_URL override."""
    override = os.environ.get("DATABASE_URL")
    if override:
        return override

    db_creds = get_db_credentials()
    url_template = config.get_main_option("sqlalchemy.url")
    if not url_template:
        raise ValueError(
            "sqlalchemy.url is not defined in alembic.ini and DATABASE_URL override not provided"
        )
    return url_template % db_creds


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    db_url = get_database_url()
    connect_args = {}

    engine = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=db_url,
        connect_args=connect_args,
    )

    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
