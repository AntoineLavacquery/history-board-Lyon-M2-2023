import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium import plugins
from streamlit_folium import st_folium
import time

from neo4jtools import *
from Accueil import page_config_params, make_sidebar_foot

st.set_page_config(**page_config_params)
make_sidebar_foot("https://github.com/AntoineLavacquery/history-board-Lyon-M2-2023")

query = """
MATCH (n)-[l:HABITE]->(p:LIEU), (n)-[:EXERCE]->(a:ACTIVITÉ {nom: "Agent de change"})
RETURN n, l, l.date_début, l.date_fin, p
"""

data = get_neo4j_results_of(query)

# Liste pour stocker les données finales
final_data = []

# Parcours des éléments de la liste initiale et extraction des informations
for item in data:
    d = {
        "nom": item["n"]["nom"],
        "adresse_historique": item["p"]["adresse_historique"],
        "adresse_actuelle": item["p"]["adresse_actuelle"],
        "latitude": item["p"]["latitude"],
        "longitude": item["p"]["longitude"],
        "date_debut": item.get("l.date_début", None),
        "date_fin": item.get("l.date_fin", None),
    }
    final_data.append(d)

for d in final_data:
    if d["date_debut"]:
        d["date_debut"] = d["date_debut"].to_native()
    if d["date_fin"]:
        d["date_fin"] = d["date_fin"].to_native()
df = pd.DataFrame(final_data)
df = df.drop_duplicates()



@st.cache_data(show_spinner="Chargement de la carte...", experimental_allow_widgets=True)
def make_map(df):
    # Liste des colonnes à conserver (toutes les autres colonnes)
    cols_to_keep = [col for col in df.columns if col not in ["adresse_historique", "adresse_actuelle", "longitude", "latitude"]]
    # Liste des années de 1802 à 1863
    years = range(1802, 1863 + 1)

    # Regrouper les données en fonction des colonnes "adresse_historique", "adresse_actuelle", "longitude" et "latitude"
    grouped_df = df.groupby(["adresse_historique", "adresse_actuelle", "longitude", "latitude"])[cols_to_keep].apply(lambda x: x.to_dict(orient='records')).reset_index(name='noms')
    print(grouped_df.loc[0]["noms"])
    # Créer les colonnes pour chaque année
    for year in years:
        grouped_df[(year)] = None

    # Remplir les colonnes des années avec les noms correspondants
    for index, row in grouped_df.iterrows():
        noms = row['noms']
        for nom in noms:
            try:
                debut = nom['date_debut'].year
                fin = nom['date_fin'].year
            except:
                continue
            for year in range(debut, fin + 1):
                if grouped_df.at[index, year] is None:
                    grouped_df.at[index, year] = []
                grouped_df.at[index, year].append(nom['nom'])

    # Supprimer la colonne 'noms' car elle n'est plus nécessaire
    grouped_df.drop(columns=['noms'], inplace=True)

    columns = list(grouped_df)
    # Constitution d'une liste des années à partir des noms de colonne : seules celles ayant "18" sont conservées (pour discriminer automatiquement les autres)
    years = [str(year) for year in columns if "18" in str(year)]

    # Liste de points initialisée
    points = []
    # Pour chaque année
    for year in years:
        year = int(year)
        # Pour chaque adresse
        for i in range(len(grouped_df.index)):
            # Si la cellule est une chaine de caractère (donc n'est pas vide)
            # st.write(grouped_df[year][i])
            if isinstance(grouped_df[year][i], list):
                # Le contenus de la cellule (c à d : liste de noms des agents de change) est stocké dans "residents"
                residents = grouped_df[year][i]
                residents = list(dict.fromkeys(residents))
                popup_txt = "<br>".join(residents)
                # Idem pour longitude et latitude
                longitude = grouped_df["longitude"][i]
                latitude = grouped_df["latitude"][i]
                # Définition d'un "score" (c à d le nombre d'agents habitants dans la rue) via la retransformation en liste et comptage de la longueur de ladite liste
                score = len(residents)

                # Définition du point qui sera ajouté sur la carte (infos sur "time" -> voir cellule markdown plus bas)
                point = {
                    "time": "20" + str(year)[2:],
                    "popup": popup_txt,
                    "coordinates": [longitude, latitude],
                    "score": score
                }
                # Chaque dict ainsi constitué est ajouté à la liste "points"
                points.append(point)

    merged_points = {}
    for item in points:
        key_str = item['time'] + '_' + '_'.join(map(str, item['coordinates']))
        if key_str in merged_points:
            merged_points[key_str]['popup'] += "<br>" + item['popup']
            merged_points[key_str]['score'] += item['score']
        else:
            merged_points[key_str] = item.copy()

    # Conversion du dictionnaire fusionné en une liste de dictionnaires
    merged_points = list(merged_points.values())

    # Pour chaque point dans points, on constitue des features qui nous permettront de constuire le graphique
    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": point["coordinates"],
            },
            "properties": {
                "time": point["time"],
                "popup": point["popup"],
                "id": "house",
                "icon": "circle",
                "iconstyle": {
                    'radius': point["score"] * 5
                },
            },
        }
        for point in merged_points
    ]

    m = folium.Map(location=[45.765, 4.835],
                zoom_start=15,
                attr="ign.fr",
                tiles='https://wxs.ign.fr/cartes/geoportail/wmts?'+
                '&REQUEST=GetTile&SERVICE=WMTS&VERSION=1.0.0&TILEMATRIXSET=PM'+
                '&LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&STYLE=normal&FORMAT=image/png'+
                '&TILECOL={x}&TILEROW={y}&TILEMATRIX={z}'
                )

    folium.raster_layers.WmsTileLayer(url = 'https://wxs.ign.fr/cartes/geoportail/r/wms?SERVICE=WMS',
                                    layers = 'GEOGRAPHICALGRIDSYSTEMS.ETATMAJOR40',
                                    transparent = True, 
                                    control = True,
                                    fmt="image/png",
                                    name = 'État-major (1820-1866)',
                                    overlay = True,
                                    show = True,
                                    ).add_to(m)
    folium.LayerControl().add_to(m)

    plugins.TimestampedGeoJson(
        {"type": "FeatureCollection", "features": features},
        period="P1Y",
        add_last_point=True,
        auto_play=False,
        loop=False,
        max_speed=1,
        loop_button=True,
        date_options="YY",
        time_slider_drag_update=True,
        duration="P1Y",
    ).add_to(m)

    st_folium(m, use_container_width=True, returned_objects=[])


st.markdown("""## 2. Répartition géographique""")

st.markdown(
    """
    La carte suivant est interactive. Elle permet de faire défiler les lieux de résidence des agent de change au cours des années.
    Point important : seuls les deux derniers chiffres s'affichent pour signifier les années dans le lecteur de manipulation.
    """)

map_tab, df_tab, query_tab = st.tabs(["Carte", "Données d'origine (dataframe)", "Requête depuis la base de données"])
with map_tab:
    make_map(df)
with df_tab:
    st.write(df)
with query_tab:
   st.code(query, language="cypher", line_numbers=True)

st.markdown(
    """
    La construction de la carte interactive passe par deux grandes étapes : la préparation des données et la paramétrisation
    des bibliothèques de géovisualisation. Nous nous concentrerons uniquement sur les points notables de ces étapes.
    Les données source de la carte interactive sont représentées par des adresses. Stockée dans notre base de données, elles 
    sont représentées par des nœuds de type LIEU. À chaque lieu correspond un nœud. Nous avions envisagé d’encoder les villes
    dans un type de nœud distinct des noms de rue avant d’abandonner cette solution car elle ne présentait aucun avantage et rendait
    la manipulation confuse. Chaque nom de rue possède une propriété "adresse_historique" et "adresse_actuelle" et de coordonnées
    géographiques issues du geoparser de Google.

    Nous construisons notre géo visualisation sur la bibliothèque open source Folium, basée sur la bibliothèque java Leaflet.
    Sur le versant du paramétrage de cette géovisualisation un paramètre propre aux études en histoire complique le fonctionnement de
    la visualisation. Très peu documentée au moment de réaliser cette étude, une erreur survient systématiquement au sein du paramètre
    définissant les années lorsque nous passons notre tranche du XIXe siècle. Il s’avère en effet que le système de gestion du temps s’appuie 
    sur l’heure Unix (ou Posix) fondée sur le nombre de seconde écoulée depuis la 1er janvier 1970 à minuit. Toute date antérieure à
    cette second zéro provoque le dysfonctionnement du module. Il est donc nécessaire, dans l’état actuel du code de ces bibliothèque
    de tricher sur les dates. Par conséquent, deux siècles ont été ajoutés à nos dates pour permettre le fonctionnement du code.
    Afin de ne pas perturber la lecture de l’interface, nous avons choisi de représenter les années seulement avec les deux derniers
    chiffres. Ainsi l’utilisateur ne s’aperçoit pas qu’en sélectionnant l’année 30, à savoir 1830, la machine exécute sa recherche pour l’année 2030.
    """)