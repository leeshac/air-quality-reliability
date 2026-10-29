-- Insert only unique sites into the site table
INSERT INTO sites (site_code, site_name)
SELECT DISTINCT site_code, site_name
FROM historical_df AS df
ON CONFLICT (site_code) DO NOTHING;

-- Insert measurements into the measurements table, linking to the correct site_id on the sites table
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
    JOIN sites AS s ON s.site_code = df.site_code;