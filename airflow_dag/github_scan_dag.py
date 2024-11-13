import json
from datetime import timedelta

import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from kafka import KafkaProducer
from kafka.errors import KafkaError

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

GITHUB_TOKEN = "github_pat_000000"
GITHUB_URL = "https://api.github.com/org/sailpoint/repos"
KAFKA_SERVER = "kafka:9092"
KAFKA_TOPIC = "github-scanner-events"
REQUIRED_FIELDS = ["project_name", "owner_team", "lifecycle_status", "organization"]
MANIFEST_FORMAT = ".config.json"


def send_message(producer: KafkaProducer, kafka_topic: str, message: dict) -> None:
    serialized_message = serialize_message(message)
    if serialized_message:
        try:
            future = producer.send(kafka_topic, serialized_message)
            future.get(timeout=3)
        except KafkaError as error:
            print(f"Failed to produce a message: {message} with error {error}")
    else:
        print("Nothing to send")


def serialize_message(message: dict) -> str | None:
    serialized_message = None
    try:
        serialized_message = json.dumps(message).encode("utf-8")
    except (ValueError, KeyError, TypeError) as error:
        print(f"Invalid message, failed to encode: {message} with error {error}")
    return serialized_message


def fetch_user_repositories(github_token: str) -> list:
    url = GITHUB_URL
    headers = {"Authorization", f"token {github_token}"}  # for now not used
    repositories = []
    page = 1

    while True:
        response = requests.get(url, params={"per_page": 100, "page": page})
        response.raise_for_status()
        repos = response.json()
        if not repos:
            break
        repositories.extend(repo["full_name"] for repo in repos)
        page += 1
    return repositories


def process_repository(
    producer: KafkaProducer, kafka_topic: str, repo_name: str, github_token: str
):
    headers = {"Authorization": f"token {github_token}"}  # for now not used
    url = f"https://api.github.com/repos/{repo_name}/contents/{MANIFEST_FORMAT}"
    print(f"Requesting manifest {MANIFEST_FORMAT} from url: {url}")
    response = requests.get(url)

    if response.status_code == 200:
        try:
            file_data = response.json()
            config_content = json.loads(requests.get(file_data["download_url"]).text)

            config_content["repository_source"] = repo_name
            print(f"configuration info {config_content} will be sent")

            if all(field in config_content for field in REQUIRED_FIELDS):
                send_message(
                    producer=producer, kafka_topic=kafka_topic, message=config_content
                )
                print(f"Sent config for {repo_name} to Kafka")
            else:
                print(f"Invalid manifest in {repo_name}: Missing required fields")
        except (json.JSONDecodeError, ValueError, Exception) as e:
            print(f"Error processing {repo_name}: {e}")
    else:
        print(f"manifest not found in {repo_name}")


def collect_configs(**context):
    github_token = context["params"].get("github_token")
    repo_list = context["params"].get("repo_list", [])
    kafka_topic = context["params"].get("kafka_topic")

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_SERVER,
        security_protocol="PLAINTEXT",
        api_version=(3, 8, 0),
        retries=3,
        linger_ms=100,
        batch_size=10,
    )

    if not repo_list:
        repo_list = fetch_user_repositories(github_token)

    for repo_name in repo_list:
        process_repository(
            producer=producer,
            kafka_topic=kafka_topic,
            repo_name=repo_name,
            github_token=github_token,
        )
    producer.flush()
    producer.close()


with DAG(
    "github_personal_config_collector",
    default_args=default_args,
    description="Collects manifest files from personal GitHub repositories",
    schedule_interval="@daily",
    start_date=days_ago(1),
    catchup=False,
) as dag:

    collect_task = PythonOperator(
        task_id="collect_configs",
        python_callable=collect_configs,
        provide_context=True,
        params={
            "github_token": GITHUB_TOKEN,
            "kafka_topic": KAFKA_TOPIC,
            "repo_list": [],
        },
    )
