import os


class Config:
    """
    Base configuration with defaults.
    """

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://discovery:discovery@127.0.0.1:5432/discovery?sslmode=disable",
    )
    AIRFLOW_TRIGGER_URL = os.getenv(
        "AIRFLOW_TRIGGER_URL", "http://127.0.0.1:8080/api/v1/dags/github_scan_dag/dagRuns"
    )
    AIRFLOW_CREDENTIALS = os.getenv("AIRFLOW_CREDENTIALS", "discovery:discovery")
    AIRFLOW_API_TOKEN = os.getenv("AIRFLOW_API_TOKEN", None)
    FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() in ("true", "1", "yes")
    KAFKA_BROKER = os.getenv("KAFKA_BROKER", "127.0.0.1:9092")
    KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "github-scanner-consumer")
    KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "github-scanner-events")


class DevelopmentConfig(Config):
    """
    Development-specific configuration.
    """

    FLASK_DEBUG = True


class TestingConfig(Config):
    """
    Testing-specific configuration.
    """

    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///:memory:"  # In-memory SQLite database for tests
    )
    FLASK_DEBUG = True
    TESTING = True


class ProductionConfig(Config):
    """
    Production-specific configuration.
    """

    FLASK_DEBUG = False


def get_config(env: str = None) -> Config:
    """
    Get the configuration object based on the environment.

    :param env: The environment name ('development', 'testing', 'production').
                If not specified, defaults to 'production'.
    :return: The configuration class for the selected environment.
    """
    env = env or os.getenv("FLASK_ENV", "production").lower()

    config_map = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "production": ProductionConfig,
    }

    return config_map.get(env, ProductionConfig)
