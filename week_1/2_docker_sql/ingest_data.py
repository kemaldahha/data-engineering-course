import argparse
import os
import pandas as pd
from time import time
from sqlalchemy import create_engine
import requests


def download_file(url, filename):
    response = requests.get(url)
    response.raise_for_status()  # Check if the request was successful
    with open(filename, 'wb') as file:
        file.write(response.content)
    print(f"Downloaded {filename} from {url}")


def main(params):
    user = params.user
    password = params.password
    host = params.host
    port = params.port
    db = params.db
    yellow_taxi_table_name = params.yellow_taxi_table_name
    yellow_taxi_url = params.yellow_taxi_url
    zones_table_name = params.zones_table_name
    zones_url = params.zones_url

    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')

    yt_csv_name = 'yt_data.csv'
    download_file(yellow_taxi_url, yt_csv_name)

    zones_csv_name = 'zones.csv'
    download_file(zones_url, zones_csv_name)

    zone_lookup = pd.read_csv(zones_csv_name)
    zone_lookup.columns = [c.lower() for c in zone_lookup.columns]
    zone_lookup.to_sql(name=zones_table_name, con=engine, if_exists='replace')
    print('Inserted zone data')

    df_iter = pd.read_csv(yt_csv_name, iterator=True, chunksize=100_000)
    df = next(df_iter)
    df = df.assign(tpep_pickup_datetime=lambda df_: pd.to_datetime(df_['tpep_pickup_datetime']),
                   tpep_dropoff_datetime=lambda df_: pd.to_datetime(df_['tpep_dropoff_datetime']))

    df.columns = [c.lower() for c in df.columns]

    df.head(0).to_sql(name=yellow_taxi_table_name, con=engine, if_exists='replace')
    df.to_sql(name=yellow_taxi_table_name, con=engine, if_exists='append')

    while True:
        try:
            t_start = time()
            df = next(df_iter)
            df = df.assign(tpep_pickup_datetime=lambda df_: pd.to_datetime(df_['tpep_pickup_datetime']),
                           tpep_dropoff_datetime=lambda df_: pd.to_datetime(df_['tpep_dropoff_datetime']))
            df.columns = [c.lower() for c in df.columns]
            df.to_sql(name=yellow_taxi_table_name, con=engine, if_exists='append')
            t_end = time()

            print(f'Inserted another chunk..., took {t_end - t_start:.2f} seconds')

        except StopIteration:
            print("All chunks inserted.")
            break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Ingest CSV Data to Postgres")
    parser.add_argument('--user', help='username for postgres')
    parser.add_argument('--password', help='password for postgres')
    parser.add_argument('--host', help='host for postgres')
    parser.add_argument('--port', help='port for postgres')
    parser.add_argument('--db', help='database name for postgres')
    parser.add_argument('--yellow_taxi_table_name', help='name of table to write the taxi data to')
    parser.add_argument('--yellow_taxi_url', help='url of the csv file')
    parser.add_argument('--zones_table_name', help='name of table to write the zones to')
    parser.add_argument('--zones_url', help='url of the zones data')

    args = parser.parse_args()

    main(args)
