#TODO
#Pipeline that collects the historical data from the Air Quality Network API and stores it in a database.

from urllib import response

import requests
import pandas as pd
import calendar
from datetime import date
from pathlib import Path
import duckdb
import json

def fetch_sites():
    #Get site codes from the API
    base_url = "https://api.erg.ic.ac.uk/AirQuality"
    url = (f"{base_url}/Information/MonitoringSites/GroupName=London/Json")
    
    response = requests.get(url, timeout=120)
    sites_data = response.json()

    #From sites_data, only keep the sites that are still active, i.e. where '@DateClosed' is an empty field.
    active_sites = {}

    for site in sites_data['Sites']['Site']:
        if site['@DateClosed'] == '':
            active_sites[site['@SiteCode']] = site
    return active_sites


def fetch_historical_data(active_sites):
    #For each site, fetch the historical data starting from january 2026 and stopping at september 2026.
    #Do this in batches of one month at a time, save the data in its raw form in data/api-data/raw/2026-01 [etc for each month].
    #Save with the site code as the filename, e.g. data/api-data/raw/2026-01/TH1.json for site TH1 in january 2026.
    #Once one site has been collected from january to september 2026, move on to the next site, starting again from january 2026.
    base_url = "https://api.erg.ic.ac.uk/AirQuality"
    resume = False

    for a in active_sites:
        code = active_sites[a]['@SiteCode']

        if code == "AZ99":
            resume = True

        if not resume:
            print(f"Skipping Site {code}")
            continue
        
        print(f"Fetching Site {code}")

        for month in range(1,10):
            year = 2026

            #Defining the start date
            start = date(year, month, 1)

            #Defining the end date
            last_day = calendar.monthrange(year, month)[1]
            end = date(year, month, last_day)

            #Change format to YYYY-MM-DD
            start = start.isoformat()
            end = end.isoformat()

            second_url = (f"{base_url}/Data/Site/SiteCode={code}/StartDate={start}/EndDate={end}/Json")
            
            try:
                response = requests.get(second_url, timeout=120)
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print(f"Failed: {code}, {start} to {end}: {e}")
                continue

            #Create the month folder if not already there, 02d always ensures the month is diplayed as two digit.
            folderloc = Path("data/api-data/raw") / f"{year}-{month:02d}"
            folderloc.mkdir(parents=True, exist_ok=True)

            #Save the API response as JSON with the file name corresponding to the SiteCode
            filepath = folderloc / f"{code}.json"
            filepath.write_bytes(response.content)
            print(f"Saved {filepath}")
    return

def transform_historical_data(active_sites):
    #Get every file in data/api-data/raw and for each file, extract the relevant columns, set types and keep nulls.
    
    #Map site codes to site names for later use
    site_names = {site['@SiteCode']: site['@SiteName'] for site in active_sites.values()}

    #Records will hold the extracted data from all JSON files
    records = []

    #Iterate over each JSON file and extract the relevant data into the records list
    for filepath in Path("data/api-data/raw").rglob("*.json"):
        with filepath.open("r", encoding="utf-8") as file:
            response_data = json.load(file)

        #Extract the AirQualityData from the response and get the Data section for processing
        air_quality_data = response_data.get("AirQualityData", {})
        data = air_quality_data.get("Data", [])

        #Makes sure that data is always a list, even if there's only one record
        if isinstance(data, dict):
            data = [data]

        #For each record in the data, get the relevant columns and append to records.
        for record in data:
            records.append({
                "site_code": air_quality_data.get("@SiteCode"),
                "timestamp": record.get("@MeasurementDateGMT"),
                "species": record.get("@SpeciesCode"),
                "measurement": record.get("@Value"),
            })

    #Then combine all the extracted data into a single DataFrame for further processing
    df = pd.DataFrame(records)

    #Set the appropriate data types for the columns
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    #For measurement column, convert to numeric, keep NaN for invalid values
    df["measurement"] = pd.to_numeric(df["measurement"], errors="coerce")
    df["site_code"] = df["site_code"].astype(str)
    df["species"] = df["species"].astype(str)

    #Engineer the following columns: available, date, site_expected_daily, site_available_daily, site_reliability_daily, species_expected_daily, species_available_daily, species_reliability_daily
    #Available column is a 0/False if measurement is missing and 1/True if measurement is present
    df["available"] = df["measurement"].notna()
    #Date is the date without time, for example 2026-01-27 10:00:00	becomes 2026-01-27
    df["date"] = df["timestamp"].dt.date

    #Create a column for site names based on the site_code
    df["site_name"] = df["site_code"].map(site_names)

    #SITE
    #Site expected daily column is the total count of measurements taken on that day for each site, grouping by site and date and counting the number of measurements
    df["site_expected_daily"] = df.groupby(["site_code", "date"])["measurement"].transform("size")

    #Site available daily column is the total count of present measurements for each site on that day, grouping by site and date and summing the available measurements
    df["site_available_daily"] = df.groupby(["site_code", "date"])["available"].transform("sum")

    #Site reliability daily column is the percentage of available measurements out of expected measurements for each site on that day
    df["site_reliability_daily"] = (df["site_available_daily"] / df["site_expected_daily"]) * 100

    #SPECIES
    #Species expected daily column is the total count of measurements taken on that day for each species, grouping by species and date and counting the number of measurements
    df["species_expected_daily"] = df.groupby(["site_code", "species", "date"])["measurement"].transform("size")

    #Species available daily column is the total count of present measurements for each species on that day, grouping by species and date and summing the available measurements
    df["species_available_daily"] = df.groupby(["site_code", "species", "date"])["available"].transform("sum")

    #Species reliability daily column is the percentage of available measurements out of expected measurements for each species on that day
    df["species_reliability_daily"] = (df["species_available_daily"] / df["species_expected_daily"]) * 100

    print(df.head(200))

    return df

def load_historical_data(df):
    #Load the tranformed df to DuckDB, connect to air_quality.db in data/db
    conn = duckdb.connect(database='data/db/air_quality.db')
    #Register df as a table, making it available for SQL queries
    conn.register("historical_df", df)

    #Insert only unique sites into the site table
    conn.execute('''
        INSERT INTO sites (site_code, site_name)
        SELECT DISTINCT site_code, site_name
        FROM historical_df AS df
        ON CONFLICT (site_code) DO NOTHING
    ''')

    #Insert measurements into the measurements table, linking to the correct site_id on the sites table
    conn.execute('''
        INSERT INTO measurements (
            site_id, timestamp, species, measurement, available, date,
            site_expected_daily, site_available_daily, site_reliability_daily,
            species_expected_daily, species_available_daily,
            species_reliability_daily
        )
        SELECT
            s.id, df.timestamp, df.species, df.measurement, df.available,
            df.date, df.site_expected_daily, df.site_available_daily,
            df.site_reliability_daily, df.species_expected_daily,
            df.species_available_daily, df.species_reliability_daily
        FROM historical_df AS df
        JOIN sites AS s ON s.site_code = df.site_code
    ''')

    conn.close()
    print("Historical data loaded successfully.")

    return

def main():

    active_sites = fetch_sites()

    #Commented out fetching historical data as it is already available in data/api-data/raw
    #fetch_historical_data(active_sites)

    df = transform_historical_data(active_sites)
    load_historical_data(df)
    print("Historical data transformation and loading complete.")

if __name__ == "__main__":
    main()