# Discovery

This is a discovery service based on airflow and kafka. It parses github searching for manifests, collects the data periodically and sends the results to a publisher API.

## How to install
1. Make sure you have an airflow instance
2. Make sure you have a kafka instance
3. Connect a consumer to your topic if this is the first time you use the topic

```
# consumer example to help initialize and test your topics, it requires kafka-python
from kafka import KafkaConsumer

TOPIC="github-scanner-events"

consumer = KafkaConsumer(
    bootstrap_servers='127.0.0.1:9092',
    security_protocol="PLAINTEXT",
    auto_offset_reset='earliest',
    api_version=(3, 8, 0),
)

consumer.subscribe(topics=TOPIC)

for message in consumer:
    print(f"{message.partition}:{message.offset} v={message.value}")
```

4. Install locally the rest

```
python -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

5. Run your dag
6. Setup your db in postgres and configure your project (`alembic.ini` and `shared/config.py`)
7. Initialize your db using alembic: `alembic upgrade head`

## How to run:

### API
```
export FLASK_APP=service_api
flask run
```
at the base of the project

### Consumer
`python consumer/consumer.py` at the base of the project

### DAG
Add the dag to your airflow instance


## How to test:

```
export FLASK_ENV=testing
pytest ./tests -v -s
```


## How to test using docker?
Docker compose seems the way to go, it is ugly hackish, but it runs after all. To make it work:

1. In infra (`cd infra`), run `./mkdir_base.sh`
2. Copy your dag to the `Airflow/dags` directory
3. Run: `docker-compose up -d`

This will setup all the infra you need, however, you need still to configure your consumer and service to get them to collaborate with the infra you just provisioned. Update your db settings and your API keys both for github and airflow if you plan on using airflow keys.

