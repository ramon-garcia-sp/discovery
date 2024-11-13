import os
import sys
import pytest
from sqlalchemy import inspect

from service_api.app import Service, app, db


@pytest.fixture(scope="function")
def client():

    # Safety to avoid wiping the db
    if os.getenv("FLASK_ENV", None) != "testing":
        print("Not running in testing mode, this can wipe the DB")
        sys.exit(1)

    """
    Flask test client fixture with proper app and database setup.
    After each test, the DB is torn down and recreated.
    """
    # Use testing configuration for isolation between tests
    app.config.from_object("shared.config.TestingConfig")

    with app.test_client() as client:
        with app.app_context():
            db.Model.metadata.create_all(bind=db.engine)

            inspector = inspect(db.engine)
            assert (
                "services" in inspector.get_table_names()
            ), "Table 'services' was not created"

            test_service_1 = Service(
                service_name="Test Service A",
                owner_team="Team A",
                repository_source="https://github.com/test/repoA",
                lifecycle_status="development",
                consolidation_confict=False,
            )
            db.session.add(test_service_1)

            test_service_2 = Service(
                service_name="Test Service B",
                owner_team="Team B",
                repository_source="https://github.com/test/repoB",
                lifecycle_status="development",
                consolidation_confict=True,
            )
            db.session.add(test_service_2)

            test_service_3 = Service(
                service_name="Test Service B",
                owner_team="Team C",
                repository_source="https://github.com/test/repoC",
                lifecycle_status="maintenance",
                consolidation_confict=True,
            )
            db.session.add(test_service_3)
            db.session.commit()
        yield client

        with app.app_context():
            db.Model.metadata.drop_all(bind=db.engine)