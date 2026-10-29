-- Remove today's and older forecasts first, so a rerun on the same day replaces today's rows
DELETE FROM forecasts
WHERE forecast_made_on <= CURRENT_DATE;

-- Insert the forecasted data into the forecasts table and join with the sites table to get the site_id
INSERT INTO forecasts (site_id, forecast_made_on, forecast_tomorrow, forecast_next_seven_days_mean)
SELECT s.id, CURRENT_DATE, forecast_df.target_forecast_day, forecast_df.target_forecast_week
FROM forecast_df forecast_df
JOIN sites s ON forecast_df.site_code = s.site_code;