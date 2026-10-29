#Pipeline that collects future data from the Air Quality Network API and stores it in a database.
import duckdb
import requests
from pathlib import Path
import calendar
import pandas as pd
import json
from datetime import date, timedelta

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


def fetch_data(active_sites):
    #Fetch data from the Air Quality Network API, run for each active site for the current month.
    base_url = "https://api.erg.ic.ac.uk/AirQuality"

    #Establish the dates which would be the current month from first of the month to yesterday
    today = date.today()
    yesterday = today - timedelta(days=1)

    start = date(yesterday.year, yesterday.month, 1).isoformat()
    end = today.isoformat()

    #Create the month folder if not already there, 02d always ensures the month is displayed as two digit
    folderloc = Path("data/api-data/raw") / f"{yesterday.year}-{yesterday.month:02d}"
    folderloc.mkdir(parents=True, exist_ok=True)

    #Using active_sites, fetch data for each site for the current month. If folder doesn't exist, it will be created (marking first of that month)
    for code in active_sites:
        second_url = (f"{base_url}/Data/Site/SiteCode={code}/StartDate={start}/EndDate={end}/Json")

        try:
            response = requests.get(second_url, timeout=120)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Failed: {code}, {start} to {end}: {e}")
            continue

        #Save the API response as JSON with the file name corresponding to the SiteCode
        filepath = folderloc / f"{code}.json"
        filepath.write_bytes(response.content)
        print(f"Saved {filepath}")
    return

def transform_data(active_sites):
    #Get the list of JSON files for the current month
    #Transform the raw JSON files into a structured format suitable for loading into the database
    
    #Map site codes to site names for easier reference
    site_names = {site['@SiteCode']: site['@SiteName'] for site in active_sites.values()}

    #Records will hold the extracted data from all JSON files
    records = []

    yesterday = date.today() - timedelta(days=1)
    month_folder = Path("data/api-data/raw") / f"{yesterday.year}-{yesterday.month:02d}"

    #Iterate over each JSON file and extract the relevant data into the records list
    for filepath in month_folder.glob("*.json"):
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

    #Drop duplicate rows based on site_code, timestamp, species, and measurement
    df = df.drop_duplicates(subset=["site_code", "timestamp", "species", "measurement"])
    
    #Engineer the following columns: available, date, site_expected_daily, site_available_daily, site_reliability_daily, species_expected_daily, species_available_daily, species_reliability_daily
    #Available column is a 0/False if measurement is missing and 1/True if measurement is present
    df["available"] = df["measurement"].notna()
    #Date is the date without time, for example 2026-01-27 10:00:00	becomes 2026-01-27
    df["date"] = df["timestamp"].dt.date

    #df should only include records from the start of the current month up to yesterday
    df = df[(df["date"] >= date(yesterday.year, yesterday.month, 1)) & (df["date"] <= yesterday)].copy()
    
    if df.empty:
        print("No records for yesterday, nothing to load.")
        return df

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
    
    print(df.head(10))
    
    return df

def load_data(df):
    #Load the tranformed df to DuckDB, connect to air_quality.db in data/db
    conn = duckdb.connect(database='data/db/air_quality.db')
    #Register df as a table, making it available for SQL queries
    conn.register("historical_df", df)

    #Insert only unique sites into the site table (No duplicates)
    conn.execute('''
        INSERT INTO sites (site_code, site_name)
        SELECT DISTINCT site_code, site_name
        FROM historical_df AS df
        ON CONFLICT (site_code) DO NOTHING
    ''')

    max_id_before = conn.execute("SELECT COALESCE(MAX(id), 0) FROM measurements").fetchone()[0]

    #Insert measurements into the measurements table, linking to the correct site_id on the sites table
    #Insert new rows only, avoiding duplicates based on site_id and timestamp
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
        -- Join with the sites table to get the site_id for each record
        JOIN sites AS s ON s.site_code = df.site_code

        -- Exclude records that already exist in the measurements table with the same site_id, timestamp, species, and measurement
        WHERE NOT EXISTS (
        SELECT 1
        FROM measurements AS m
        WHERE m.site_id = s.id
        AND m.timestamp = df.timestamp
        AND m.species = df.species
        -- Compare measurement as REAL to handle potential type differences
        AND m.measurement IS NOT DISTINCT FROM CAST(df.measurement AS REAL)
        )

        ON CONFLICT (site_id, timestamp, species, measurement) DO NOTHING
    ''')

    new_rows = conn.execute("SELECT * FROM measurements WHERE id > ?", [max_id_before]).df()
    print(f"Rows in current month's data: {len(df)}")
    print(f"New rows added to the database: {len(new_rows)}")
    print(f"Duplicates skipped: {len(df) - len(new_rows)}")
    print(new_rows[['site_id', 'timestamp', 'species', 'measurement']])
    
    conn.close()
    print("Historical data loaded successfully.")
    
    return

def main():
    #Main function to run the data pipeline
    active_sites = fetch_sites()
    fetch_data(active_sites)
    df = transform_data(active_sites)
    load_data(df)

if __name__ == "__main__":
    main()