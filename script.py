import streamlit as st
import folium
import requests
from streamlit_folium import st_folium
import pandas as pd
from shapely.geometry import shape

st.set_page_config(page_title="Rajasthan District Map", layout="wide")


uploaded_file = st.sidebar.file_uploader("Upload a CSV file", type="csv")


# Center of Rajasthan
rajasthan_center = [27.0238, 74.2179]

# Create Folium map
m = folium.Map(location=rajasthan_center, zoom_start=7)

# Load GeoJSON of Rajasthan districts
geojson_url = "https://raw.githubusercontent.com/datta07/INDIAN-SHAPEFILES/master/STATES/RAJASTHAN/RAJASTHAN_DISTRICTS.geojson"


@st.cache_data
def load_geojson(url):
    return requests.get(url).json()


geojson_data = load_geojson(geojson_url)


# Add districts to the map
folium.GeoJson(
    geojson_data,
    name="Districts",
    style_function=lambda x: {
        "fillColor": "orange",
        "color": "black",
        "weight": 1,
        "fillOpacity": 0.4,
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["dtname"], aliases=["District:"]
    ),
).add_to(m)


try:

    if uploaded_file is not None:
        dfo = pd.read_csv(uploaded_file)
        # Proceed with filtering and mapping

        districts_list = dfo['District'].unique().tolist()
        options = st.sidebar.multiselect(
            "Please Select District", districts_list)

        df = dfo[dfo["District"].isin(options)]

        for _, row in df.iterrows():
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=f"<b>{row['Branch_Name']}</b><br>{row['Sol ID']} <br>{row['Block_Name']}",
                tooltip=row['Branch_Name']
            ).add_to(m)

        # Function to find bounds of selected district(s)

        def get_bounds_for_districts(geojson_data, options):
            bounds = []
            for feature in geojson_data['features']:
                district_name = feature['properties']['dtname']
                if district_name in options:
                    # Convert to shapely geometry
                    geom = shape(feature['geometry'])
                    # Add bounds (minx, miny, maxx, maxy)
                    bounds.extend(geom.bounds)
            if bounds:
                minx = min(bounds[::4])
                miny = min(bounds[1::4])
                maxx = max(bounds[2::4])
                maxy = max(bounds[3::4])
                return [[miny, minx], [maxy, maxx]]
            return None

        # Zoom the map to the bounds of the selected district(s)
        if options:
            bounds = get_bounds_for_districts(geojson_data, options)
            if bounds:
                m.fit_bounds(bounds)

except FileNotFoundError:
    st.warning("CSV file 'locations.csv' not found. Place it in the same folder.")


# Display map in Streamlit
st_data = st_folium(m, width=900, height=800)
