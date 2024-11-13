import base64

import requests
from enum import Enum
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

from shared.config import get_config
from shared.models import Service
from shared.utils import deserialized

config = get_config()

app = Flask(__name__)
app.config.from_object(config)

db = SQLAlchemy(app)
db.Model = Service

class LifeCycleStatus(Enum):
    NEW = "new"
    DEVELOPMENT = "development"
    RELEASED = "released"
    MAINTENANCE = "maintenance"
    SUNSET = "sunset"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

SERVICE_KEYS = [
     "id",
     "service_name",
     "owner_team",
     "repository_source",
     "lifecycle_status",
     "consolidation_conflict",
     "last_updated",
]

@app.route("/services", methods=["GET"])
def get_services():
    session = db.session
    query = session.query(Service)
    query = query.filter(Service.consolidation_conflict == False)  # do not return conflicts
    services = query.all()
    try:
        response = deserialized(services, keys=SERVICE_KEYS)
    except Exception as serialization_error:
        app.logger.error(serialization_error)
        return jsonify({"error": "Failed to extract data for the service correctly"}), 500
    return jsonify(response)


@app.route("/services/<int:service_id>/lifecycle", methods=["PUT"])
def update_lifecycle(service_id):
    lifecycle_options = {

    }
    data = request.json
    new_lifecycle = data.get("lifecycle_status")
    try:
        lifecycle = str(LifeCycleStatus[new_lifecycle.upper()])
    except KeyError:
        return jsonify({"error": "Invalid lifecycle status"}), 400

    session = db.session
    service = session.query(Service).filter(Service.id == service_id).first()
    if not service:
        return jsonify({"error": "Service not found"}), 404

    service.lifecycle_status = lifecycle
    db.session.commit()
    return jsonify({"message": "Lifecycle updated successfully"}), 200


@app.route("/services/query", methods=["GET"])
def query_services():
    args = request.args
    session = db.session
    query = session.query(Service)

    if "name" in args:
        query = query.filter(Service.service_name.ilike(f"%{args['name']}%"))
    if "team" in args:
        query = query.filter(Service.owner_team.ilike(f"%{args['team']}%"))
    if "status" in args:
        query = query.filter(Service.lifecycle_status == args["status"])

    query = query.filter(Service.consolidation_conflict == False)  # do not return conflicts
    services = query.all()
    try:
        response = deserialized(services, keys=SERVICE_KEYS)
    except Exception as serialization_error:
        app.logger.error(serialization_error)
        return jsonify({"error": "Failed to extract data for the service correctly"}), 500
    return jsonify(response)

@app.route("/services/conflicts", methods=["GET"])
def list_conflicts():
    session = db.session
    query = session.query(Service)
    services = query.filter(Service.consolidation_conflict == True).all()
    try:
        response = deserialized(services, keys=SERVICE_KEYS)
    except Exception as serialization_error:
        app.logger.error(serialization_error)
        return jsonify({"error": "Failed to extract data for the service correctly"}), 500
    return jsonify(response)



@app.route("/services/<int:service_id>/resolve_conflict", methods=["PUT"])
def resolve_conflict(service_id):
    session = db.session
    query = session.query(Service).filter(Service.id == service_id)
    query = query.filter(Service.consolidation_conflict == True)
    service = query.first()
    if not service:
        return jsonify({"error": "Service not found"}), 404

    if service.consolidation_conflict:
        service.consolidation_conflict = False
        db.session.commit()
        return jsonify({"message": "Conflict resolved successfully"}), 200
    return jsonify({"message": "No conflict to resolve"}), 200


@app.route("/trigger/dag", methods=["POST"])
def trigger_dag():
    data = request.json
    if "repository_name" not in data:
        return jsonify({"error": "repository_name is required"}), 400

    try:
        headers = {
            "Authorization": f"Bearer {app.config.get('AIRFLOW_API_TOKEN')}",
            "Content-Type": "application/json",
        }
        if not app.config.get("AIRFLOW_API_TOKEN") and app.config.get(
            "AIRFLOW_CREDENTIALS"
        ):
            encoded_credentials = base64.b64encode(
                app.config.get("AIRFLOW_CREDENTIALS").encode("utf-8")
            ).decode("utf-8")
            headers["Authorization"] = f"Basic {encoded_credentials}"

        payload = {"conf": {"repo_list": [data["repository_name"]]}}
        response = requests.post(
            app.config.get("AIRFLOW_TRIGGER_URL"), headers=headers, json=payload
        )

        if response.status_code == 200:
            return jsonify({"status": "Airflow DAG triggered successfully"}), 200
        return jsonify({"error": response.text}), response.status_code
    except (requests.HTTPError, Exception) as e:
        app.logger.error(e)
        print(e, app.config.get("AIRFLOW_API_TOKEN"))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    db.create_all()
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
