#Streamlit application
import streamlit as st
import duckdb
import pandas as pd

st.set_page_config(layout="wide")

st.markdown("""
    <style>
        .block-container {
            max-width: 100%;
            padding-left: 2rem;
            padding-right: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

def get_site_reliability(conn):
    sql = "scripts/sql/site_reliability.sql"

    #Create a dataframe from the SQL query result
    with open(sql, "r") as file:
        site_df = conn.execute(file.read()).df()

    return site_df

def get_species_reliability(conn):
    sql = "scripts/sql/species_reliability.sql"

    #Create a dataframe from the SQL query result
    with open(sql, "r") as file:
        species_df = conn.execute(file.read()).df()

    return species_df

def get_site_reliability_predictions(conn):
    sql = "scripts/sql/site_reliability_predictions.sql"

    #Create a dataframe from the SQL query result
    with open(sql, "r") as file:
        predictions_df = conn.execute(file.read()).df()

    return predictions_df

#Store the currently selected site as Streamlit refreshes each time a user interacts with the app
if 'selected_site' not in st.session_state:
    st.session_state.selected_site = None

#Display site reliability information in the center
st.markdown("<h1 style='text-align: center;'>London Air Quality Site Reliability</h1>",
            unsafe_allow_html=True,
            )

st.markdown("&nbsp;")

conn = duckdb.connect('data/db/air_quality.db')

species_df = get_species_reliability(conn)
site_df = get_site_reliability(conn)
predictions_df = get_site_reliability_predictions(conn)

#Create main dashboard and side panel for site details
main_col, details_col = st.columns([1, 1])

#Main dashboard
with main_col:
    sort_order = st.selectbox("Sort by reliability", ["High to low", "Low to high"])

    #Sort sites by reliability
    if sort_order == "High to low":
        sorted_sites = site_df.sort_values(by="site_reliability_daily", ascending=False)
    else:
        sorted_sites = site_df.sort_values(by="site_reliability_daily", ascending=True)

    #Scrollable container for site list
    with st.container(height=700):

        for _, row in sorted_sites.iterrows():

            site_name = row['site_name']
            reliability = row['site_reliability_daily']

            # Make each site a clickable button
            if st.button(f"{site_name} | {reliability:.0f}%",
                        key=f"site_{row['site_id']}",
                        use_container_width=True
                        ):
                #Mark the selected site in the session state
                st.session_state.selected_site = row['site_id']

#Side panel
with details_col:
    if st.session_state.selected_site is None:
        st.markdown("<div style='text-align: center;'>Site details</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; font-size: smaller;'>Select a site to view its details.</div>", unsafe_allow_html=True)

    else:
        #Get the selected site's information
        selected_site = site_df[site_df['site_id'] == st.session_state.selected_site]

        #Get only the selected site's species
        selected_species = species_df[species_df['site_id'] == st.session_state.selected_site]

        #Get the selected site's reliability predictions
        selected_predictions = predictions_df[predictions_df['site_id'] == st.session_state.selected_site]

        st.markdown(
            f"""<h3 style='font-size: 1.3rem; text-align: center; margin: 0 0 -2rem 0;'>
            {selected_site['site_name'].iloc[0]}</h3>""",
            unsafe_allow_html=True)


        st.divider()

        st.write("Latest observed reliability")

        #Display the previous day's reliability as a metric
        observed = selected_site['site_reliability_daily'].iloc[0]

        left, centre, right = st.columns([2, 2, 1])

        with centre:
            st.metric(label="Previous day", value=f"{observed:.0f}%")

        st.caption("00:00–23:00")

        st.divider()

        #Forecasts
        st.write("Forecasts")

        tomorrow = selected_predictions['forecast_tomorrow'].iloc[0]
        next_seven_days = selected_predictions['forecast_next_seven_days_mean'].iloc[0]

        left, forecast_col1, forecast_col2, right = st.columns([2, 2, 2, 1])

        with forecast_col1:
            st.metric(
                label="Tomorrow",
                value=f"{tomorrow:.0f}%",
                delta=f"{tomorrow - observed:.0f} pp"
            )

        with forecast_col2:
            st.metric(
                label="Next 7 days",
                value=f"{next_seven_days:.0f}%",
                delta=f"{next_seven_days - observed:.0f} pp"
            )

        st.divider()

        st.write("Latest reliability by pollutant")

        for _, species_row in selected_species.iterrows():
            score = species_row['species_reliability_daily']

            if score >= 70:
                colour = "#2E8B57"
                status = "Good"
            elif score >= 50:
                colour = "#E6B800"
                status = "OK"
            else:
                colour = "#FF0000"
                status = "Poor"

            st.write(f"**{species_row['species']}** · {score:.0f}%")


            st.markdown(f"""
            <div style="background-color: #e0e0e0; border-radius: 10px; height: 10px;">
            <div style="
            width: {score}%;
            background-color: {colour};
            height: 10px;
            border-radius: 10px;
            "></div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("&nbsp;")

#Credit to the London Air Quality team for the data
st.markdown("<div style='text-align: center; " \
"font-size: smaller;'>This information has been obtained from the Environmental Research Group " \
"of Imperial College London (https://www.imperial.ac.uk/school-public-health/environmental-research-group/)," \
"using data from the London Air Quality Network (https://www.londonair.org.uk). This information is " \
"licensed under the terms of the Open Government Licence.</div>", unsafe_allow_html=True)