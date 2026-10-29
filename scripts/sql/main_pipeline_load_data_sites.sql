-- Insert only unique sites into the site table (No duplicates)
INSERT INTO sites (site_code, site_name)
SELECT DISTINCT site_code, site_name
FROM main_df AS df
ON CONFLICT (site_code) DO NOTHING;