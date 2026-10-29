-- Fetch the latest data for the last 8 days from the measurements table
SELECT s.site_code, m.timestamp, m.measurement
FROM measurements AS m
-- Join with the sites table to get the site code
JOIN sites AS s ON m.site_id = s.id
WHERE m.date >= ? AND m.date <= ?