FROM python:3.12

RUN pip install pandas sqlalchemy pyarrow psycopg2 requests tqdm

WORKDIR /app
COPY ingest_data.py ingest_data.py

ENTRYPOINT [ "python", "ingest_data.py" ]