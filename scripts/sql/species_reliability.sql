SELECT 
site_id,
species,
-- Get the maximum species reliability for each site
MAX(species_reliability_daily) AS species_reliability_daily
FROM measurements
-- Only include measurements from the previous day
WHERE date = CURRENT_DATE - INTERVAL '1 day'
GROUP BY
site_id,
species
ORDER BY species;