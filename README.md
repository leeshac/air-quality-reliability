# air-quality-reliability

> [!NOTE]
> The DuckDB database file (`data/db/air_quality.db`) is larger than GitHub's 100 MB limit for a single file, so it is listed in `.gitignore` for now and will be added to the repository with Git LFS (Large File Storage).

### In progress
- Add XGBoost Notebook
- Add `air_quality.db` database with Git LFS

### What I built and who for
This is an air quality site reliability dashboard and forecasting pipeline. It informs users how reliable each open monitoring site in London is at reporting measurements and provides a breakdown of reliability for the individual pollutants recorded at each site. The available data is up to date through the end of the previous day.

Alongside this, the pipeline forecasts each site's reliability for the following day and its average reliability across the next seven days. Filters help users navigate the dashboard and investigate the reliability of individual sites and pollutants.

This pipeline would be useful for someone investigating which monitoring sites are more or less reliable when it comes to reporting measurements. If a site returns few or no measurements, this could indicate an issue that warrants further investigation. Users can also explore the pollutant breakdown to investigate whether particular pollutants have lower reporting reliability than others.

The forecasts also help users anticipate how reliable sites are likely to be in the near future. For someone who needs reliable air quality data, this pipeline could help identify the most reliable sites. Equally, someone investigating sites with low reliability could use it to identify potential issues and determine where further investigation may be needed.

### The data

### How it works
`database.py`: Designed to be run once. Creates the initial database schema, including the tables, columns and foreign keys.

`history_pipeline.py`: Also designed to be run once. Populates the data/api-data folder with historical data up to the end of September for every open site.

`main_pipeline.py`: Designed to run once a day, at the end of each day. Collects the current month's data up to the previous day and adds only new rows to the database, preventing duplicates.

`predictions.py`: Also designed to run once a day, immediately after main_pipeline.py. Updates the forecasts table in the database with newly generated forecasts for every site.

`app.py`: TBA (Streamlit app)

### How to run it

### What I would do next

### Where AI helped
So far, AI has helped with syntax that I couldn't remember off the top of my head, particularly syntax from libraries I don't use often. It has also helped with debugging by suggesting where to place print statements so I could further investigate unexpected outputs and errors. Additionally, it has helped speed up writing repetitive code.