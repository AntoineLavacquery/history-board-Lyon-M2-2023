import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

from neo4jtools import *
from Accueil import page_config_params, make_sidebar_foot

st.set_page_config(**page_config_params)
make_sidebar_foot("https://github.com/AntoineLavacquery/history-board-Lyon-M2-2023")

st.markdown("""## Évolution du prix de la charge""")

query = """
MATCH (v:HOMME)-[vc:VENTE_CHARGE]->(a:HOMME)
WHERE vc.type_charge = "agent de change" AND vc.prix_charge IS NOT NULL
RETURN v, a, vc.date_acte_cession, vc.prix_charge
"""

data = get_neo4j_results_of(query)

# Extraire les informations pertinentes
rows = []
for entry in data:
    vendeur = entry['v']['nom']
    acheteur = entry['a']['nom']
    date_acte_cession = f"{entry['vc.date_acte_cession'].year}-{entry['vc.date_acte_cession'].month}-{entry['vc.date_acte_cession'].day}"
    date_acte_cession = datetime.strptime(date_acte_cession, "%Y-%m-%d").date()
    prix = entry['vc.prix_charge']
    rows.append([vendeur, acheteur, date_acte_cession, prix])
df = pd.DataFrame(rows, columns=['vendeur', 'acheteur', 'date_acte_cession', 'prix'])
df['date_acte_cession'] = pd.to_datetime(df['date_acte_cession'])
df = df.sort_values(by='date_acte_cession')

# Création de l'histogramme
fig = go.Figure(data=[go.Bar(
    x=df['date_acte_cession'],
    y=df['prix'],
)])

st.plotly_chart(fig, use_container_width=True)





# Extraction du mois et de l'année
df['annee_mois'] = df['date_acte_cession'].dt.to_period('M')

# Groupement des données par mois et calcul de la moyenne des prix
df_by_month = df.groupby('annee_mois')['prix'].mean().reset_index()

# Création d'un DataFrame avec tous les mois de janvier 1815 à décembre 1869
all_months = pd.period_range(start='1840-01', end='1855-12', freq='M')
all_months_df = pd.DataFrame(all_months, columns=['annee_mois'])

# Fusion avec les données calculées pour inclure tous les mois
final_data = pd.merge(all_months_df, df_by_month, on='annee_mois', how='left')

# Remplacement des valeurs NaN par 0
final_data['prix'].fillna(0, inplace=True)

final_data['annee_mois'] = final_data['annee_mois'].astype(str)

# Création de l'histogramme
fig2 = px.bar(final_data, x='annee_mois', y='prix',
             title='Prix moyen mensuel de janvier 1815 à décembre 1869',
             labels={'annee_mois': 'Date', 'prix': 'Prix moyen'},
             template='plotly_white')

# Modification de l'axe des x pour afficher les dates sous forme de frise chronologique
fig2.update_xaxes(type='category')

st.plotly_chart(fig2, use_container_width=True)