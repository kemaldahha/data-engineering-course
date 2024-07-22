# Week 1

## 1.1.1 Introduction to Docker

[DE Zoomcamp 1.2.1 - Introduction to Docker](https://youtu.be/EYNwNlOrpr0?si=rw7Z_lDFc1A7Fo36)

Say you have multiple data pipelines chained. Each of them takes some data

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

## 1.2.1 Ingesting NY Taxi Data to Postgres

[DE Zoomcamp 1.2.2 - Ingesting NY Taxi Data to Postgres](https://youtu.be/2JM-ziJt0WI?si=1Mi05VsHPgodbmVn)

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


## 1.2.3 Connecting pgAdmin and Postgres

[DE Zoomcamp 1.2.3 Connecting pgAdmin and Postgres](https://youtu.be/hCAIVe9N0ow?si=NWVSa25g4QeRjzue)

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

## DE Zoomcamp 1.2.4 - Dockerizing the Ingestion Script

[DE Zoomcamp 1.2.4 - Dockerizing the Ingestion Script](https://youtu.be/B1WwATwf-vY?si=-xj66cqaCgP6t1Rf)

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

## DE Zoomcamp 1.2.5 - Running Postgres and pgAdmin with Docker-Compose

[DE Zoomcamp 1.2.5 - Running Postgres and pgAdmin with Docker-Compose](https://youtu.be/hKI6PkPhpa0?si=68EVr2JXH6wkrTZm)

This lesson 

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

Not sure why, but the data is gone. Perhaps I removed the container (though I don't remember doing that).

In any case, to ingest the data again:

```ps
set URL="http://172.26.160.1:8000/temp.parquet"
```

```ps
docker run -it ^
    --network=data-engineering-course_default ^
    taxi_ingest:v001 ^
        --user=root ^
        --password=root ^
        --host=pg-database ^
        --port=5432 ^
        --db=ny_taxi ^
        --table-name=yellow_taxi_trips ^
        --url=%URL%
```

After ingesting the data and subsequently `docker compose down` and `docker compose up`, I inspected the data and verified that the data persisted.

## DE Zoomcamp 1.2.6 - SQL Refresher

[DE Zoomcamp 1.2.6 - SQL Refresher](https://youtu.be/QEcps_iskgg?si=6NYcKjcoTl9uoOtt)

