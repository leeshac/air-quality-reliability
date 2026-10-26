#TODO
#Pipeline that collects the historical data from the Air Quality Network API and stores it in a database.

import requests
import pandas as pd
import calendar
from datetime import date
from pathlib import Path

def fetch_sites():
    #Get site codes from the API
    base_url = "https://api.erg.ic.ac.uk/AirQuality"
    url = (f"{base_url}/Information/MonitoringSites/GroupName=London/Json")
    
    response = requests.get(url, timeout=10)
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

    for a in active_sites:
        print(f"Fetching Site {code}")
        code = active_sites[a]['@SiteCode']

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
            response = requests.get(second_url, timeout=10)
            response.raise_for_status()

            #Create the month folder if not already there, 02d always ensures the month is diplayed as two digit.
            folderloc = Path("data/api-data/raw") / f"{year}-{month:02d}"
            folderloc.mkdir(parents=True, exist_ok=True)

            #Save the API response as JSON with the file name corresponding to the SiteCode
            filepath = folderloc / f"{code}.json"
            filepath.write_bytes(response.content)
            print(f"Saved {filepath}")
    return

def load_historical_data():
    #TODO
    #Load historical data into the database

    #Read every file in data/api-data/raw
    #For each file: rename columns, drop unwanted columns, set types and keep nulls
    #Engineer the following columns: available, date, site_expected_daily, site_available_daily, site_reliability_daily, species_expected_daily, species_available_daily, species_reliability_daily

    return

def main():

    active_sites = fetch_sites()
    fetch_historical_data(active_sites)

    #TODO
    load_historical_data()

if __name__ == "__main__":
    main()