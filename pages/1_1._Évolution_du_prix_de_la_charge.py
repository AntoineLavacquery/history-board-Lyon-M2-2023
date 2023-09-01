import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

from neo4jtools import *
from Accueil import page_config_params, make_sidebar_foot

st.set_page_config(**page_config_params)
make_sidebar_foot("https://github.com/AntoineLavacquery/history-board-Lyon-M2-2023/blob/main/pages/1_1._Évolution_du_prix_de_la_charge.py")

population = len(get_neo4j_results_of("""
                                  MATCH (v)-[vc:VENTE_CHARGE]->(a)
                                  WHERE vc.type_charge = "agent de change"
                                  RETURN v, a, vc.date_acte_cession, vc.prix_charge
                                  """))

query = """
MATCH (v)-[vc:VENTE_CHARGE {type_charge: "agent de change"}]->(a), (v)-[e:EXERCE]->(:ACTIVITÉ {nom: "Agent de change"})
WHERE vc.prix_charge IS NOT NULL AND vc.date_acte_cession IS NOT NULL
RETURN v, a, vc.date_acte_cession, vc.prix_charge, (e.date_fin.year - e.date_début.year) AS d
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
    duree_charge = entry['d']
    rows.append([vendeur, acheteur, date_acte_cession, prix, duree_charge])
df = pd.DataFrame(rows, columns=['vendeur', 'acheteur', 'date_acte_cession', 'prix', 'duree_charge'])
df['date_acte_cession'] = pd.to_datetime(df['date_acte_cession'])
df = df.sort_values(by='date_acte_cession')
df_org = df.copy()

# Convert the 'date_acte_cession' column of the original df to datetime
df['date_acte_cession'] = pd.to_datetime(df['date_acte_cession'])

# Extraction du mois et de l'année
df['annee_mois'] = df['date_acte_cession'].dt.to_period('M')

# Création d'un colonne dédiée à l'affichage des informations de survol
df['transaction'] = "<br>Vendeur : " + df['vendeur'] + '<br>Acheteur : ' + df['acheteur'] + '<br>Prix : ' + df['prix'].astype(str) + ' F<br>'

# Groupement par mois pour obtenir la liste des transactions et la moyenne des prix
df_transaction = df.groupby('annee_mois')['transaction'].apply(list).reset_index()
df_by_month = df.groupby('annee_mois')['prix'].mean().reset_index()

# Merge the average prices and transactions data
df_by_month = pd.merge(df_by_month, df_transaction, on='annee_mois', how='left')

# Create a DataFrame with a row for each month between January 1841 and June 1860
all_months = pd.period_range(start='1841-01', end='1860-06', freq='M')
all_months_df = pd.DataFrame(all_months, columns=['annee_mois'])

# Merge this with the original df to ensure there's a row for every month
df_extended = pd.merge(all_months_df, df, on='annee_mois', how='left')

# Fill NaN values in 'duree_charge'
df_extended['duree_charge'].fillna(0, inplace=True)

# Fusion avec les données calculées pour inclure tous les mois
final_data = pd.merge(all_months_df, df_by_month, on='annee_mois', how='left')

# Remplacement des valeurs NaN par 0
final_data['prix'].fillna(0, inplace=True)
final_data['annee_mois'] = final_data['annee_mois'].astype(str)

# Create the subplot
fig = make_subplots(specs=[[{"secondary_y": True}]])


# Add first bar plot (Average Price) with custom hover info
fig.add_trace(
    go.Bar(x=final_data['annee_mois'], 
           y=final_data['prix'], 
           name='Prix moyen', 
           customdata=final_data['transaction'],
           hovertemplate='%{customdata}Prix: %{y} F',
           marker=dict(color=px.colors.qualitative.Dark2[0])
           ),
    secondary_y=False
)

# Add second bar plot (Duration for each transaction)
fig.add_trace(
    go.Bar(x=df_extended['annee_mois'].astype(str),
           y=df_extended['duree_charge'],
           name='Durée',
           opacity=0.6,
           marker=dict(color=px.colors.qualitative.Dark2[1])),
    secondary_y=True
)

# Set the layout with updated y-axis ranges and fixed x-axis range
fig.update_layout(title_text="Graphique 1.A. : Prix moyen mensuel et Durée de charge de janvier 1841 à juin 1860")
fig.update_xaxes(title_text="Date", fixedrange=True)
fig.update_yaxes(title_text="Prix moyen", range=[0, 350000], secondary_y=False)
fig.update_yaxes(title_text="Durée d'occupation de la charge en années", range=[0, 35], secondary_y=True)





st.markdown("""## 1. Évolution du prix de la charge""")

st.markdown("""
            #### Présentation
            Cette page donne accès au graphique du prix des charges des agents de change à partir des données issues des dépouillements
            des sources. Nous choisissons de représenter les données avec un diagramme en barre simple :
            - L'échelle de temps est placée en abscisses
            - Le montant des charges est représenté en ordonnée
            - Chaque barre représente une durée d'**un mois**. Sa largeur est **proportionnelle** à la durée effective que représente un
            un mois sur l'axe des x.
            - Les sommes exprimée sont alors la moyenne de toutes les ventes de charge survenues dans le mois en question. Puisque nous
            disposons d'un échantillon de données peu important, la plupart des entrées représentent une seule vente. Autrement dit, à l'échelle de nos données, il est rare que
            deux ventes se soient produites le même mois.
            - Le survole de la souris fait apparaitre le ou les couples vendeur - acheteurs, avec le prix de la charge.
            """)

graph_tab, df_tab, query_tab = st.tabs(["Graphique", "Données d'origine (dataframe)", "Requête depuis la base de données"])
with graph_tab:
    st.plotly_chart(fig, use_container_width=True)
with df_tab:
    st.write(df_org)
with query_tab:
   st.code(query, language="cypher", line_numbers=True)

st.markdown(f"""
        #### Typologie des données
        Dans le périmètre de notre base de données, la population totale des agents de change est de 247 individus.
        Sur ce nombre, nous connaissons des informations sur les ventes pour {population} charges. Nous disposons
        de {len(df_org)} charges dont nous connaissons suffisemment d'information pour la construction de notre graphique.
        
        Ainsi, la sélection de l'échantillon est surtout une question de contrainte. L'individu statistique est un charge d'agent de change.
        Elle nous donne des informations sur un acheteur et un vendeur puisqu'elle prend le forme même de relation dans la base de données.
        Nous construisons ici une visualisation simple, à partir d'un petit échantillon de valeurs quantitatives continues, afin de constater et
        mettre en corrélation les tendances avec des informations extérieures à ses données. 
        """)