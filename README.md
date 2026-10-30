# air-quality-reliability

> [!NOTE]
> The DuckDB database file (data/db/air_quality.db) is larger than GitHub's 100 MB limit for a single file, so it is excluded from the repository using .gitignore. The database is maintained locally and can be recreated using the `database.py` and `history_pipeline.py` included in this repository.

### What I built and who for
This is an air quality site reliability dashboard and forecasting pipeline. It informs users how reliable each open monitoring site in London is at reporting measurements and provides a breakdown of reliability for the individual pollutants recorded at each site. The available data is up to date through the end of the previous day.

Alongside this, the pipeline forecasts each site's reliability for the following day and its average reliability across the next seven days. Filters help users navigate the dashboard and investigate the reliability of individual sites and pollutants.

This pipeline would be useful for someone investigating which monitoring sites are more or less reliable when it comes to reporting measurements. If a site returns few or no measurements, this could indicate an issue that warrants further investigation. Users can also explore the pollutant breakdown to investigate whether particular pollutants have lower reporting reliability than others.

The forecasts also help users anticipate how reliable sites are likely to be in the near future. For someone who needs reliable air quality data, this pipeline could help identify the most reliable sites. Equally, someone investigating sites with low reliability could use it to identify potential issues and determine where further investigation may be needed.

### The data
The data is collected from the London Air Quality Network API, which provides air quality measurements from monitoring sites across London. The dataset includes measurements for individual pollutants alongside the site and timestamp associated with each reading.

Historical data is collected to analyse measurement availability and calculate the reliability of each monitoring site. This data is then used to train the models to predict site reliability for the following day and the average reliability across the next seven days.

### How it works
`app.py`: The Streamlit app, featuring a main dashboard with sites listed alongside yesterday's daily measurement reliability, and a side panel that includes a breakdown of the specific pollutants and their reliability within the selected site, alongside the forecasted reliability for tomorrow and the average across the next seven days.

`database.py`: Designed to be run once. Creates the initial database schema, including the tables, columns and foreign keys.

`history_pipeline.py`: Also designed to be run once. Populates the data/api-data folder with historical data up to the end of September for every open site.

`main_pipeline.py`: Designed to run once a day, at the end of each day. Collects the current month's data up to the previous day and adds only new rows to the database, preventing duplicates.

`predictions.py`: Also designed to run once a day, immediately after main_pipeline.py. Updates the forecasts table in the database with newly generated forecasts for every site.

### How to run it
TBA

### What I would do next
I would develop a retraining pipeline for the model, running once a month and retraining it on the latest month of data that was not included in the previous training run. This would allow the model to incorporate newer data over time and help prevent data drift.

I would also add a metric for forecasted reliability over the next month (30 days), as I think this could be an even more telling measure of a site's overall reliability.

### Where AI helped
AI has helped with syntax that I couldn't remember off the top of my head, particularly syntax from libraries I don't use often. It has also helped with debugging by suggesting where to place print statements so I could further investigate unexpected outputs and errors. Additionally, it has helped speed up writing repetitive code.