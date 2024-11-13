import datetime
import json
import logging
import os
import sys

from kafka import KafkaConsumer
from sqlalchemy.exc import SQLAlchemyError

# editing the path here so the consumer can run from the base of the project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from shared.config import get_config
from shared.models import Service, init_db

config = get_config()

_, Session = init_db(config)


def consolidate_data(session, new_data):
    try:
        existing_service = (
            session.query(Service)
            .filter_by(service_name=new_data["project_name"])
            .first()
        )
        in_conflict = False

        if existing_service:
            if new_data["owner_team"] != existing_service.owner_team:
                existing_service.owner_team = new_data["owner_team"]

            if new_data["repository_source"] != existing_service.repository_source:
                logging.warning(
                    f"Conflict: Duplicate service names from different repositories for {new_data['project_name']}."
                )
                in_conflict = True

            if new_data["lifecycle_status"].lower() == "deprecated":
                existing_service.lifecycle_status = "deprecated"

            existing_service.last_updated = datetime.datetime.utcnow()

        else:
            new_service = Service(
                service_name=new_data["project_name"],
                owner_team=new_data["owner_team"],
                repository_source=new_data["repository_source"],
                lifecycle_status=new_data["lifecycle_status"],
                consolidation_confict=in_conflict,
                last_updated=datetime.datetime.utcnow(),
            )
            session.add(new_service)

        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Database error during consolidation: {e}")


def process_message(session, message):
    try:
        message = json.loads(message)
        logging.info(f"Processing message: {message}")
        consolidate_data(session, message)
    except Exception as e:
        logging.error(f"Error processing message: {e}")


def run_consumer():
    logging.info("Starting Kafka consumer...")
    consumer = KafkaConsumer(
        config.KAFKA_TOPIC,
        bootstrap_servers=config.KAFKA_BROKER,
        security_protocol="PLAINTEXT",
        auto_offset_reset="latest",
        enable_auto_commit=False,
        group_id=config.KAFKA_CONSUMER_GROUP,
        api_version=(3, 8, 0),
    )

    session = Session()
    try:
        for message in consumer:
            process_message(session, message.value.decode("utf-8"))
            consumer.commit()
    except Exception as e:
        logging.error(f"Error in consumer: {e}")
    finally:
        consumer.close()
        session.close()
        logging.info("Kafka consumer shut down.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_consumer()
