#TODO
#This script would be run daily, generating the predictions for site reliability based on the latest measurements in the database

import datetime
import pandas as pd
import duckdb

def fetch_latest_data():
    #Fetch the last 8 days of data from duckdb database
    folderloc = "data/db"
    today = datetime.date.today()

    #Define the start and end dates for the last 8 days of data
    start_date = today - datetime.timedelta(days=8)
    end_date = today - datetime.timedelta(days=1)

    conn = duckdb.connect(f'{folderloc}/air_quality.db')

    #Fetch the latest data for the last 8 days from the measurements table
    latest_df = conn.execute(f"""
    SELECT *
    FROM measurements
    WHERE date >= '{start_date}' AND date <= '{end_date}'
    """).fetchdf()

    return latest_df

def transform_data(data):
    pass

def forecast_day(data):
    pass

def forecast_week(data):
    pass

def load_data(data):
    pass

def main():
    data = fetch_latest_data()
    transformed_data = transform_data(data)
    day_forecast = forecast_day(transformed_data)
    week_forecast = forecast_week(transformed_data)
    load_data(day_forecast)
    load_data(week_forecast)

if __name__ == "__main__":
    main()