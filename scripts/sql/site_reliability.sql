SELECT
s.id AS site_id,
s.site_name,
-- Get the maximum site reliability for each site
MAX(m.site_reliability_daily) AS site_reliability_daily
FROM measurements m
JOIN sites s ON m.site_id = s.id
-- Only include measurements from the previous day
WHERE m.date = CURRENT_DATE - INTERVAL '1 day'
-- Group rows by site id and site name
GROUP BY s.id, s.site_name
-- Order from highest to lowest site reliability
ORDER BY site_reliability_daily DESC;