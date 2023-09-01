import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from streamlit_agraph import agraph, Node, Edge, Config

from neo4jtools import *
from Accueil import page_config_params, make_sidebar_foot

st.set_page_config(**page_config_params)
make_sidebar_foot("https://github.com/AntoineLavacquery/history-board-Lyon-M2-2023/blob/main/pages/4_4._Origines_sociales.py")

st.markdown("""## 6. Explorateur de la base de données""")

st.markdown("""Cette page donne un aperçu de la base de données et de leur organisation au sein de la base Neo4J.
            L'affichage qui suit sert d'exemple, en affichant les transmissions de charges entre les agents de change.""")

# --- Tous les agents de change
query = """
MATCH (v)-[vc:VENTE_CHARGE {type_charge: "agent de change"}]-(a)
RETURN v, vc, a
"""

data = get_neo4j_results_of(query)

nodes = []
edges = []

# Ensemble vide
noms_vus = set()
for entry in data:
    nom = entry["v"]["nom"]
    if nom not in noms_vus:
        nodes.append(Node(id=nom, label=nom, size=25, shape="circularImage", image="https://drive.google.com/file/d/1PT1OSB8rV1rEs8eqiEKOuPQK8bittsS8/view?usp=sharing"))
        noms_vus.add(nom)

for entry in data:
    source = entry["v"]["nom"]
    label = entry["vc"][1]
    target = entry["a"]["nom"]
    edges.append(Edge(source=source, label=label, target=target)) 


config = Config(width=1000,
                height=700,
                directed=False, 
                physics=True, 
                hierarchical=False,
                use_container_width=True,
                stabilize=False
                # **kwargs
                )

graph, cypher = st.tabs(["Graphique", "Requête"])
with graph:
    return_value = agraph(nodes=nodes, 
                      edges=edges, 
                      config=config)
with cypher:
    st.code(query, language="cypher", line_numbers=True)
