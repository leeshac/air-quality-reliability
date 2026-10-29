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
    FROM main_df AS df
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