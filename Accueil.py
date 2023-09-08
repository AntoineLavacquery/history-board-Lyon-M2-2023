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
from datetime import datetime

# Personnal modules
from neo4jtools import *

page_config_params = {"layout": "wide",
                      "page_title": "Mémoire | Université Lyon 3 | 2023 | Les agents de change auprès de la Bourse de Lyon - première moitié du XIX<sup>e<\sup> siècle",
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
make_sidebar_foot("https://github.com/AntoineLavacquery/history-board-Lyon-M2-2023/blob/main/Accueil.py")

title = "Les agents de change auprès de la Bourse de Lyon, première moitié du XIXe siècle"

st.markdown("## " + title)


st.markdown(
    """
    #### Présentation
    Nous présentons, au travers de cette interface, la **mise en œuvre et le regroupement des visualisations** développées pour
    argumenter le propos de notre étude sur le groupe des agents de change lyonnais de la première moitié du XIXe siècle. L'idée poursuivie au sein de ces
    pages n'est pas de copier ou reformuler le propos tenu au sein du mémoire ou au sein des annexes consacrées aux humanités numériques, mais 
    bien d'expliquer davantage et avec une orientation plus technique les caractéristiques de ces visualisations.

    Nous détaillons ici les grandes différences avec les versions "papiers" du mémoire :
    1. Une partie des visualisations contenue au sein de ces pages ne sont pas disponibles ici.
    2. Elles sont toutes interactives. Cette interactivité peut être **faible**, par exemple dans le cas du diagramme en barre
    sur le prix des charges ou **forte** voire **indispensable**, comme dans le cas de la visualisation de la répartition géographique.
    3. Le plus souvent, nous présentons les données ayant servies à constituer les visualisations, mais toujours en second plan (onglet ou menu déroulant).
    Le fait qu'il soit nécessaire de consulter ces pages dans certains cas nous a conduits à ne pas obstruer l'information avec les données brutes.
    L'interface est prévue pour être **consultée rapidement**, pendant la lecture.

    Le propos que nous adoptons dans ces pages cherche avant tout à être succinct. L'idée est d'expliquer les informations essentielles
    pour comprendre les démarches qui ont initié les visualisations. Nous expliquons également les raisons nous ayant conduits à en effectuer
    certaines plutôt que d'autres.

    #### Code source
    Les traitements informatiques qui ne trouvent pas leur place au sein de cette interface sont disponibles en ligne :
    https://github.com/AntoineLavacquery/history-board-Lyon-M2-2023/tree/main/notebooks. Surtout utilisés
    en tant que qu'outils facilitateurs de la recherche (ou même simplement d'expérimentation), ils n'ont pas vocation à être présentés
    en tant que tel.
    """
)

st.error("""Le chargement des pages peut être long. Ne pas hésiter à rafraichir la page si une erreur apparait.
         En cas d'erreur ou de blocage prolongé :
         antoine.lavacquery@proton.me.
         """,
         icon="⚠️")
