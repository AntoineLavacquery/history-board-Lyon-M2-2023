import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from neo4jtools import *
import pandas as pd
import numpy as np
from streamlit_folium import st_folium
from folium.plugins import TimestampedGeoJson


st.markdown("## Test sur données d'exemple")

df = px.data.tips()
fig = px.histogram(df, x="total_bill", color="sex", marginal="box", # can be `box`, `violin`
                         hover_data=df.columns)

df
chart = st.plotly_chart(fig, width=1000, height=500, use_container_width=True)

# Créez une carte de base
m = folium.Map(location=[45.5236, -122.6750], zoom_start=10)

# Données pour TimestampedGeoJson
data = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [-122.6750, 45.5236]
            },
            "properties": {
                "times": ["2023-01-01T00:00:00"],
                "popup": "Information sur le point 1",
                "id": "point1"
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [-122.6650, 45.5136]
            },
            "properties": {
                "times": ["2023-01-02T00:00:00"],
                "popup": "Information sur le point 2",
                "id": "point2"
            }
        }
    ]
}

# Ajoutez TimestampedGeoJson à la carte
timestamped_layer = TimestampedGeoJson(
    data,
    auto_play=False,
    loop=False,
    max_speed=1,
    loop_button=True,
    date_options='YYYY/MM/DD',
    time_slider_drag_update=True
)

timestamped_layer.add_to(m)

# Sauvegardez la carte dans un fichier HTML
m.save('map.html')

st_folium(m, use_container_width=True)