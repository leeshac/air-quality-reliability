#Script to create the database and tables for the application

import duckdb

def create_database():
    #Create the database and tables for the application

    #Establish a connection to the database
    fileloc = 'data/db'
    conn = duckdb.connect(f'{fileloc}/air_quality.db')

    #Create sequences for sites and measurements tables so that the id columns can auto-increment
    conn.execute("CREATE SEQUENCE IF NOT EXISTS sites_id_seq START 1")
    conn.execute("CREATE SEQUENCE IF NOT EXISTS measurements_id_seq START 1")
    conn.execute("CREATE SEQUENCE IF NOT EXISTS forecasts_id_seq START 1")

    #Create the sites table with columns for site_id, site_code and site_name
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY DEFAULT nextval('sites_id_seq'),
            site_code TEXT UNIQUE,
            site_name TEXT
        )
    ''')

    #Create the measurements table with columns for site_id, timestamp, species, 
    #measurement, available, date, site_expected_daily, site_available_daily, 
    #site_reliability_daily, species_expected_daily, species_available_daily, and 
    #species_reliability_daily
    conn.execute('''
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY DEFAULT nextval('measurements_id_seq'),
            site_id INTEGER,
            timestamp TIMESTAMP,
            species TEXT,
            measurement REAL,
            available BOOLEAN,
            date DATE,
            site_expected_daily REAL,
            site_available_daily REAL,
            site_reliability_daily REAL,
            species_expected_daily REAL,
            species_available_daily REAL,
            species_reliability_daily REAL,
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )
    ''')

    #Create a table for storing the forecasts for each site. One column for forecast for tomorrow and one for the average predicted reliability over the next seven days
    #Joined by the site_id to the sites table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS forecasts (
            id INTEGER PRIMARY KEY DEFAULT nextval('forecasts_id_seq'),
            site_id INTEGER,
            forecast_made_on DATE,
            forecast_tomorrow REAL,
            forecast_next_seven_days_mean REAL,
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )
    ''')

    conn.close()

def main():
    create_database()
    print("Database and tables created successfully.")

if __name__ == "__main__":
    main()