#!/usr/bin/env bash
set -e

:  '

This is the desired project tree

.
├── Airflow
│   ├── config
│   ├── dags
│   ├── logs
│   └── plugins
├── Kafka
│   ├── kafka-data
│   └── zookeeper-data
├── Postgres
│   ├── init.sql
│   └── pg_data
├── Redis
   └── config
'

mkdir Airflow
mkdir Airflow/config
mkdir Airflow/dags
mkdir Airflow/logs
mkdir Airflow/plugins

mkdir Kafka
mkdir Kafka/kafka-data
mkdir Kafka/zookeper-data

mkdir Postgres
mkdir Postgres/pg_data

mkdir Redis
mkdir Redis/config
mkdir Redis/data

cp init.sql Postgres
echo -e "AIRFLOW_UID=$(id -u)" > .env
