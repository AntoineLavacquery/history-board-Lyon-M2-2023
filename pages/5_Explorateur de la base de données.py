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
make_sidebar_foot("https://www.univ-lyon3.fr/medias/photo/udl-lyon3-web_1493035760450-png?ID_FICHE=239744&INLINE=FALSE")

st.markdown("""## Explorateur de la base de données""")

# --- Tous les agents de change entre 1815 et 1852
query = """
MATCH (v)-[vc:VENTE_CHARGE {type_charge: "agent de change"}]-(a)
RETURN v, vc, a
"""
data = get_neo4j_results_of(query)
# data

nodes = []
edges = []

# Initialiser un ensemble vide
noms_vus = set()

for entry in data:
    nom = entry["v"]["nom"]
    if nom not in noms_vus:
        nodes.append(Node(id=nom, label=nom, size=25, shape="circularImage", image="https://drive.google.com/file/d/1PT1OSB8rV1rEs8eqiEKOuPQK8bittsS8/view?usp=sharing"))
        noms_vus.add(nom)  # Ajouter le nom à l'ensemble

for entry in data:
    source = entry["v"]["nom"]
    label = entry["vc"][1]
    target = entry["a"]["nom"]
    edges.append(Edge(source=source, label=label, target=target)) 


config = Config(width=1000,
                height=700,
                directed=True, 
                physics=True, 
                hierarchical=False,
                use_container_width=True
                # **kwargs
                )

return_value = agraph(nodes=nodes, 
                      edges=edges, 
                      config=config)

with st.expander("Voir la requête"):
    st.write(query)