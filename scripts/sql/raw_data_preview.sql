-- Display the latest 100 raw measurements along with site info
SELECT
s.site_code,
s.site_name,
m.timestamp,m.species,
    m.measurement,
    m.available
FROM measurements m 
JOIN sites s ON m.site_id = s.id
ORDER BY m.timestamp DESC
LIMIT 100;