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

st.markdown("""## Répartition géographique""")

# query = """
# MATCH (h:HOMME)-[:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'})
# OPTIONAL MATCH (h:HOMME)-[l:HABITE]->(p:LIEU)
# RETURN h, l, l.date_début, l.date_fin, p
# """
query = """
MATCH (n)-[l:HABITE]->(p:LIEU)
OPTIONAL MATCH (n)-[:EXERCE]->(a:ACTIVITÉ)
RETURN n, a, l, l.date_début, l.date_fin, p
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
    if item["a"]:
        d["activite"] = item["a"]["nom"]
    else:
        d["activite"] = None
    final_data.append(d)
for d in final_data:
    if d["date_debut"]:
        d["date_debut"] = d["date_debut"].to_native()
    if d["date_fin"]:
        d["date_fin"] = d["date_fin"].to_native()
df = pd.DataFrame(final_data)


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

# Affichage du DataFrame final
# grouped_df



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
    for point in points
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

st.markdown("Parler du fait que les années n'ont que les deux chiffres de la fin à cause du temps UNIX universel.")
st_folium(m, use_container_width=True, returned_objects=[])