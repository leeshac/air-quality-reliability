#This script would be run daily, generating the predictions for site reliability based on the latest measurements in the database

import datetime
import pandas as pd
import duckdb
from xgboost import XGBRegressor

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

    conn.close()

    print(latest_df.head(10))

    return latest_df

def transform_data(latest_df):
    #Perform transformations on the lastest data

    #Ensure the timestamp and measurement columns are in the correct format
    latest_df["timestamp"] = pd.to_datetime(latest_df["timestamp"])
    latest_df["measurement"] = pd.to_numeric(latest_df["measurement"], errors="coerce")

    #Add a column for the normalised date and availability of measurements
    latest_df["date"] = latest_df["timestamp"].dt.normalize()
    latest_df["available"] = latest_df["measurement"].notna()

    #Combine the data to get the expected and available daily measurements per site
    main_df = (latest_df.groupby(["site_code", "date"], as_index=False).agg(site_expected_daily=("measurement", "size"),
                                                                            site_available_daily=("available", "sum")))


    #Calculate the daily site reliability
    main_df["site_reliability_daily"] = (main_df["site_available_daily"] / main_df["site_expected_daily"]) * 100

    #Sort in order
    main_df = main_df.sort_values(["site_code", "date"]).reset_index(drop=True)

    #site_reliability_lag_1 column: The site's reliability 1 day ago.
    main_df["site_reliability_lag_1"] = main_df.groupby("site_code")["site_reliability_daily"].shift(1)

    #site_reliability_lag_2 column: The site's reliability 2 days ago.
    main_df["site_reliability_lag_2"] = main_df.groupby("site_code")["site_reliability_daily"].shift(2)

    #site_reliability_lag_3 column: The site's reliability 7 days ago.
    main_df["site_reliability_lag_3"] = main_df.groupby("site_code")["site_reliability_daily"].shift(7)

    #site_reliability_mean_7 column: The average daily reliability over the previous 7 days.
    main_df["site_reliability_rolling_mean_7"] = main_df.groupby("site_code")["site_reliability_daily"].transform(lambda s: s.shift(1).rolling(window=7, min_periods=7).mean())

    #Day of the week column
    main_df["day_of_the_week"] = (main_df["date"] + pd.Timedelta(days=2)).dt.dayofweek

    #site_expected_daily_lag_1 column: The total number of measurements expected from that site yesterday.
    main_df["site_expected_daily_lag_1"] = (main_df.groupby("site_code")["site_expected_daily"].shift(1))

    #site_available_daily_lag_1 column: The number of measurements that actually had values available yesterday.
    main_df["site_available_daily_lag_1"] = (main_df.groupby("site_code")["site_available_daily"].shift(1))

    print(main_df.head(10))

    return main_df

def forecast_day(main_df):
    #Forecast the reliability for the next day based on the main_df using XGBoost model
    folderloc = "data/models/current"
    day_model = XGBRegressor()
    day_model.load_model(f"{folderloc}/xgboost_model_forecast_day.json")

    #Define the features and target for the forecast model
    features = ["site_code","day_of_the_week","site_reliability_lag_1",
                "site_reliability_lag_2","site_reliability_lag_3",
                "site_reliability_rolling_mean_7","site_expected_daily_lag_1",
                "site_available_daily_lag_1"]
    target = "target_forecast_day"

    #Create a copy of the main_df so it avoids modifying the original DataFrame
    forecast_df = main_df.copy()

    #Add column for the forecasted target for the next day
    forecast_df["target_forecast_day"] = day_model.predict(forecast_df[features])

    print(forecast_df.head(10))

    return forecast_df

def forecast_week(forecast_df, main_df):
    #Forecast the reliability for the next week based on the main_df using XGBoost model
    folderloc = "data/models/current"
    week_model = XGBRegressor()
    week_model.load_model(f"{folderloc}/xgboost_model_forecast_week.json")

    features = ["site_code","day_of_the_week","site_reliability_lag_1",
                "site_reliability_lag_2","site_reliability_lag_3",
                "site_reliability_rolling_mean_7","site_expected_daily_lag_1",
                "site_available_daily_lag_1"]
    target = "target_forecast_week"

    #Add column for the forecasted target for the next week
    forecast_df["target_forecast_week"] = week_model.predict(forecast_df[features])

    print(forecast_df.head(10))

    return forecast_df

def load_data(forecast_df):
    #Load the forecasted data into the DuckDB forecasts table
    fileloc = 'data/db'
    conn = duckdb.connect(f'{fileloc}/air_quality.db')

    conn.register("forecast_df", forecast_df)

    #Insert the forecasted data into the forecasts table and join with the sites table to get the site_id
    conn.execute('''
        INSERT INTO forecasts (site_id, forecast_made_on, forecast_tomorrow, forecast_next_seven_days_mean)
        SELECT s.id, CURRENT_DATE, forecast_df.target_forecast_day, forecast_df.target_forecast_week
        FROM forecast_df forecast_df
        JOIN sites s ON forecast_df.site_code = s.site_code
    ''')

    #Remove rows that fall before the current date from the forecasts table
    conn.execute('''
        DELETE FROM forecasts
        WHERE forecast_made_on < CURRENT_DATE
    ''')

    conn.close()
    return

def main():
    #Fetch the latest data and transform it for forecasting
    latest_df = fetch_latest_data()
    main_df = transform_data(latest_df)

    #Forecast the reliability for the next day and the next week using the transformed data
    forecast_df = forecast_day(main_df)
    forecast_df = forecast_week(forecast_df, main_df)

    #Load the forecasted data into the DuckDB forecasts table
    load_data(forecast_df)

if __name__ == "__main__":
    main()