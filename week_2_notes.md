# Week 2

> [!IMPORTANT]
Since I want to learn Apache Airflow, I am following the 2022 cohort version of this week. 
The most recent version of the course covering this week ([2024 cohort](https://github.com/DataTalksClub/data-engineering-zoomcamp/tree/main/02-workflow-orchestration)) uses Mage. I'll skim the material and might do a second pass at some point, if I find it necessary

## [DE Zoomcamp 2.1.1 - Data Lake](https://www.youtube.com/watch?v=W3Zm6rjOq70&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb)

### What is a Data Lake?

A Data Lake is a central repository that holds big data from many sources. 
The data it holds can either be structured, semi-structured, or unstructured.

Data Lakes are extensively used for ML and analytics. They also make use of metadata for faster access to data.

Data Lake solutions need to be secure, scalable, and its HW inexpensive to be able to store as much data as quickly as possible.

### Data Lake vs Data Warehouse
- Data lake: 
    - Unstructured data
    - Target users are data scientists/analysts
    - Huge amounts of data (petabytes)
    - Use cases: stream processing, ML, real-time analytics
- Data warehouse: 
    - Structured data
    - Target users are business analysts
    - Smaller amounts of data (petabytes)
    - Use cases: batch processing or BI reporting

### How did it start? / Why did Data Lakes become popular?
- Companies realized the value of data
- Data cannot always be well-defined from the get go. Store now and figure out what to do with it later. Data Lakes allow for this.
- Increase in Data Scientists and R&D on data products
- This prompted the need for cheap storage of Big Data

### ETL vs ELT
- ETL = Export-Transform-Load
    - Mainly used for small amount of data
    - Provides support for Data Warehouse (Schema on Write)
        - First define schema, then write data
- ELT = Export-Load-Transform
    - Mainly used for large amount of data
    - Provides support for Data Lake (Schema on Read)
        - First write (store) data, define relationships when reading data

### Data Lake Pitfalls
- Data Swamp
    - Makes it very hard to use the data
    - Can happen due to lack of versioning, conflicting schemas, lack of metadata
    - Joins not possible (e.g. no foreign key available)

### Data Lake Cloud Solutions by Various Providers
- GCP: Cloud Storage
- AWS: S3
- Azure Blob


## [DE Zoomcamp 2.2.1 - Introduction to Workflow Orchestration](https://www.youtube.com/watch?v=0yK7LXwYeD0&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb)

### What is Workflow Orchestration?

Data pipeline takes data as input, does something, then outputs the data in a different form.

![week 1pipeline](images/2.2.1/image-1.png)

The pipeline downloads csv data from internet, then reads it, then inserts to a Postgres database.

This is not a very good idea, because if either the download fails or the database connection fails, the entire script fails and have to start over.

Better to create multiple files:
- Download data
- Ingest csv to postgres

Also we can parametrize the various scripts or execute them at separate intervals.

![currentpipeline](images/2.2.1/image-2.png)

How can we set it up? 
- For example we can do 2 Python scripts and 1 bash script.
- Make ingest (?)

During week 2 a different pipeline will be made:
- First download with wget
- Parquetize
- Upload to GSC (possibly also to AWS S3 in parallel)
- Upload to BigQuery

![newpipeline](images/2.2.1/image-3.png)

Each step depends on the previous step, so need to execute in order and verify success of previous step.

Rather than a pipeline, this is sometimes also called a Workflow or DAG (Directed Acyclic Graph). A DAG specifies dependencies between set of Tasks with explicit execution order. Task is a defined unit of work.

We have this workflow, but how do we orchestrate this to ensure:
- Workflow dependencies are respected
- Retry mechanism is in place
- Workflow is parametrized
- Logs/history can easily be inspected

We can use Make, but this is more suitable for smaller workflows. For Data Workflow Orchestration following tools are used:
- Luigi
- Apache Airflow (one of the more popular ones)
- Mage
- Prefect


## [DE Zoomcamp 2.3.1 - Setup Airflow Environment with Docker-Compose](https://www.youtube.com/watch?v=lqDMzReAtrw&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb)

### Introduction

Airflow consists of:
- **Web server** (handy GUI to inspect, trigger, and debug DAGs and tasks).
- **Scheduler** (scheduling jobs, triggering/scheduling workflows, monitors tasks and DAGs)
- **Worker** (executes tasks given by scheduler)
- **Metadata Database** (backend to airflow env, used by the scheduler/executor/web server to store state of the environment)
- Other:
    - redis: message broker, forwards messages from scheduler to workers
    - flower: app for monitoring the environment (port 5555)
    - airflow-init: initialization service

### Setup

> [!NOTE]
> 1. Previously I created my Google credentials when doing the Terraform setup in week 1. I did this in Windows, not WSL. Therefore the Google Service Account credentials json file was stored in my Windows Downloads folder. I moved it to Linux and renamed it according to the course instructions for this week.
> 2. There was an instruction to increase the memory for Docker Engine, but since Docker is using WSL2, this is not possible directly. Instead I would have to make a .wslconfig file. I will try it without changing this setting, but if I do run into memory problems later on, I will look into this.

#### **Step 1**: Create `.google/credentials` and place `google_credentials.json` there.

#### **Step 2**: Create `airflow` directory with subfolders `dags`, `log`, `plugins`, `scripts`. 

```bash
mkdir -p airflow/dags airflow/logs airflow/plugins airflow/scripts
```

In this directory I will set up Airflow as it has already been done in `week_2/airflow`. 

#### **Step 3**: add `entrypoint.sh` to `scripts` folder

Copy `entrypoint.sh` from `week_2` course folder into newly made `airflow/scripts` folder 

#### **Step 3**: Set the Airflow user by creating a `.env` file with your user id

Run this command in the `project/airflow` folder:

```bash
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

#### **Step 5**: Copy `Dockerfile` from `week_2/airflow` folder

#### **Step 6**: Import the official docker setup file

```bash
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/stable/docker-compose.yaml'
```

#### **Step 7**: adjust `docker-compose.yaml` to use our dockerfile instead of default airflow image

This part is not explained very clearly in the [course notes](https://github.com/DataTalksClub/data-engineering-zoomcamp/blob/main/cohorts/2022/week_2_data_ingestion/airflow/1_setup_official.md). The final result is given (see `week_2/docker-compose.yaml`), but the changes to make are not mentioned explicitly and I did not want to spend a lot of time sifting through the YAML files to figure out what changes to make.

Therefore I used the [notes by Alvaro](https://github.com/ziritrion/dataeng-zoomcamp/blob/main/notes/2_data_ingestion.md) which explain the steps very clearly. But I was running into an error:

```bash
(base) kd@DESKTOP-U30C45H:~/coding-practice/data-engineering-course/week_2_data_ingestion_airflow_2022/project/airflow$ docker-compose up airflow-init
WARN[0000] /home/kd/coding-practice/data-engineering-course/week_2_data_ingestion_airflow_2022/project/airflow/docker-compose.yaml: `version` is obsolete
[+] Running 4/4
 ✔ Network airflow_default           Created                                                                                                                                           0.0s
 ✔ Container airflow-redis-1         Created                                                                                                                                           0.1s
 ✔ Container airflow-postgres-1      Created                                                                                                                                           0.1s
 ✔ Container airflow-airflow-init-1  Created                                                                                                                                           0.1s
Attaching to airflow-init-1
airflow-init-1  | The container is run as root user. For security, consider using a regular user account.
airflow-init-1  | ....................
airflow-init-1  | ERROR! Maximum number of retries (20) reached.
airflow-init-1  |
airflow-init-1  | Last check result:
airflow-init-1  | $ airflow db check
airflow-init-1  | Traceback (most recent call last):
airflow-init-1  |   File "/home/airflow/.local/bin/airflow", line 5, in <module>
airflow-init-1  |     from airflow.__main__ import main
airflow-init-1  |   File "/home/airflow/.local/lib/python3.6/site-packages/airflow/__init__.py", line 34, in <module>
airflow-init-1  |     from airflow import settings
airflow-init-1  |   File "/home/airflow/.local/lib/python3.6/site-packages/airflow/settings.py", line 35, in <module>
airflow-init-1  |     from airflow.configuration import AIRFLOW_HOME, WEBSERVER_CONFIG, conf  # NOQA F401
airflow-init-1  |   File "/home/airflow/.local/lib/python3.6/site-packages/airflow/configuration.py", line 1129, in <module>
airflow-init-1  |     conf.validate()
airflow-init-1  |   File "/home/airflow/.local/lib/python3.6/site-packages/airflow/configuration.py", line 224, in validate
airflow-init-1  |     self._validate_config_dependencies()
airflow-init-1  |   File "/home/airflow/.local/lib/python3.6/site-packages/airflow/configuration.py", line 267, in _validate_config_dependencies
airflow-init-1  |     raise AirflowConfigException(f"error: cannot use sqlite with the {self.get('core', 'executor')}")
airflow-init-1  | airflow.exceptions.AirflowConfigException: error: cannot use sqlite with the CeleryExecutor
airflow-init-1  |
airflow-init-1 exited with code 1
```

I tried a lot of troubleshooting steps, but to no avail.

At this point I tried to run the setup in the course folder `week_2/airflow`, which ran fine. So I figured there must be some discrepancy between my setup vs the course's setup (previously I thought it might have something to do with compatibility between docker compose and python). Upon comparing the course's `docker-compose.yaml` file with mine, I found that the `docker-compose.yaml` file from the Airflow documentation page contains the following line:

```yaml
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
```
After changing it as follows, I did not run into error: cannot use sqlite with the CeleryExecutor any longer:

```yaml
AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
```

Alvaro's notes did not point out this discrepancy between his `docker-compose.yaml` file and the one from the Airflow documentation.

During my troubleshooting, I checked Stack Overflow and found someone else ran into the same `cannot use sqlite with the CeleryExecutor` error. I wrote this [answer](https://stackoverflow.com/a/78877992/11486502).

#### **Step 8**: adjust `docker-compose.yaml` to use our dockerfile instead of default airflow image

#### **Step 9**: Initialize the scheduler, DB, and other config

```bash
docker build
```

### **Step 10**: Start all the services

```bash
docker compose up airflow-init
```


## [DE Zoomcamp 2.3.4 - Optional: Lightweight Local Setup for Airflow](https://www.youtube.com/watch?v=A1p5LQ0zzaQ&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb)

This shows how to use a lightweight setup to Airflow.

Although my laptop seemed to be able to run the full version, I still followed through these steps to increase my familiarity with Airflow setup using Docker Compose.

I first tried following the YouTube video, but I was getting errors when running `docker compose up`. Then I looked at the [instructions on GitHub](https://github.com/DataTalksClub/data-engineering-zoomcamp/blob/main/cohorts/2022/week_2_data_ingestion/airflow/2_setup_nofrills.md).

After following those, I also got an error about `entrypoint.sh` not being run due to lack of permission. I changed this line in the `docker-compose.yaml` file from `-50000` to `-1000` which is what I get when I run `echo -e "AIRFLOW_UID=$(id -u)"`:

```yaml
user: "${AIRFLOW_UID:-1000}:0"
```

After that it worked.


## [DE Zoomcamp 2.3.2 - Ingesting Data to GCP with Airflow](https://www.youtube.com/watch?v=9ksX9REfL8w&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb&index=19)

Now that our Airflow environment is set up, the next step will be to write an ingestion pipeline to ingest compressed, raw data into a data lake in a more queryable format.

The anatomy of a dag and components of a typical workflow will be covered. 

### DAG

There are four main components to a DAG:
1. DAG: Directec Acyclic Graph
    - Specifies dependencies between tasks
    - DAG has an explicit execution order
    - DAG has a beginning and an end 
2. Task: defined unit of work
    - Also known as operatores
    - Describe what to do such as fetching data, running analysis, triggering other systems, etc.
3. DAG run: individual execution of a DAG
4. Task instance: individual run of a single task

Airflow DAG is defined in a Python file and is composed of:
- DAG definition 
- Tasks
- Task dependencies

Declaring a DAG can be done with a context manager or a constructor or a decorator.

Tasks:
- A DAG runs through a series of tasks. 
- Types of tasks:
    - Operators: predefined tasks 
    - Sensors: special subclass of operators which are event listeners
- Best practice: tasks should be atomic, i.e. standalone and do not share resources with other tasks.

### Task Dependencies

Responsible for control flow within a DAG. A task operator does not live on its own. It typically has other task operators that it depends on and/or that depend on it.

Dependencies are specified using `>>` or `<<`. Alternatively, if you want to set dependencies explicitly, you can use the `.set_downstream()` and `.set_upstream()` methods.

A task will run when all of its upstream dependencies have succeeded, though there are ways to further customize this behavior.

Passing data between tasks can happen in 2 ways:
1. `XCOM ` (?) variable
2. Upload and download data from storage service

Airflow send tasks to workers as space becomes available. 

You can run DAGs manually, via API, or scheduled using scheduled interval variable.
<<<<<<< Updated upstream


## Walkthrough of data ingestion script `data_ingestion_gcs_dag.py`

First some libraries are imported, for example: `BashOperator` and `PythonOperator`. Also some libraries are imported that were installed via the `requirements.txt` file from the Docker setup. For example `google.cloud`, which will interact with GCS storage. Besides that a library is imported to interact with BigQuery.

Some values are imported from the environment variables which were set in the Docker setup, like the GCP project and bucket name, as well as the name of the BigQuery table that we will be writing our data into. Note that these were all defined in the `docker-compose.yaml` file. 

Next, some functions follow for our operators: `format_to_parquet` and `upload_to_gcs`. 

Then, a DAG is defined using a context manager. It has the following tasks defined: `download_dataset_task`, `format_to_parquet_task`, `local_to_gcs_task`, and `bigquery_external_table_task`. The second and third functions are PythonOperators. They have an argument `callable`. The functions that were previously defined `format_to_parquet` and `upload_to_csv` are provided as values to these arguments.

Short descriptions:
- **download_dataset_task**: downloads csv file using a `curl` command from the url specified at the top of the script and store either in memory (Cloud service) or in a temporary folder (Docker)
- **format_to_parquet_task**: convert from csv to parquet (uses `pyarrow` library)
- **local_to_gcs_task**: uploads given a filepath to the GCS bucket
- **bigquery_external_table_task**: from GCS bucket to BigQuery table

At the end the dependencies of the tasks are defined. 

When a DAG is run (it can be triggered manually), the status will update in the Airflow browser UI, the log can be inspected.
=======
>>>>>>> Stashed changes


## Overview of data ingestion script `data_ingestion_gcs_dag.py`

First some libraries are imported, for example: `BashOperator` and `PythonOperator`. Also some libraries are imported that were installed via the `requirements.txt` file from the Docker setup. For example `google.cloud`, which will interact with GCS storage. Besides that a library is imported to interact with BigQuery.

Some values are imported from the environment variables which were set in the Docker setup, like the GCP project and bucket name, as well as the name of the BigQuery table that we will be writing our data into. Note that these were all defined in the `docker-compose.yaml` file. 

Next, some functions follow for our operators: `format_to_parquet` and `upload_to_gcs`. 

Then, a DAG is defined using a context manager. It has the following tasks defined: `download_dataset_task`, `format_to_parquet_task`, `local_to_gcs_task`, and `bigquery_external_table_task`. The second and third functions are PythonOperators. They have an argument `callable`. The functions that were previously defined `format_to_parquet` and `upload_to_csv` are provided as values to these arguments.

Short descriptions:
- **download_dataset_task**: downloads csv file using a `curl` command from the url specified at the top of the script and store either in memory (Cloud service) or in a temporary folder (Docker)
- **format_to_parquet_task**: convert from csv to parquet (uses `pyarrow` library)
- **local_to_gcs_task**: uploads given a filepath to the GCS bucket
- **bigquery_external_table_task**: from GCS bucket to BigQuery table

At the end the dependencies of the tasks are defined. 

When a DAG is run (it can be triggered manually), the status will update in the Airflow browser UI, the log can be inspected.


## Walkthrough of data ingestion script `data_ingestion_gcs_dag.py`

> [!NOTE]
    I will now go step by step to run the DAG. I will use the normal Airflow setup, rather than the lightweight one.

    Note that we still have Google Cloud Storage Bucket and BigQuery dataset from week 1. So we don't need to do anything with Terraform to set it up. The VM is down, but we will not use that anyway. We are running it locally on WSL2.

#### Step 1: copy `week_2_data_ingestion_airflow_2022/airflow/dags/data_ingestion_gcs_dag.py` to `week_2_data_ingestion_airflow_2022/project/airflow`

#### Step 2: run docker containers

cd into `week_2_data_ingestion_airflow_2022/project/airflow` and run `docker compose up`

#### Step 3: go to `localhost:8080` and trigger the DAG

You should see the DAG now as below:

![airflowdag](images/2.3.2/image.png)

Clicking on the DAG link should show:

![airflowdaglink](images/2.3.2/image-1.png)

Clicking on the play icon on the the top right shows the option to trigger the DAG. Upon clicking on it, the steps in the DAG will start updating their status.

#### Step 4: troubleshooting

In my case, the DAG failed to complete the final task `bigquery_external_table_task`.

Clicking on the status color will show the option to view the logs.

![dagstatus](images/2.3.2/image-2.png)

In the log I found this line:

![failedtasklog](images/2.3.2/image-3.png)

This seems to suggest that the name that the DAG assumes for my BigQuery table does not match the name of it in GCP.

Let's check the name in GCP:

![BQdatasetname](images/2.3.2/image-4.png)

It's called `demo_dataset`

Inspecting the `variables.tf` file with which we set it up using Terraform, it indeed confirms this was the name we gave it previously:

```
variable "bq_dataset_name" {
    description = "My BigQuery Dataset Name"
    default = "demo_dataset"
}
```

We will take following steps now:
1. `CTRL+C` to stop all containers
2. `docker compose down` to remove them
3. Change the BigQuery dataset name to `demo_dataset`. 
    - See more details on how to do this below under 'step 3 explanation'
5. `docker compose up`
    - Note that `docker build` was not needed. I initially expected it would have been. I asked ChatGPT about it, see answer below under 'step 5 explanation'.
6. Run the DAG

![dagsuccesful](images/2.3.2/image-5.png)

##### Step 3 explanation

Note that `data_ingestion_gcs_dag.py` takes the dataset name from the environment variable `BIGQUERY_DATASET`. 

```python
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", 'trips_data_all')
```

If this environment variable is not set, the default is `trips_data_all`. We need to either change the default or set the environment variable in `docker-compose.yaml`.

We will do the latter:

```yaml
  build:
    context: .
    dockerfile: ./Dockerfile
  environment:
    &airflow-common-env
    AIRFLOW__CORE__EXECUTOR: CeleryExecutor
    AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__BROKER_URL: redis://:@redis:6379/0
    AIRFLOW__CORE__FERNET_KEY: ''
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
    AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
    AIRFLOW__API__AUTH_BACKENDS: 'airflow.api.auth.backend.basic_auth,airflow.api.auth.backend.session'
    GOOGLE_APPLICATION_CREDENTIALS: /.google/credentials/google_credentials.json
    AIRFLOW_CONN_GOOGLE_CLOUD_DEFAULT: 'google-cloud-platform://?extra__google_cloud_platform__key_path=/.google/credentials/google_credentials.json'
    GCP_PROJECT_ID: 'dtc-de-course-430705'
    GCP_GCS_BUCKET: 'dtc-de-course-430705-terra-bucket'
    BIGQUERY_DATASET: 'demo_dataset'
```

The last line is the change that was made.

##### Step 5 explanation

Answer by ChatGPT why `docker build` is not needed to update environment variable based on the change made in the docker-compose.yaml file:

```
You didn’t need to run docker-compose build because you only changed the environment variables in the docker-compose.yaml file, not the Dockerfile or the underlying Docker image. The docker-compose build command is used to rebuild Docker images when the Dockerfile or the build context changes. However, environment variables defined in docker-compose.yaml are applied at runtime, so when you ran docker compose down and docker compose up, the updated environment variables (including BIGQUERY_DATASET) were passed to the running containers without needing to rebuild the images. This allowed your DAG to recognize the new environment variable immediately.
```

## [DE Zoomcamp 2.3.3 - Ingesting Data to Local Postgres with Airflow](https://www.youtube.com/watch?v=s2U8MWJH5xA&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb)



## [DE Zoomcamp 2.4.1 - Moving Files from AWS to GPC with Transfer Service](https://www.youtube.com/watch?v=rFOFTfD1uGk&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb)



## [DE Zoomcamp 2.4.2 - Configuring the Transfer Service with Terraform](https://www.youtube.com/watch?v=VhmmbqpIzeI&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb)



