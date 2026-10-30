SELECT
    s.id AS site_id,
    s.site_name,
    f.forecast_made_on,
    f.forecast_tomorrow,
    f.forecast_next_seven_days_mean
FROM sites s
JOIN forecasts f
    ON s.id = f.site_id
ORDER BY s.site_name;