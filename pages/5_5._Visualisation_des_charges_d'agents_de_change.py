# Global modules
import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium import plugins
from streamlit_folium import st_folium
import time
import plotly.graph_objects as go
from streamlit_extras.mention import mention
import json

# Personnal modules
from neo4jtools import *

page_config_params = {"layout": "wide",
                      "page_title": "Mémoire | Université Lyon 3 | 2023 | Les agents de change auprès de la Bourse de Lyon (1815 - 1852)",
                      "page_icon": "https://www.univ-lyon3.fr/images/logo.png"}

def make_sidebar_foot(url):
    sidebar_data = {"label": "Code source de la page",
                "icon": "github",
                "hint": {"body": "Double-cliquer dans un graphique pour réinitialiser l'échelle des axes et le niveau de zoom",
                         "icon": "💡"},
                "image": "https://www.univ-lyon3.fr/medias/photo/udl-lyon3-web_1493035760450-png?ID_FICHE=239744&INLINE=FALSE",
                "markdown": "**Antoine LAVACQUERY**  \n*Master 2 - Construction des sociétés contemporaines  \nMaster 2 - Humanités numériques  \n2022 - 2023*"
                }
    with st.sidebar:
        mention(
            label=sidebar_data["label"],
            icon=sidebar_data["icon"],
            url=url,
        )
        st.success(**sidebar_data["hint"])
        st.image(sidebar_data["image"])
        st.markdown(sidebar_data["markdown"])

st.set_page_config(**page_config_params)
make_sidebar_foot("https://github.com/AntoineLavacquery/history-board-Lyon-M2-2023/blob/main/pages/5_5._Visualisation_des_charges_d'agents_de_change.py")


st.markdown("## 5. Visualisation des charges d'agents de change")


st.markdown(
    """
    La visualisation proposée dans cette page n'appartient à aucun type prédéfini.
    Nous avons choisi de représenter le passage des charges de main en main sur une échelle temporelle.
    Plusieurs points sont à noter pour la lecture de ce graphique :
    - En ordonnée : à chaque numéro correspond une charge. Aucun ordre n'a été défini, les numéros représentent
    un indice et non une valeur. Ils facilitent ainsi la lecture et le repérage dans au sein du graphique.
    - En abscisse : échelle de temps, l'unité est l'année.
    - Survoler le centre d'une barre fait apparaitre les informations sur l'agent représenté. 
""")


query = """
MATCH (n0)-[re0:EXERCE]->(a:`ACTIVITÉ` {nom: "Agent de change"}),
(n1)-[re1:EXERCE]->(a),
(n0)-[rv:VENTE_CHARGE {type_charge: "agent de change"}]->(n1)
RETURN n0, re0.date_début, re0.date_fin, rv.date_acte_cession, n1, re1.date_début, re1.date_fin
"""

results = get_neo4j_results_of(query)

all = []
for result in results:
    person0 = {
        "nom": result["n0"]["nom"],
        "date_debut": result["re0.date_début"],
        "date_fin": result["re0.date_fin"]
        }
    person1 = {
        "nom": result["n1"]["nom"],
        "date_debut": result["re1.date_début"],
        "date_fin": result["re1.date_fin"],
        "date_acte_cession": result["rv.date_acte_cession"]
        }
    all.append([person0, person1])

def connect_strands(all):
    for i in range(len(all)):
        strand_i = all[i]
        person0 = strand_i[0]
        person1 = strand_i[-1]
        person1_light = person1.copy()
        del person1_light["date_acte_cession"]

        for j in range(i + 1, len(all)):
            strand_j = all[j]
            other_person0 = strand_j[0]
            other_person1 = strand_j[-1]
            other_person1_light = other_person1.copy()
            del other_person1_light["date_acte_cession"]

            if person0 == other_person1_light:
                all[j] += strand_i[1:]
                all.remove(strand_i)
                connect_strands(all)
                return
            if person1_light == other_person0:
                all[i] += strand_j[1:]
                all.remove(strand_j)
                connect_strands(all)
                return
connect_strands(all)

fig = go.Figure()

# Traçage des bandes des bandes grises signifiant les décennies
for i in range(1700, 2000, 20):  # Pas de 20 pour alterner
    fig.add_shape(
        go.layout.Shape(
            type="rect",
            xref="x",
            yref="paper",
            x0=i,
            x1=i+10,
            y0=0,
            y1=1,
            fillcolor="rgb(245, 245, 245)",
            layer="below",
            line_width=0,
        )
    )

annotations = []
# Initialisation de l'index des couleurs
color_index = 0
color_palette = px.colors.qualitative.Set2

values = st.slider(
    "Sélectionnez l'intervalle de durée de charges (par défaut : toutes)",
    0, 38, (0, 38))

for i in range(len(all)):
    h = i
    strand = all[i]

    for j in range(len(strand)):
        if j > 0:
            previous = strand[j - 1]
        guy = strand[j]
        if j < len(strand) - 1:
            next = strand[j + 1]
        
        if "date_acte_cession" in guy and guy["date_acte_cession"]:
            annee_debut = guy["date_acte_cession"].year
        elif "date_debut" in guy and guy["date_debut"]:
            annee_debut = guy["date_debut"].year
        elif previous and "date_fin" in previous and previous["date_fin"]:
             annee_debut = previous["date_fin"].year
        
        if "date_fin" in guy and guy["date_fin"]:
            annee_fin = guy["date_fin"].year
        elif next and "date_acte_cession" in next and next["date_acte_cession"]:
            annee_fin = next["date_acte_cession"].year
        elif next and "date_debut" in next and next["date_debut"]:
            annee_fin = next["date_debut"].year
        
        # Utilisez la couleur actuelle de la palette
        current_color = color_palette[color_index % len(color_palette)]

        if (annee_fin - annee_debut) >= values[0] and (annee_fin - annee_debut) <= values[1]:
            fig.add_shape(
                type="rect",
                x0=annee_debut,
                x1=annee_fin,
                y0=1+i-0.142,
                y1=1+i+0.142,
                fillcolor=current_color,
                line_width=0)

                
            # Ajout de la trace de survol
            fig.add_trace(go.Scatter(
                x=[(annee_debut + annee_fin) / 2],  # Position centrale du rectangle sur l'axe des x
                y=[(1+i-0.142+1+i+0.142) / 2],  # Position centrale du rectangle sur l'axe des y
                hovertext=[f"{guy['nom']}<br>Entrée : {guy['date_debut']}<br>Sortie : {guy['date_fin']}"],
                hoverinfo="text",
                mode="markers",
                marker=dict(
                    color='rgba(0,0,0,0)',  # Couleur transparente
                    size=1  # Taille minimale
                )
            ))
        
        # Augmentez l'index des couleurs pour la prochaine itération
        color_index += 1

fig.update_xaxes(range=[1795, 1870], showgrid=False, title_text="Années", side='top')
fig.update_yaxes(range=[6, 20], title_text="Numéro des charges d'agent de change", tickvals=list(range(1, 45)), 
                 showticklabels=True, showgrid=True)
fig.update_layout(title=f"Graphique 5.A. La transmission des charges d'agents de change (de {values[0]} à {values[1]} années d'exercice)", 
                  height=900, dragmode="pan", showlegend=False)



graph, data, cypher = st.tabs(["Graphique", "Données reconstituées (list of dict)", "Requête"])
with graph:
    st.plotly_chart(fig, use_container_width=True)
with data:
    st.json(all)
with cypher:
    st.code(query, language="cypher", line_numbers=True)
