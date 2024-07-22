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
