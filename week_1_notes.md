# Week 1

## [DE Zoomcamp 1.2.1 - Introduction to Docker](https://youtu.be/EYNwNlOrpr0?si=rw7Z_lDFc1A7Fo36)

### What is Docker?

Docker is a platform that uses containers to create, deploy, and run applications.

### What are the benefits of Docker?

- Self-contained: Docker containers contain all dependencies needed to run the application (e.g. data processing pipeline). Avoids conflict between different Docker containers.
- Portability: Run in another environment &rarr; reproducibility
- Lightweight

### Why care about Docker as DE?

- Local experiments
- Integration tests (CI/CD)
    - Github Actions, Jenkins
- Reproducibility
- Running pipelines on the cloud
    (AWS Batch, Kubernetes jobs)
- Spark
- Serverless (AWS lambda)
    - processing data one record at a time

### docker commands

Run Ubuntu image in interactive mode and start Bash:
```docker
docker run -it ubuntu bash
```

Run Python image in interactive mode:
```docker
docker run -it ubuntu python:3.xx
```

Run Python image but start Bash:
```docker
docker run -it --entrypoint=bash python:3.xx
```

Here you can install libraries for instance.


### Dockerfile

You can automate the creation of Docker images. This installs Pandas and overwrites the entry point:

```
FROM python:3.12

RUN pip install pandas

ENTRYPOINT [ "bash" ]
```

You can build an image from a Dockerfile:

```bash
docker build -t test:pandas .
```

`-t` tags the image.
`test` will be the name and `pandas` will be the tag.
`.` will build image in the current directory where it will look for a Dockerfile.

If you also want to copy a file from the current working directory to the container in a location `app`:

```docker
FROM python:3.12

RUN pip install pandas

WORKDIR /app
COPY pipeline.py pipeline.py

ENTRYPOINT [ "python", "pipeline.py"]
```

Let's say this is our Python pipeline.py file.
```python
import sys
import pandas as pd


print(sys.argv)

day = sys.argv[1]

print(day)
```

It takes an argument. You can provide the argument to the `docker run` command by appending it as follows:

```docker
docker run -it test:pandas 2024-07-04
```

Don't forget to build the Docker image first.

## [DE Zoomcamp 1.2.2 - Ingesting NY Taxi Data to Postgres](https://youtu.be/2JM-ziJt0WI?si=1Mi05VsHPgodbmVn)

Run Postgres in Docker and put data in Postgres database with a Python script.

First create a named volume (needed otherwise I was running into permission error):

```docker
docker volume create ny_taxi_data
```

Note: after running the Docker image (below), I was running into an error with the password. I took a couple troubleshooting steps, like removing the docker named volume and stopping/removing all unused volumes and containers. After that it worked. So i don't think this step to create a named volume is needed. 

Then run Docker image with config shown below in CMD:

```docker
docker run -it ^
    -e POSTGRES_USER="root" ^
    -e POSTGRES_PASSWORD="root" ^
    -e POSTGRES_DB="ny_taxi" ^
    -v C:/projects/data-engineering-course/week_1/2_docker_sql/ny_taxi_postgres_data:/var/lib/postgresql/data ^
    -p 5432:5432 ^
    postgres:13
```

`-v` (volume) command is to to map a folder in our file system on the host machine to a folder in the container.
Postgres needs to keep files in a filesystem.

`-p` is to specify a port

Next use cli client to access the database.

```
pgcli -h localhost -p 5432 -u root -d ny_taxi
```

In pgcli we can list the tables with `\dt`:
```
\dt
+--------+------+------+-------+
| Schema | Name | Type | Owner |
|--------+------+------+-------|
+--------+------+------+-------+
```

The code below is to read in the data from a csv file and create a database connection:
```python
import pandas as pd
from sqlalchemy import create_engine


DATA_FILEPATH = 'C:/projects/data-engineering-course/week_1/2_docker_sql/yellow_tripdata_2021-01.csv'

# This creates an iterator which can then be used in a loop 
# to read the data in chunks instead of all in memory in one go.
df_iter = pd.read_csv(DATA_FILEPATH, iterator=True, chunksize=100_000)

# Connect to Postgres (in Docker)
engine = create_engine('postgresql://root:root@localhost:5432/ny_taxi')
engine.connect()
```

We can check how Pandas will create a table
```python
# We can inspect how Pandas will try to create the table in Postgres.
# This is handy for checking the data types are as expected.
print(pd.io.sql.get_schema(df, name='yellow_taxi_data', con=engine))
```
We can see that datetime is not being recognized properly. Normally we would have to fix that.
```sql
CREATE TABLE yellow_taxi_data (
	"VendorID" BIGINT, 
	tpep_pickup_datetime TEXT, 
	tpep_dropoff_datetime TEXT, 
	passenger_count FLOAT(53), 
	trip_distance FLOAT(53), 
	"RatecodeID" FLOAT(53), 
	store_and_fwd_flag TEXT, 
	"PULocationID" BIGINT, 
	"DOLocationID" BIGINT, 
	payment_type BIGINT, 
	fare_amount FLOAT(53), 
	extra FLOAT(53), 
	mta_tax FLOAT(53), 
	tip_amount FLOAT(53), 
	tolls_amount FLOAT(53), 
	improvement_surcharge FLOAT(53), 
	total_amount FLOAT(53), 
	congestion_surcharge FLOAT(53), 
	airport_fee FLOAT(53)
)
```

Now we can create the table in Postgres first:
```python
df.head(n=0).to_sql(name='yellow_taxi_data', con=engine, if_exists='replace')
```

We can check it in pgcli:
```
root@localhost:ny_taxi> \d yellow_taxi_data;
+-----------------------+------------------+-----------+
| Column                | Type             | Modifiers |
|-----------------------+------------------+-----------|
| index                 | bigint           |           |
| VendorID              | bigint           |           |
| tpep_pickup_datetime  | text             |           |
| tpep_dropoff_datetime | text             |           |
| passenger_count       | bigint           |           |
| trip_distance         | double precision |           |
| RatecodeID            | double precision |           |
| store_and_fwd_flag    | text             |           |
| PULocationID          | bigint           |           |
| DOLocationID          | bigint           |           |
| payment_type          | bigint           |           |
| fare_amount           | double precision |           |
| extra                 | double precision |           |
| mta_tax               | double precision |           |
| tip_amount            | double precision |           |
| tolls_amount          | double precision |           |
| improvement_surcharge | double precision |           |
| total_amount          | double precision |           |
| congestion_surcharge  | double precision |           |
| airport_fee           | double precision |           |
+-----------------------+------------------+-----------+
```

Finally we can add each chunk of data into postgres as follows:
```python
while True:
        df = next(df_iter)
        df.to_sql(name='yellow_taxi_data', con=engine, if_exists='append')
        print('inserted chunk')
```

We can check the number of rows in Postgres:
```postgres
SELECT count(1) from yellow_taxi_data
```
which will give us:
```
+--------+
| count  |
|--------|
| 100000 |
+--------+
```
Next, we will use pgAdmin instead of pgcli.


## [DE Zoomcamp 1.2.3 Connecting pgAdmin and Postgres](https://youtu.be/hCAIVe9N0ow?si=NWVSa25g4QeRjzue)

Picking up where we left off last time, we can do some additional checks of our data in the database using pgcli:

```
root@localhost:ny_taxi> SELECT max(tpep_pickup_datetime), min(tpep_pickup_datetime), max(total_amount) FROM yellow_taxi_data;
+---------------------+---------------------+--------+
| max                 | min                 | max    |
|---------------------+---------------------+--------|
| 2021-01-31 23:56:00 | 2021-01-10 17:00:56 | 159.36 |
+---------------------+---------------------+--------+
```

In this session pgAdmin will be introduced. It is a GUI-based tool to manage a Postgres database.

We will run it in Docker:
```
docker run -it ^
    -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" ^
    -e PGADMIN_DEFAULT_PASSWORD="root" ^
    -p 8080:80 ^
    dpage/pgadmin4
```

Then we can go to the browser to `localhost:8080` and we see a GUI. After logging in we can create a new server.

In connection we specify the `Host name/address` to be `localhost`. Upon saving, we get an error message saying the connection is refused. What is happening is that pgAdmin is searching for our Postgres database, but that is in a different container. We need to connect the database in one container to pgAdmin in another container using a network.

At this point we stop all containers.

We create a network called `pg-network`:
```
docker network create pg-network
```

Then we will re-run the containers, specifying the `--network` flag:

```docker
docker run -it ^
    -e POSTGRES_USER="root" ^
    -e POSTGRES_PASSWORD="root" ^
    -e POSTGRES_DB="ny_taxi" ^
    -v C:/projects/data-engineering-course/week_1/2_docker_sql/ny_taxi_postgres_data:/var/lib/postgresql/data ^
    -p 5432:5432 ^
    --network=pg-network ^
    --name=pg-database ^
    postgres:13

docker run -it ^
    -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" ^
    -e PGADMIN_DEFAULT_PASSWORD="root" ^
    -p 8080:80 ^
    --network=pg-network ^
    --name=pgadmin ^
    dpage/pgadmin4
```

In the next session we will dockerize the ingestion script and run everything from Docker.

## [DE Zoomcamp 1.2.4 - Dockerizing the Ingestion Script](https://youtu.be/B1WwATwf-vY?si=-xj66cqaCgP6t1Rf)

The code from the last session is made into a python script called `ingest_data.py`.

Note: the course assumes the file format to be CSV. However the NY taxi dataset has been changed to parquet format. I asked ChatGPT to update the script to ingest parquet format, write to CSV, and then upload to Postgres. So the script below is quite different from the script used in the course. However, the purpose is no learn how to use Docker, not the script.


```python
import argparse
import pandas as pd
from sqlalchemy import create_engine
import requests
from tqdm import tqdm
import io

def main(params):
    user = params.user
    password = params.password
    host = params.host
    port = params.port
    db = params.db
    table_name = params.table_name
    url = params.url

    print('Start downloading Parquet file')

    response = requests.get(url, stream=True)
    if response.status_code == 200:
        print('Successfully downloaded the file')
    else:
        print(f'Failed to download the file. Status code: {response.status_code}')
        return

    total_size = int(response.headers.get('content-length', 0))
    chunk_size = 1024  # 1 KB
    downloaded_file = io.BytesIO()

    for data in tqdm(response.iter_content(chunk_size=chunk_size), total=total_size//chunk_size, unit='KB'):
        downloaded_file.write(data)

    downloaded_file.seek(0)  # Reset pointer to the start of the BytesIO object

    print('Finished downloading Parquet file and start reading into DataFrame')

    try:
        df = pd.read_parquet(downloaded_file)
        print('Successfully read into DataFrame')
    except Exception as e:
        print(f'Error reading Parquet file: {e}')
        return

    print('Finish reading into DataFrame and start exporting to CSV file')
    df.to_csv('output.csv', index=False)
    print('Finish exporting to CSV file')

    # Connect to Postgres (in Docker)
    print('Connecting to Postgres...')
    try:
        engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')
        print('Connected to Postgres successfully.')
    except Exception as e:
        print(f'Error connecting to Postgres: {e}')
        return

    # Read CSV in chunks and insert into database
    print('Start inserting data into Postgres')
    df_iter = pd.read_csv("output.csv", iterator=True, chunksize=100_000)

    i = 1
    while True:
        try:
            df = next(df_iter)
        except StopIteration:
            break
        except Exception as e:
            print(f'Error reading CSV chunk: {e}')
            break

        if i == 1:
            df.head(n=0).to_sql(name=table_name, con=engine, if_exists='replace')
        df.to_sql(name=table_name, con=engine, if_exists='append')
        print('Inserted chunk', i)
        i += 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest csv data to Postgres")

    parser.add_argument("--user", help="user name for postgres")
    parser.add_argument("--password", help="password for postgres")
    parser.add_argument("--host", help="host for postgres")
    parser.add_argument("--port", help="port name for postgres")
    parser.add_argument("--db", help="database name for postgres")
    parser.add_argument("--table-name", help="table name to write the results to")
    parser.add_argument("--url", help="url of the csv file")

    args = parser.parse_args()

    main(args)
```

The py file can be called with arguments as follows:

```ps
set URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet" ^
```

```ps
python ingest_data.py ^
    --user=root ^
    --password=root ^
    --host=localhost ^
    --port=5432 ^
    --db=ny_taxi ^
    --table-name=yellow-taxi-trips ^
    --url=%URL%
```

Now we will dockerize this as a pipeline.

Update the Dockerfile

```docker
FROM python:3.12

RUN pip install pandas sqlalchemy pyarrow psycopg2 requests tqdm

WORKDIR /app
COPY ingest_data.py ingest_data.py

ENTRYPOINT [ "python", "ingest_data.py" ]
```

Build the image:

```ps
docker build -t taxi_ingest:v001 .
```

First set the environment variable:
```ps
set URL="https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
```

Then run the image in Docker:
```ps
docker run -it ^
    --network=pg-network ^
    taxi_ingest:v001 ^
        --user=root ^
        --password=root ^
        --host=pg-database ^
        --port=5432 ^
        --db=ny_taxi ^
        --table-name=yellow_taxi_trips ^
        --url=%URL%
```

This will download the parquet file again, which takes a long time. Instead we will use a trick.

We can start an HTTP server in our folder:

```ps
python -m http.server
```

Now we can navigate to our folder using the browser and copy the link for the parquet file, which was already downloaded. We will provide that as URL instead of the online URL.

```ps
set URL="http://172.26.160.1:8000/temp.parquet"
```

```ps
docker run -it ^
    --network=pg-network ^
    taxi_ingest:v001 ^
        --user=root ^
        --password=root ^
        --host=pg-database ^
        --port=5432 ^
        --db=ny_taxi ^
        --table-name=yellow_taxi_trips ^
        --url=%URL%
```

In the next session we will use docker compose to run these commands in a YAML file instead of in two separate command prompt windows.

## [DE Zoomcamp 1.2.5 - Running Postgres and pgAdmin with Docker-Compose](https://youtu.be/hKI6PkPhpa0?si=68EVr2JXH6wkrTZm)

Our Docker compose file is intended to automatically start the postgres and pgadmin containers. Note that network is not specified, since Docker compose will automatically create a network named `data-engineering-course_default`.

```docker
services:
  pgdatabase:
    image: postgres:13
    environment:
      - POSTGRES_USER=root
      - POSTGRES_PASSWORD=root
      - POSTGRES_DB=ny_taxi
    volumes:
      - "./ny_taxi_postgres_data:/var/lib/postgresql/data:rw"
    ports:
      - "5432:5432"
  pgadmin:
    image: dpage/pgadmin4
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@admin.com
      - PGADMIN_DEFAULT_PASSWORD=root
    ports:
      - "8080:80"
```

Now we can run docker compose with the following command:

```bash
docker compose up
```

Now we have to add a server again. To persist pgAdmin configuration, update docker compose by adding volume mapping to pgadmin service and the volumes section at the very end:

```bash
services:
  pgdatabase:
    image: postgres:13
    environment:
      - POSTGRES_USER=root
      - POSTGRES_PASSWORD=root
      - POSTGRES_DB=ny_taxi
    volumes:
      - "./ny_taxi_postgres_data:/var/lib/postgresql/data:rw"
    ports:
      - "5432:5432"
  pgadmin:
    image: dpage/pgadmin4
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@admin.com
      - PGADMIN_DEFAULT_PASSWORD=root
    volumes:
      - "pgadmin_conn_data:/var/lib/pgadmin:rw"
    ports:
      - "8080:80"
    
volumes:
  pgadmin_conn_data:
```

After ingesting the data and subsequently `docker-compose down` and `docker-compose up -d`, I inspected the data and verified that the server persisted.

> [!NOTE]
Not sure why, but the data is gone. Perhaps I removed the container (though I don't remember doing that).

In any case, to ingest the data again:

```ps
set URL_taxi="http://192.168.137.1:8000/output.csv"
```

```ps
set URL_lookup="http://192.168.137.1:8000/taxi_zone_lookup.csv"
```

```ps
docker run -it ^
    --network=data-engineering-course_default ^
    taxi_ingest:v001 ^
        --user=root ^
        --password=root ^
        --host=pgdatabase ^
        --port=5432 ^
        --db=ny_taxi ^
        --yellow_taxi_table_name=yellow_taxi_trips ^
        --yellow_taxi_url=%URL_taxi% ^
        --zones_table_name=zones ^
        --zones_url=%URL_lookup%
```

After ingesting the data and subsequently `docker-compose down` and `docker-compose up`, I inspected the data and verified that the data persisted.

## [DE Zoomcamp 1.2.6 - SQL Refresher](https://youtu.be/QEcps_iskgg?si=6NYcKjcoTl9uoOtt)

It was not explained in the last video, but you also have to upload the taxi zones csv file. I found a script on the Github repository of the course. But it uses `wget`. I asked ChatGPT to change it to `requests` library. I got it to work and uploaded the data to the database.

Below you can see an Inner join (always a match between tables).
What happens is:
- We `SELECT` some columns
- `FROM` 3 tables (actually the latter two are the same, but these are appended. I believe this happens as a Cartesian product). The 3 tables get aliases.
- We filter with the `WHERE` condition (this is effectively an Inner join, i.e. there is always a match)
- We `LIMIT` the results to the first 100 rows only.

```postgresql
SELECT
	t.tpep_pickup_datetime,
	t.tpep_dropoff_datetime,
	t.total_amount,
	CONCAT(zpu.borough, ' / ', zpu.zone) AS "pick_up_loc",
	CONCAT(zdo.borough, ' / ', zdo.zone) AS "do_up_loc"
FROM 
	yellow_taxi_trips t,
	zones zpu,
	zones zdo
WHERE
	t.pulocationid = zpu.locationid AND
	t.dolocationid = zdo.locationid
LIMIT
    100;
```

### JOIN

An alternative formulation of this with `JOIN` instead of `WHERE`:

```postgresql
SELECT
	t.tpep_pickup_datetime,
	t.tpep_dropoff_datetime,
	t.total_amount,
	CONCAT(zpu.borough, ' / ', zpu.zone) AS "pick_up_loc",
	CONCAT(zdo.borough, ' / ', zdo.zone) AS "do_up_loc"
FROM 
	yellow_taxi_trips t 
JOIN zones zpu 
  ON t.pulocationid = zpu.locationid
JOIN zones zdo
  ON t.dolocationid = zdo.locationid
LIMIT 100;
```

Let's check for records which are missing a Location ID:

```sql
SELECT
	t.tpep_pickup_datetime,
	t.tpep_dropoff_datetime,
	t.total_amount,
	pulocationid,
	dolocationid
FROM 
	yellow_taxi_trips t
WHERE
	pulocationid IS NULL
LIMIT 100;
```

```sql
SELECT
	t.tpep_pickup_datetime,
	t.tpep_dropoff_datetime,
	t.total_amount,
	pulocationid,
	dolocationid
FROM 
	yellow_taxi_trips t
WHERE
	dolocationid IS NULL
LIMIT 100;
```

There is one record which is missing pickup and dropoff location information.

Are there any records in the `yellow_taxi_trips` table that are not in the `zones` table?

```postgresql
SELECT
	*
FROM
	yellow_taxi_trips t
WHERE
	pulocationid NOT IN (SELECT locationid FROM zones)
LIMIT 100;
```

```postgresql
SELECT
	*
FROM 
	yellow_taxi_trips t
WHERE
	dolocationid NOT IN (SELECT locationid FROM zones)
LIMIT 100;
```

There are no such records. Let's create such a case.

First find `pulocationid` of the first row from `yellow_taxi_trips`.

```sql
SELECT *
FROM yellow_taxi_trips
LIMIT 100;
```

It is 97. Now let's delete it.

```sql
DELETE FROM zones WHERE locationid = 97;
```

Now we find many such missing records.

Next, let's do a left join:

```postgresql
SELECT
	t.tpep_pickup_datetime,
	t.tpep_dropoff_datetime,
	t.total_amount,
	CONCAT(zpu.borough, ' / ', zpu.zone) AS "pick_up_loc",
	CONCAT(zdo.borough, ' / ', zdo.zone) AS "do_up_loc"
FROM 
	yellow_taxi_trips t 
LEFT JOIN zones zpu 
  ON t.pulocationid = zpu.locationid
LEFT JOIN zones zdo
  ON t.dolocationid = zdo.locationid
WHERE t.dolocationid = 97 OR t.pulocationid = 97 
LIMIT 100;
```

This shows all records on the left, that may or may not have records on the right.

There is also `RIGHT JOIN`, which is the opposite.

There is also `OUTER JOIN`, which is either one.

### GROUPBY

Let's look at number of trips per day.

Below two options are shown to get the day:

```postgresql
SELECT
	CAST(tpep_dropoff_datetime AS DATE),
	t.total_amount
FROM 
	yellow_taxi_trips t
LIMIT 100;
```

We will go for the second one using `CAST`.

Now we can use `GROUP BY`:

```postgresql
SELECT
	CAST(tpep_dropoff_datetime AS DATE) as "day",
	COUNT(1)
FROM
	yellow_taxi_trips t
GROUP BY
	"day"
ORDER BY "day" ASC;
```

What is the day with the highest number of trips?

```postgresql
SELECT
	CAST(tpep_dropoff_datetime AS DATE) as "day",
	COUNT(1),
    MAX(total_amount)
FROM
	yellow_taxi_trips t
GROUP BY
	"day"
ORDER BY "count" DESC
LIMIT 1;
```

What is the highest amount paid on the day with the highest  number of trips?

```postgresql
SELECT
	CAST(tpep_dropoff_datetime AS DATE) as "day",
	COUNT(1),
    MAX(total_amount)
FROM
	yellow_taxi_trips t
GROUP BY
	"day"
ORDER BY "count" DESC
LIMIT 1;
```

We can also group by multiple columns.

```postgresql
SELECT
	CAST(tpep_dropoff_datetime AS DATE) as "day",
	dolocationid,
	COUNT(1),
    MAX(total_amount)
FROM
	yellow_taxi_trips t
GROUP BY
	1, 2
ORDER BY "day" ASC, "dolocationid" ASC;
```

## [DE Zoomcamp 1.3.1 - Terraform Primer](https://youtu.be/s2bOYDCKl_M?si=xOYCfHjJrBU-BYWo)

### What is Terraform?
Software by Hashicorp that:
- Sets up infrastructure on cloud or on-premise resources
- Infrastructure is set up with code
- It uses human-readable configuration files that can be versioned, reused, shared

### Why use Terraform?
- Simplicity in keeping track of infrastructure
- Collaboration
- Reproducibility
- Ensure resources are removed (important to avoid unnecessary charges)

### How does Terraform work?
- You have your local machine with Terraform installed
- You get a provider which allows you to communicate with a resource such as a cloud platform (e.g. GCP, AWS, Azure)
- A provider can be pulled from Terraform (like a Docker image from Docker Hub?). There are many, such as AWS, Azure, GCP, Kubernetes, VSphere, Alibaba Cloud, Oracle Cloud Infrastructure

### Key Terraform Commands
- `init`: once you define your provider, `init` downloads the corresponding code to your local machine
- `plan`: once you defined some resources, `plan` shows you what its about to do, i.e. show resources that are about to be created
- `apply`: does what is in the .tf files, build that infrastructure
- `destroy`: brings down all the resources that are in your .tf files.


## [DE Zoomcamp 1.3.2 - Terraform Basics](https://youtu.be/Y2ux7gq3Z0o?si=tXSVjlOAr-iRntRs)

First need to set up a Google Cloud Platform (GCP) account.

Then set up Service Account (explained in video).

Then download Terraform binary and add to Path variable (asked ChatGPT).

Search for `Terraform Google Provider` and `Terraform Google Storage Bucket` and take code snippets:

```
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.38.0"
    }
  }
}

provider "google" {
  credentials = "./keys/my-creds.json"
  project     = "dtc-de-course-430705"
  region      = "us-central1"
}

resource "google_storage_bucket" "demo-bucket" {
  name          = "dtc-de-course-430705-terra-bucket"
  location      = "US"
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}
```

Now to `terraform init` and it will initialize.

Then do `terraform plan` to see what Terraform plans to create in terms of resources.

Then do `terraform apply`. Confirm bucket was created on GCP.

Finally use `terraform destroy`. Confirm bucket was deleted on GCP.

[Terraform .gitignore file](https://github.com/github/gitignore/blob/main/Terraform.gitignore) 

## [DE Zoomcamp 1.3.3 - Terraform Variables](https://youtu.be/PBi0hHjLftk?si=yekeJcir_sMAnAaB)

We will create a Bigquery dataset via Terraform. Google `Terraform Bigquery Dataset` and take small code snippet:

```
resource "google_bigquery_dataset" "demo_dataset" {
  dataset_id = "demo_dataset"
}
```

Add to `main.tf`. Now if we do `terraform plan`, we can see information on Bigquery. Now we can `terraform apply`.

> [!NOTE]
I needed to enable BigQuery manually. Not sure why it wasn't already enabled.

After `terraform apply` confirmed that indeed `demo_dataset` is created.

Now do `terraform destroy`.

You do not need to put everything in your `main.tf` file. Instead you can have a separate file with your variables defined there. Here is an example:

`main.tf`

```
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.38.0"
    }
  }
}

provider "google" {
  credentials = file(var.credentials)
  project     = var.project
  region      = var.region
}

resource "google_storage_bucket" "demo-bucket" {
  name          = var.gcs_bucket_name
  location      = var.location
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}

resource "google_bigquery_dataset" "demo_dataset" {
  dataset_id = var.bq_dataset_name
  location = var.location
}
```


`variables.tf`

```
variable "credentials" {
    description = "My Credentials"
    default = "./keys/my-creds.json"
}

variable "project" {
    description = "Project Description"
    default = "dtc-de-course-430705"
}

variable "region" {
    description = "Region"
    default = "us-central1"
}

variable "location" {
    description = "Project Location"
    default = "US"
}

variable "bq_dataset_name" {
    description = "My BigQuery Dataset Name"
    default = "demo_dataset"
}

variable "gcs_bucket_name" {
    description = "My Storage Bucket Name"
    default = "dtc-de-course-430705-terra-bucket"
}

variable "gcs_storage_class" {
  description = "Bucket Storage Class"
  default = "STANDARD"
}
```

The variables in `variables.tf` can be accessed in `main.tf`.




## [DE Zoomcamp 1.4.1 - Setting up the Environment on Google Cloud (Cloud VM + SSH access)](https://youtu.be/ae-CV2KfoN0?si=vZfDz6CfuEa3aQ7i)

> [!NOTE]
From here on out I will work with Windows Subsystem for Linux. I might need to redo some of the steps from before in setting up Docker, but it's probably worth it. 

The goal for this section is to familiarize myself with Google Cloud Platform. This is a key skill if I want to build things and if I'm looking for a Data Engineering role.

### Generate SSH Key

I already have an SSH key, but here's how to do it (described in [GCP docs: create-ssh-keys](https://cloud.google.com/compute/docs/connect/create-ssh-keys)):

```bash
ssh-keygen -t rsa ~/.ssh/gcp -C kdahha -b 2048
```

This will generate two keys in your `.ssh` folder: a public key `gcp.pub` and a private key `gcp`.

### Add SSH key to GCP Compute Engine

Now go to GCP Compute Engine > Settings > Metadata > SSH Keys > Add SSH Key.

In the command line use the command `cat ~/.ssh/gcp.pub` to print your public key. Copy that into GCP and save.

Note that all VMs will use this key.

### .ssh config file

Go to `.ssh` folder and create file named config: ```touch config```.

Open with text editor and add following:
```
Host de-zoomcamp
    HostName [external ip]
    User [ssh user name]
    IdentityFile ~/.ssh/[gcp]
```

Now instead of using this command:

```
ssh -i ~/.ssh/gcp [user name belonging to SSH key]@[IP]
```

We can use:

```bash
ssh de-zoomcamp
```

Note that if the VM instance is stopped and resumed, the external IP will change and this will no longer work.

### Create VM Instance

> [!Note]
This is only needed if you cannot set up a local environment. Although not necessary for me, I went through this section to learn about this anyway and to reinforce the things I learned so far while I was setting up locally.

We can create a VM instance (specify name, region, OS as Ubuntu, certain specs). Then there will be an external IP shown. We can now SSH into this VM with:

```ps
ssh -i ~/.ssh/gcp [user name belonging to SSH key]@[IP]
```

### How to connect to VM via SSH using VS Code

In VS Code you can press `CTRL`+`SHIFT`+`P` which will open the command palette.
Then you can type `Remote-SSH: Connect to Host`. There the host from the SSH config file should be visible. If you click it, it will open a new VS Code window with an SSH connection to the VM.

Note that in my case, I set up my GCP SSH key and config file in WSL. If you open VS Code with WSL and try to connect to the VM, it will give an error. Windows cannot interpret the IdentityFile path from the config file which is `~/.ssh/gcp`. As a workaround, copy `gcp` and `gcp.pub` to the .ssh folder on Windows. Also add the host to the config as follows:

```bash
Host de-zoomcamp
    HostName 34.90.68.192
    User kdahha
    IdentityFile C:/Users/kfdah/.ssh/gcp
```

### Clone DE Zoomcamp Repository

Close the repository:
```bash
git clone https://github.com/DataTalksClub/data-engineering-zoomcamp.git
```

### Anaconda

We will download Anaconda:

```bash
wget https://repo.anaconda.com/archive/Anaconda3-2024.06-1-Linux-x86_64.sh
bash Anaconda3-2024.06-1-Linux-x86_64.sh
```

This installs Anaconda. If it is not added to the path then run:

```bash
~/anaconda3/bin/conda init
```

You can check in .bashrc at the end that there is something added for Anaconda:

```bash
less .bashrc
```

Moreover you can now run `conda --version` and `which python` and you should see `(base)` prepended to your prompt. You may need to log out and log in, but you can also do `source .bashrc`.

### Docker

Now install Docker:

```bash
sudo apt-get update
sudo apt-get install docker.io
```

The first one updates the list of packages for apt-get, the second actually installs Docker.

Check that install is succesful by `docker --version`.

Run hello world:

```bash
docker run hello-world
```

This gives the output:

```
docker: permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock: Post "http://%2Fvar%2Frun%2Fdocker.sock/v1.24/containers/create": dial unix /var/run/docker.sock: connect: permission denied.
See 'docker run --help'.
```

From https://github.com/sindresorhus/guides/blob/main/docker-without-sudo.md:

```bash
sudo groupadd docker
sudo gpasswd -a $USER docker
sudo service docker restart
```

Then log out (`CTRL`+`D`) and log back in (`ssh de-zoomcamp`).

Now try hello world again:

```bash
docker run hello-world
```

Now pull and run Ubuntu image in interactive mode in bash:

```bash
docker run -it ubuntu bash
```

### Docker-Compose

Create bin directory with mkdir.

Download docker-compose from its GH repo:

```bash
wget https://github.com/docker/compose/releases/download/v2.29.1/docker-compose-linux-x86_64 -O bin/docker-compose
```

Use `ls` to check color of file. At first it's white. This means it is not an executable. Need to change it to executable (green):

```bash
chmod +x docker-compose
```

We can check version:

```bash
./docker-compose version

Docker Compose version v2.29.1
```

Let's add it to the `PATH` variable so we can access it from anywhere:

Use vim to open `~/.bashrc` and add following line to prepend to `PATH`:

```bash
export PATH="${HOME}/bin:${PATH}"
```

You can do `source .bashrc` to reload .bashrc file.

To verify it worked, do `which docker-compose` or `docker-compose version`.

Now navigate to: `~/data-engineering-zoomcamp/01-docker-terraform/2_docker_sql` 

Run docker-compose:

```bash
docker-compose up -d
```

This will run the Dockerfile to pull and run postgres and pgadmin container.

Run following to view active containers:

```bash
docker ps
```

### pgcli

```bash
pip install pgcli
```

Now we can run pgcli:

```bash
 pgcli -h localhost -U root -d ny_taxi
 ```

This works fine. I also followed the instructions to download via Conda-Forge, but actually that did not work. Had to follow these steps to fix it:

1. pip uninstall psycopg2
2. pip uninstall pgcli
3. conda remove pgcli
4. pip install pgcli
check with "pgcli -h localhost -U root -d ny_taxi"(without double quotes obvs)
if it generates error no module named 'pgspecial' or something like this then
5. pip install --force-reinstall pgcli
Now recheck with "pgcli -h localhost -U root -d ny_taxi"(without double quotes obvs) should be running now. 

### Setup port forwarding to local machine

Open VS Code, SSH into GCP VM de-zoomcamp, go to Ports, forward 8080 and 5432.

The you can use:

```bash
 pgcli -h localhost -U root -d ny_taxi
 ```

And you can also go to pgadmin via browser:
```bash
localhost:8080
```

> [!NOTE]
I could not get port forwarding to work on WSL2.
Maybe this is not needed though and a connection from Windows is good enough.
However not sure what the added value is in the first place over simply SSH'ing into the VM from VS Code to run pgcli.

### How to open Jupyter

cd to `2_docker_sql` directory and run `jupyter notebook`. Add the port (8888) to VS Code. Then click the link in the terminal.

### Terraform

First we download Terraform (binary) on the GCP VM into bin folder (which is already in our Path variable). Use `unzip` to unzip it and `rm` to remove zipped file. After installing, check that it worked with `terraform version`.

Use `mkdir ~./.gc` to create a folder that will hold GCP credentials. Use `sftp` from local machine to upload `my-creds.json` which we set up during Zoomcamp 1.3.2 to GCP. Create and navigate to `.gc` on GCP and use `put my-creds.json`.

Then input: 

```bash
export GOOGLE_APPLICATION_CREDENTIALS=~/.gc/my-creds.json
gcloud auth activate-service-account --key-file $GOOGLE_APPLICATION_CREDENTIALS
```

The command `export GOOGLE_APPLICATION_CREDENTIALS=~/.gc/my-creds.json` sets the environment variable that points to your Google Cloud service account credentials file, while `gcloud auth activate-service-account --key-file $GOOGLE_APPLICATION_CREDENTIALS` uses that file to authenticate your session, allowing Terraform and other tools to interact with Google Cloud resources securely.

Now `cd` into `1_terraform_gcp/terraform_with_variables`. Update in variables.tf: project id (needs to match the one from GCP). Update main.tf as below (this assigns random bucket name and id which is a requirement by GCP).

```
resource "random_id" "bucket_id" {
  byte_length = 4
}

resource "google_storage_bucket" "demo_bucket" {
  name     = "${var.gcs_bucket_name}-${random_id.bucket_id.hex}"
  location = "US"
  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}
```

Now do:
`terraform init`, `terraform plan`, `terraform apply`, and, finally, `terraform destroy`.


## [DE Zoomcamp 1.4.2 - Using Github Codespaces for the Course (by Luis Oliveira)](https://youtu.be/XOSUt8Ih3zA?si=hwYxC6643OM7Rqwe)

Walkthrough of how to set up Github Codespaces. Not of interest to me, I'll work either locally or on a VM.

## [DE Zoomcamp 1.5.1 - Port Mapping and Networks in Docker (Bonus)](https://youtu.be/tOr4hTsHOzU?si=ccwn_HBFcqZhO0N4)

Say you are running 2 containers on a VM. You can map a port used by the application in the container (e.g. Postgres uses 5432, pgAdmin uses 8080) to a port on the VM. Typically you would map it to the same port if available, otherwise you can pick another port that is free. This could happen for instance if you are running Postgres on the VM without Docker. It will occupy port 5432. Then if you want to run Postgres via a Docker container, that port will be unavailable for the port mapping. In this case, you could opt for port 5431 for instance.

![schematic](images/image.png)