#TODO
#Pipeline that collects the historical data from the Air Quality Network API and stores it in a database.

import requests
import pandas as pd

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

    pass

def load_historical_data():
    #TODO
    #Load historical data into the database
    pass

def main():
    #TODO
    #Main function to run the historical data pipeline
    active_sites = fetch_sites()
    fetch_historical_data(active_sites)
    load_historical_data()
    