import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import numpy as np
from streamlit_extras.mention import mention

from neo4jtools import *
from Accueil import page_config_params, make_sidebar_foot

st.set_page_config(**page_config_params)
make_sidebar_foot("https://github.com/AntoineLavacquery/history-board-Lyon-M2-2023/blob/main/pages/3_3._Statistiques_sur_les_durées_de_charge.py")

# ******************************
# Requêtes vers la base de données
# ******************************

# --- Agents de change ayant un agent de change dans leur famille proche
query_fam = """
MATCH (h)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'}),
(gp)-[ad:`AÏEUL_DE`]->(h), (gp)-[:EXERCE]->(a)
RETURN h, e.date_début, e.date_fin
UNION
MATCH (h)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'}),
(p)-[pd:PÈRE_DE]->(h), (p)-[:EXERCE]->(a)
RETURN h, e.date_début, e.date_fin
UNION
MATCH (h)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'}),
(f)-[fd:FRÈRE_DE]-(h), (f)-[:EXERCE]->(a)
RETURN h, e.date_début, e.date_fin
UNION
MATCH (h)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'}),
(o)-[od:ONCLE_DE]->(h), (o)-[:EXERCE]->(a)
RETURN h, e.date_début, e.date_fin

UNION

MATCH (h)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'}),
(f)-[:MARIAGE]-(h),
(gpf)-[adf:`AÏEUL_DE`]->(f), (gpf)-[:EXERCE]->(a)
RETURN h, e.date_début, e.date_fin
UNION
MATCH (h)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'}),
(f)-[:MARIAGE]-(h),
(pf)-[pdf:`PÈRE_DE`]->(f), (pf)-[:EXERCE]->(a)
RETURN h, e.date_début, e.date_fin
UNION
MATCH (h)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'}),
(f)-[:MARIAGE]-(h),
(ff)-[fdf:`FRÈRE_DE`]-(f), (ff)-[:EXERCE]->(a)
RETURN h, e.date_début, e.date_fin
UNION
MATCH (h)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'}),
(f)-[:MARIAGE]-(h),
(onf)-[odf:`ONCLE_DE`]->(f), (onf)-[:EXERCE]->(a)
RETURN h, e.date_début, e.date_fin
"""
data_fam = get_neo4j_results_of(query_fam)

rows = []
for entry in data_fam:
    nom = entry['h']['nom']
    date_naissance = entry['h'].get('date_naissance', None)
    year_naissance = date_naissance.year if date_naissance else date_naissance
    date_debut = entry['e.date_début']
    year_debut = date_debut.year if date_debut else date_debut
    date_fin = entry['e.date_fin']
    year_fin = date_fin.year if date_fin else date_fin
    rows.append([nom, year_naissance, year_debut, year_fin])
df_fam = pd.DataFrame(rows, columns=['nom', 'year_naissance', 'year_debut', 'year_fin'])
df_fam_yn = df_fam.dropna(subset=['year_naissance'])  # Suppression des valeurs 'None' dans la colonne "date_naissance"


# --- Tous les agents de change
query = """
MATCH (h)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'})
RETURN h, e.date_début, e.date_fin
"""
data = get_neo4j_results_of(query)

rows = []
for entry in data:
    nom = entry['h']['nom']
    date_naissance = entry['h'].get('date_naissance', None)
    year_naissance = date_naissance.year if date_naissance else date_naissance
    date_debut = entry['e.date_début']
    year_debut = date_debut.year if date_debut else date_debut
    date_fin = entry['e.date_fin']
    year_fin = date_fin.year if date_fin else date_fin
    rows.append([nom, year_naissance, year_debut, year_fin])
df = pd.DataFrame(rows, columns=['nom', 'year_naissance', 'year_debut', 'year_fin'])

# --- Tous les agents de change MOINS ceux ayant au moins 1 agent de change dans leur famille
df_other = df[~df['nom'].isin(df_fam['nom'])]
df_other_yn = df_other.dropna(subset=['year_naissance']) # Suppression des valeurs 'None' dans la colonne "date_naissance"


st.markdown("""
            ## 3. Statistiques sur les durées de charge
            Cette page regroupe l'ensemble des statistiques issues des données temporelles de la base de données.
            Il s'agit pour l'essentiel de :
            - la date de **naissance** des individus
            - leur date de **début d'exercice**
            - leur date de **sortie d'exercice**
            
            Ces données sont ensuite croisées avec le tissu familial : aïeuls, père, mère, frère, oncle, etc.
            """)

st.warning("""Les requêtes utilisées pour la récupération des données de cette page sont disponibles en bas de page.
         """,
         icon="⚠️")



st.markdown("#### Distribution des âges des agents de change")

# ******************************
# 3A Histogramme : distribution des âges entrée charge
# ******************************

df_yn = df.dropna(subset=['year_naissance'])
df_yn["age_charge"] = df_yn['year_debut'] - df_yn['year_naissance']

# --- Paramètres du graph
bins_start = 15
bins_end = 70
bins_size = 5

# --- Construction d'un histogramme pour constituer les infos affichées lors du survole de la souris
bins = list(range(bins_start, bins_end, bins_size))
hist_data, bin_edges = np.histogram(df_yn['age_charge'], bins=bins) # calcul de la distribution des âges pour l'histogramme

binned_data = []
for i in range(len(bin_edges) - 1):
    bin_mask = (df_yn['age_charge'] >= bin_edges[i]) & (df_yn['age_charge'] < bin_edges[i+1])
    binned_data.append(df_yn['age_charge'][bin_mask])

hover_text = ["<br>".join([f"{df_yn.loc[id, 'nom']} : {int(bin_data[id])} ans" for id in bin_data.index]) for bin_data in binned_data]

# --- Construction du graph
fig_age_entree = go.Figure()
fig_age_entree.add_trace(go.Histogram(
    x=df_yn['age_charge'],
    name='Agents de change',
    opacity=1,
    marker=dict(color=px.colors.qualitative.Set2[7]),
    xbins=dict(start=bins_start, end=bins_end, size=bins_size),
    hovertext=hover_text,
    hoverinfo='text'
))

fig_age_entree.update_layout(
    # title_text='Distribution des âges au moment de l\'entrée en charge sur l\'ensemble des agents de change (1815-1852)',
    xaxis_title_text='Âge au moment de l\'entrée en charge',
    title="Graphique 3.A. : Distribution des âges au moment de l'entrée en charge sur l'ensemble des agents de change",
    yaxis_title_text='Nombre des agents de change',
    height=500
)

graph_tab, df_tab = st.tabs(["Graphique", "Données d'origine (dataframe)"])
with graph_tab:
    st.plotly_chart(fig_age_entree, use_container_width=True)
with df_tab:
    st.write(df_yn)

st.markdown(f"""Ce graphique résume la distribution des âges au moment de l'entrée en charge des agents de change.
            Sur notre population totale de {len(df)} individus, nous pouvons constituer un échantillon de **{len(df_yn)}**
            individus dont nous connaissons la naissance. Cet échantillon est constitué à partir de la Requête générale (voir plus bas)
            à laquelle nous avons retranché les individus pour lesquels la date de naissance est manquante.
            """)

# ******************************
# 3B Histogramme : distribution des âges entrée charge, DEUX GROUPES
# ******************************
st.markdown("---")
st.markdown("##### Distribution de la probabilité des âges")

# ---  Calcul des ages au moment de l'entrée en charge
df_fam_yn['age_debut'] = df_fam_yn['year_debut'] - df_fam_yn['year_naissance']
df_other_yn['age_debut'] = df_other_yn['year_debut'] - df_other_yn['year_naissance']

# --- Construction du graph
fig_dble = go.Figure()

fig_dble.add_trace(go.Histogram(
    x=df_fam_yn['age_debut'],
    name='Agents ayant un<br>agent de change dans<br>leur famille proche',
    opacity=0.75,
    marker=dict(color=px.colors.qualitative.Dark2[0]),
    autobinx=False,
    xbins=dict(size=5)
))

fig_dble.add_trace(go.Histogram(
    x=df_other_yn['age_debut'],
    name='Reste de la<br>population',
    opacity=0.5,
    marker=dict(color=px.colors.qualitative.Dark2[1]),
    autobinx=False,
    xbins=dict(size=5)
))

fig_dble.update_traces(histnorm='probability density') # Normalisation de l'histogramme (probability density function)

# Set layout details
fig_dble.update_layout(
    barmode='overlay',
    title_text="Graphique 3.B. : Distribution de la probabilité des âges au moment de l'entrée en charge, séparation en deux groupes",
    xaxis_title_text="Âge au moment de l'entrée en charge",
    xaxis_range=[15, 70],
    yaxis_title_text='Densité de probabilité',
    yaxis_range=[0, 0.06],
    bargap=0,
    height=500
)

st.plotly_chart(fig_dble, use_container_width=True)
# --- Interprétation
st.markdown(f"""
        Notre échantillon est constitué de **{len(df_fam)} individus**. Autrement dit, {len(df_fam)} agents de change ont au moins un membre
        de leur famille qui est ou a été agent de change. Le reste des agents de change, c'est à dire la population totale
        (**{len(df)}**) retranchée de notre premier échantillon, est de **{len(df_other)}**.\n
        Puisque la différence dans les effectifs est très importantes (quasiment multipliée par 10) nous avons choisi d'opérer une
        **normalisation des histogrammes**. Elle permet de les rendre comparables entre eux et évite que l'échantillon le plus faible
        soit écrasé par le reste de la population statistique.
        """)

# ******************************
# Bonus Histogramme : distribution des âges des 30 agents de change en fonction de l'année
# ******************************

with st.expander("Graphique bonus : Distribution des âges des agents de change en exercice avec choix de l'année"):
    first_year = 1803
    last_year = 1862

    # df_yn = df.dropna(subset=['year_naissance'])
    # df_yn["age_charge"] = df_yn['year_debut'] - df_yn['year_naissance']

    df_yc = df_yn.copy()

    # Calcul de l'age pour chaque année
    for year in range(first_year, last_year + 1):
        df_yn[f'age_{year}'] = year - df_yn['year_naissance']

    for year in range(first_year, last_year + 1):
        df_yc[f'age_{year}'] = year - df_yc['year_debut']


    year = st.slider("Sélection de l'année", min_value=first_year, max_value=last_year, value=1830)

    # Filtrer pour ne conserver que les personnes dont "year_début" <= 1830 et "year_fin" >= 1830
    df_year = df_yn[(df_yn['year_debut'] <= year) & (df_yn['year_fin'] >= year)]

    bins = list(range(20, 90, 5))
    # Calculer la distribution des âges pour l'histogramme
    hist_data, bin_edges = np.histogram(df_year[f'age_{year}'], bins=bins) # calcul de la distribution des âges pour l'histogramme

    # Créer un histogramme avec plotly
    fig = go.Figure(data=[go.Bar(x=[(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(bin_edges)-1)],
                                y=hist_data,
                                width=np.diff(bin_edges),
                                marker=dict(color=px.colors.qualitative.Vivid[9]))])

    # Configuration de l'affichage
    fig.update_layout(title=f"Distribution des âges en {year} - {len(df_year)} en exercice",
                    xaxis_title='Âge',
                    yaxis_title='Nombre des agents de change',
                    xaxis={'tickvals': bins},
                    yaxis_range=[0,8],
                    bargap=0,
                    height=500)

    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"""Ce graphique permet l'exploration de la distribution des âge des agents de change par année.""")


# ******************************
# 3C Histogramme : moyenne des durées de charge par année
# ******************************
st.markdown("---")
st.markdown("#### Moyennes des durées d'exercice par année")

# Recalcul des moyennes avec les bonnes colonnes
moyennes = {}
moyennes_fam = {}
moyennes_other = {}

for year in range(1815, 1862):
    # Filtrage des individus dont l'année est comprise entre year_debut et year_fin
    df_filtered = df[(df['year_debut'] <= year) & (df['year_fin'].fillna(float('inf')) >= year)]
    df_filtered_fam = df_fam[(df_fam['year_debut'] <= year) & (df_fam['year_fin'].fillna(float('inf')) >= year)]
    df_filtered_other = df_other[(df_other['year_debut'] <= year) & (df_other['year_fin'].fillna(float('inf')) >= year)]

    # Calcule la durée de charge pour ces individus
    df_filtered['duration'] = year - df_filtered['year_debut']
    df_filtered_fam['duration'] = year - df_filtered_fam['year_debut']
    df_filtered_other['duration'] = year - df_filtered_other['year_debut']
    
    # Calcul de la moyenne de la durée de charge pour cette année
    moyennes[year] = df_filtered['duration'].mean()
    moyennes_fam[year] = df_filtered_fam['duration'].mean()
    moyennes_other[year] = df_filtered_other['duration'].mean()

# Convertion en df
df_moyennes = pd.DataFrame(list(moyennes.items()), columns=['Year', 'Average Duration'])
df_moyennes_fam = pd.DataFrame(list(moyennes_fam.items()), columns=['Year', 'Average Duration Fam'])
df_moyennes_other = pd.DataFrame(list(moyennes_other.items()), columns=['Year', 'Average Duration Other'])

fig_moy_year = go.Figure()
# Moyennes générales
fig_moy_year.add_trace(go.Scatter(x=df_moyennes['Year'], y=df_moyennes['Average Duration'],
                         mode='lines', name='Population entière'))
# Moyennes fam
fig_moy_year.add_trace(go.Scatter(x=df_moyennes_fam['Year'], y=df_moyennes_fam['Average Duration Fam'],
                         mode='lines', name='Échantillon'))

# Configuration 
fig_moy_year.update_layout(title="Graphique 3.C. : Moyennes des durées d'exercice par année",
                  xaxis_title='Années',
                  yaxis_title="Moyennes des durées d'exercice",
                  hovermode='x unified',
                  yaxis=dict(range=[0, 21]),
                  height=500)
st.plotly_chart(fig_moy_year, use_container_width=True)

st.markdown("""
            Ce graphique représente la moyenne des durées d'exercice des agents de change par année.
            """)




with st.expander("Requête générale"):
    st.code(query, language="cypher", line_numbers=True)

with st.expander("Requête des agents de change ayant un agent de change dans leur famille"):
    st.code(query_fam, language="cypher", line_numbers=True)