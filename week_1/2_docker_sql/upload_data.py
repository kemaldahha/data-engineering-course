import pandas as pd
from sqlalchemy import create_engine


engine = create_engine(f"postgresql://root:root@pgdatabase:5432/ny_taxi")

df = pd.read_csv("week_1/2_docker_sql/taxi_zone_lookup.csv")

df.to_sql(name="yellow_taxi_trips", con=engine, if_exists='append')