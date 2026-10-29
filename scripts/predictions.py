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
    sql = "scripts/sql/predictions_fetch_latest_data.sql"

    conn = duckdb.connect(f'{folderloc}/air_quality.db')

    with open(sql, "r") as file:
        query = file.read()

    #Fetch the latest data for the last 8 days from the measurements table and join with site information to get the site code
    latest_df = conn.execute(query, [start_date, end_date]).fetchdf()
    
    conn.close()

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

    #Keep only yesterday's row for each site as the earlier days were only needed to calculate the lags
    yesterday = pd.Timestamp(datetime.date.today() - datetime.timedelta(days=1))
    main_df = main_df[main_df["date"] == yesterday].reset_index(drop=True)

    return main_df

def forecast_day(main_df):
    #Forecast the reliability for the next day based on the main_df using XGBoost model
    folderloc = "models/current"
    day_model = XGBRegressor()
    day_model.load_model(f"{folderloc}/xgboost_model_forecast_day.json")

    #Define the features for the forecast model
    features = ["site_code","day_of_the_week","site_reliability_daily","site_reliability_lag_1",
                "site_reliability_lag_2","site_reliability_lag_3",
                "site_reliability_rolling_mean_7","site_expected_daily_lag_1",
                "site_available_daily_lag_1"]

    #Create a copy of the main_df so it avoids modifying the original DataFrame
    forecast_df = main_df.copy()

    #One hot encode site_code, then match the model's training columns exactly
    X = pd.get_dummies(forecast_df[features], columns=["site_code"], dtype=int)
    X = X.reindex(columns=day_model.get_booster().feature_names, fill_value=0)

    #Add column for the forecasted target for the next day
    forecast_df["target_forecast_day"] = day_model.predict(X)

    return forecast_df

def forecast_week(forecast_df, main_df):
    #Forecast the reliability for the next week based on the main_df using XGBoost model
    folderloc = "models/current"
    week_model = XGBRegressor()
    week_model.load_model(f"{folderloc}/xgboost_model_forecast_week.json")

    features = ["site_code","day_of_the_week","site_reliability_daily", "site_reliability_lag_1",
                "site_reliability_lag_2","site_reliability_lag_3",
                "site_reliability_rolling_mean_7","site_expected_daily_lag_1",
                "site_available_daily_lag_1"]

    #One hot encode site_code, then match the model's training columns exactly
    X_week = pd.get_dummies(forecast_df[features], columns=["site_code"], dtype=int)
    X_week = X_week.reindex(columns=week_model.get_booster().feature_names, fill_value=0)

    #Add column for the forecasted target for the next week
    forecast_df["target_forecast_week"] = week_model.predict(X_week)

    print(forecast_df.head(10))

    return forecast_df

def load_data(forecast_df):
    #Load the forecasted data into the DuckDB forecasts table
    fileloc = 'data/db'
    conn = duckdb.connect(f'{fileloc}/air_quality.db')

    conn.register("forecast_df", forecast_df)
    sql = ("scripts/sql/predictions_load_data.sql")

    #Execute the SQL script to delete existing forecasted data and load the new forecasted data into the database
    with open(sql, "r") as file:
        conn.execute(file.read())

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