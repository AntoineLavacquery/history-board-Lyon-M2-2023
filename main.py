# Global modules
import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium import plugins
from streamlit_folium import st_folium
import time

# Personnal modules
from neo4jtools import *

title = "Les agents de change auprès de la Bourse de Lyon (1815 - 1852)"
st.set_page_config(
    page_title=f"Mémoire | Université Lyon 3 | 2023 | {title}",
    page_icon="https://www.univ-lyon3.fr/images/logo.png"
)
st.title(title)


query = """
MATCH (n0)-[re0:EXERCE]->(a:`ACTIVITÉ` {nom: "Agent de change"}),
(n1)-[re1:EXERCE]->(a:`ACTIVITÉ` {nom: "Agent de change"}),
(n0)-[rv:VENTE_CHARGE {type_charge: "agent de change"}]->(n1)
RETURN n0, re0.date_début, re0.date_fin, rv.date_acte_cession, n1, re1.date_début, re1.date_fin
"""

results = get_neo4j_results_of(query)
# results

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
all




import plotly.graph_objects as go

fig = go.Figure()
# Set axes properties
fig.update_xaxes(range=[1800, 1860], showgrid=True, title_text="Années")
fig.update_yaxes(range=[0, 30], title_text="Charges d'agent de change")
fig.update_layout(title="La transmission des charges d'agents de change entre 1815 et 1852", width=700, height=500)


fig.add_trace(go.Scatter(
    x=[1.5, 4.5],
    y=[0.75, 0.75],
    text=["Unfilled Rectangle", "Filled Rectangle"],
    mode="text",
))

for i in range(len(all)):
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
        
        try:
            fig.add_shape(
                type="rect",
                x0=annee_debut,
                x1=annee_fin,
                y0=i,
                y1=i+0.8,
                line=dict(color="RoyalBlue")
                )
        except:
            continue



# # Add shapes
# fig.add_shape(type="rect",
#     x0=1815, y0=5, x1=1820, y1=6,
#     line=dict(color="RoyalBlue"),
# )
# fig.add_shape(type="rect",
#     x0=1820, y0=5, x1=1828, y1=6,
#     line=dict(
#         color="RoyalBlue",
#         width=2,
#     ),
#     fillcolor="LightSkyBlue",
# )
# fig.update_shapes(dict(xref='x', yref='y'))

# Plot!
st.plotly_chart(fig, use_container_width=True)