import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

from neo4jtools import *
from Accueil import page_config_params, make_sidebar_foot

st.set_page_config(**page_config_params)
make_sidebar_foot("https://www.univ-lyon3.fr/medias/photo/udl-lyon3-web_1493035760450-png?ID_FICHE=239744&INLINE=FALSE")

st.markdown("""## Origines sociales""")
query0 = """
MATCH (h:HOMME)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'}), (h)<-[pd:PÈRE_DE]-(p:HOMME)-[:EXERCE]->(pp)
WHERE (e.date_début.year >= 1815 AND e.date_début.year <= 1852)
OR (e.date_fin.year >= 1815 AND e.date_fin.year <= 1852)
RETURN h, p, pp
"""

data = get_neo4j_results_of(query0)

# data

rows = []
for entry in data:
    adc = entry['h']['nom']
    pere = entry['p']['nom']
    pp = entry['pp']['nom']
    rows.append([adc, pere, pp])
df = pd.DataFrame(rows, columns=['adc', 'pere', 'pp'])

# Calculer les effectifs pour chaque profession
df_pp_count = df['pp'].value_counts().reset_index()
df_pp_count.columns = ['pp', 'effectif']

# Créer un diagramme en cercle avec les effectifs comme données de survol
fig0 = px.pie(df_pp_count, names='pp', values='effectif', title='Répartition des professions du père', 
             hover_data=['effectif'])

st.write(f"Adc dont nous connaissons la profession du père : {len(df)}.")
st.plotly_chart(fig0, use_container_width=True)




query1 = """
MATCH (h:HOMME)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'}), (h)-[:MARIAGE]->(f), (f)<-[pd:PÈRE_DE]-(p:HOMME)-[:EXERCE]->(pp)
WHERE (e.date_début.year >= 1815 AND e.date_début.year <= 1852)
OR (e.date_fin.year >= 1815 AND e.date_fin.year <= 1852)
RETURN h, f, p, pp
"""

data = get_neo4j_results_of(query1)

rows = []
for entry in data:
    adc = entry['h']['nom']
    ep = entry['f']['nom']
    pere = entry['p']['nom']
    pp = entry['pp']['nom']
    rows.append([adc, ep, pere, pp])
df = pd.DataFrame(rows, columns=['adc', 'ep', 'pere', 'pp'])

# Calculer les effectifs pour chaque profession
df_pp_count = df['pp'].value_counts().reset_index()
df_pp_count.columns = ['pp', 'effectif']

# Créer un diagramme en cercle avec les effectifs comme données de survol
fig1 = px.pie(df_pp_count, names='pp', values='effectif', title='Répartition des professions du père de l\'épouse', 
             hover_data=['effectif'])

st.plotly_chart(fig1, use_container_width=True)