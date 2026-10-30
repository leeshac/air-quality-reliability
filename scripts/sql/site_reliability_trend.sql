-- Get the site reliability trend for the past 30 days: one row per site per day
SELECT
s.id AS site_id,
s.site_name,
m.date,
AVG(m.site_reliability_daily) AS site_reliability
FROM measurements m
JOIN sites s ON m.site_id = s.id

-- Get measurements where the date is larger than or equal to 30 days ago
WHERE m.date >= CURRENT_DATE - INTERVAL '30 days'
-- And where the date is less than today
AND m.date < CURRENT_DATE

-- Group by site and date so we can calculate the average reliability for each site on each day
GROUP BY s.id, s.site_name, m.date
-- Order by date to see the trend over time from oldest to newest
ORDER BY m.date;