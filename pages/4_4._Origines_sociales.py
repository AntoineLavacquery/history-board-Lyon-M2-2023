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

h = 500
# -[:EXERCE]->(pp)
query0 = """
MATCH (h)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'}), (h)<-[pd:PÈRE_DE]-(p)-[:EXERCE]->(pp)
OPTIONAL MATCH (p)-[:EXERCE]->(pp)
RETURN h, p, pp
"""

data = get_neo4j_results_of(query0)

rows = []
for entry in data:
    adc = entry['h']['nom']
    pere = entry['p']['nom']
    try:
        pp = entry['pp']['nom']
    except:
        pp = None
    rows.append([adc, pere, pp])
df0 = pd.DataFrame(rows, columns=['adc', 'pere', 'pp'])

# Calcule des effectifs pour chaque profession
df_pp_count0 = df0['pp'].value_counts().reset_index()
df_pp_count0.columns = ['pp', 'effectif']

# Création un diagramme en cercle avec les effectifs comme données de survol
fig0_pie = px.pie(df_pp_count0,
              names='pp',
              values='effectif',
              title='Graphique 4.A. : Diagramme sectoriel des professions du père des agents de change',
              hover_data=['effectif'],
              height=h,
              color_discrete_sequence=px.colors.qualitative.Set2)

fig0_bar = px.bar(df_pp_count0,
              x='pp',
              y='effectif',
              title="Graphique 4.A. : Diagramme en bâton des professions du père des agents de change",
              hover_data=['effectif'],
              color='pp',
              height=h,
              color_discrete_sequence=px.colors.qualitative.Set2)


query1 = """
MATCH (h:HOMME)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'}), (h)-[:MARIAGE]->(f), (f)<-[pd:PÈRE_DE]-(p:HOMME)-[:EXERCE]->(pp)
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
df1 = pd.DataFrame(rows, columns=['adc', 'ep', 'pere', 'pp'])

# Calculer les effectifs pour chaque profession
df_pp_count1 = df1['pp'].value_counts().reset_index()
df_pp_count1.columns = ['pp', 'effectif']

fig1_bar = px.bar(df_pp_count1,
              x='pp',
              y='effectif',
              title="Graphique 4.B. : Diagramme en bâton des professions du père des épouses des agents de change",
              hover_data=['effectif'],
              color='pp',
              color_discrete_sequence=px.colors.qualitative.Set2)

fig1_pie = px.pie(df_pp_count1,
              names='pp',
              values='effectif',
              title='Graphique 4.B. : Diagramme sectoriel des professions du père des épouses des agents de change',
              hover_data=['effectif'],
              color_discrete_sequence=px.colors.qualitative.Set2)

st.markdown(f"""
            ## 4. Origines sociales

            Cette page décrit statistiquement les origines sociales des agents de change. Nous choisissons de cronstruire les graphiques,
            à partir des données profession du père des agents de change et du père de leurs épouses. Nous récupérerons **{len(df0)}** cas pour lesquels
            nous connaissons au moins une profession. Pareillement, la répartition dans le cas des épouse nous utilisons de **{len(df1)}** individus.
            """)

# st.markdown("""
#             #### Répartition des professions des pères des agents de change
#             Ipsum lorem
#             """)

tab0_pie, tab0_bar, tab0_q = st.tabs(["Diagramme sectoriel", "Diagramme en bâton", "Requête"])
with tab0_pie:
    st.plotly_chart(fig0_pie, use_container_width=True)
with tab0_bar:
    st.plotly_chart(fig0_bar, use_container_width=True)
with tab0_q:
    st.code(query0, language="cypher", line_numbers=True)

st.markdown("""
            #### Répartition des professions des pères des épouses des agents de change
            Ipsum lorem
            """)

tab1_pie, tab1_bar, tab1_q = st.tabs(["Diagramme sectoriel", "Diagramme en bâton", "Requête"])
with tab1_pie:
    st.plotly_chart(fig1_pie, use_container_width=True)
with tab1_bar:
    st.plotly_chart(fig1_bar, use_container_width=True)
with tab1_q:
    st.code(query0, language="cypher", line_numbers=True)


query = """
MATCH (h)-[eadc:EXERCE]->(adc:ACTIVITÉ {nom:'Agent de change'}), (p)-[pd:PÈRE_DE]->(h), (p)-[ep:EXERCE]->(ap:ACTIVITÉ)
WHERE eadc.date_début IS NOT NULL
RETURN h, eadc.date_début, ap
"""

data = get_neo4j_results_of(query)

# Extraire les informations pertinentes
rows = []
for entry in data:
    if 3 < 2:#entry['a']['nom'] == "Agent de change" or entry['a']['nom'] == "Syndic":
        pass
    else:
        nom = entry['h']['nom']
        date_debut = f'{entry["eadc.date_début"].year}-{entry["eadc.date_début"].month}-{entry["eadc.date_début"].day}'
        date_debut = datetime.strptime(date_debut, "%Y-%m-%d").date()
        activite = entry['ap']['nom']
        rows.append([nom, date_debut, activite])
df = pd.DataFrame(rows, columns=["nom", "date_debut", "activite"])
df['date_debut'] = pd.to_datetime(df['date_debut'])
df = df.sort_values(by='date_debut')

# Extraire l'année de la colonne 'date_debut'
df['annee_debut'] = df['date_debut'].dt.year

# Regrouper les données par année et par activité
pivot_df = df.groupby(['annee_debut', 'activite']).size().unstack().fillna(0)


# Vos données doivent être stockées dans df_new
fig_point = px.scatter(df, x='date_debut', y='nom', color='activite',
                 color_discrete_sequence=px.colors.qualitative.Set2,
                 height=600)
fig_point.update_traces(marker=dict(size=6))
fig_point.update_layout(showlegend=True, yaxis_title="Nom de l'agent', xaxis_title='Date de début d'activité", title="Graphique 4.C. : Analyse bivariée")


# Conversion du DataFrame pivoté pour la visualisation avec Plotly
df_plotly = pivot_df.reset_index()

fig_bar = px.bar(df_plotly, x='annee_debut', y=df_plotly.columns[1:],
             labels={'value': "Nombre d'agents de change', 'annee_debut': 'Année de début d'activité"},
             height=600)

fig_bar.update_layout(barmode='stack', xaxis_title="Année de début d'activité", yaxis_title="Nombre d'agents de change", title='Graphique 4.C. : Analyse bivariée')



bi_point, bi_bar = st.tabs(["Points", "Histogramme empilé"])
with bi_point:
    st.plotly_chart(fig_point, use_container_width=True)
with bi_bar:
    st.plotly_chart(fig_bar, use_container_width=True)


# # Sunburst
# df_sunburst = df.groupby(['annee_debut', 'activite']).size().reset_index(name='count')
# fig_sun = px.sunburst(df_sunburst, path=['annee_debut', 'activite'], values='count') # color='activite'
# st.plotly_chart(fig_sun, use_container_width=True)

# # Treemap
# fig_tree = px.treemap(df_sunburst, path=['annee_debut', 'activite'], values='count') #color='activite',
# st.plotly_chart(fig_tree, use_container_width=True)