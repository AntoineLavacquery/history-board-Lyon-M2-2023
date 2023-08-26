import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import numpy as np
from streamlit_extras.mention import mention

from neo4jtools import *
from Accueil import page_config_params, make_sidebar_foot

st.set_page_config(**page_config_params)
make_sidebar_foot("https://github.com/AntoineLavacquery/history-board-Lyon-M2-2023")


st.markdown("""
            ## Statistiques sur les durées de charge
            Cette page regroupe l'ensemble des statistiques issues des données temporelles de la base de données.
            Il s'agit pour l'essentiel de :
            - la date de **naissance** des individus
            - leur date d'**entrée en charge**
            - leur date de **sortie de charge**
            
            Ces données sont ensuite croisées avec les relations existants entre les individus :
            - liens familiaux (père, frère, oncle, etc.)

            #### Distribution des âges au moment de l\'entrée en charge sur l\'ensemble des agents de change (1815-1852)
        
            """)

# ******************************
# Requêtes vers la base de données
# ******************************

# --- Agents de change ayant un agent de change dans leur famille proche
query_fam = """
MATCH (h:HOMME)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'}),
(gp)-[ad:`AÏEUL_DE`]->(h), (gp)-[:EXERCE]->(a)
RETURN h, e.date_début, e.date_fin
UNION
MATCH (h:HOMME)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'}),
(p)-[pd:PÈRE_DE]->(h), (p)-[:EXERCE]->(a)
RETURN h, e.date_début, e.date_fin
UNION
MATCH (h:HOMME)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'}),
(f)-[fd:FRÈRE_DE]-(h), (f)-[:EXERCE]->(a)
RETURN h, e.date_début, e.date_fin
UNION
MATCH (h:HOMME)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'}),
(o)-[od:ONCLE_DE]->(h), (o)-[:EXERCE]->(a)
RETURN h, e.date_début, e.date_fin

UNION

MATCH (h:HOMME)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'}),
(f)-[:MARIAGE]-(h),
(gpf)-[adf:`AÏEUL_DE`]->(f), (gpf)-[:EXERCE]->(a)
RETURN h, e.date_début, e.date_fin
UNION
MATCH (h:HOMME)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'}),
(f)-[:MARIAGE]-(h),
(pf)-[pdf:`PÈRE_DE`]->(f), (pf)-[:EXERCE]->(a)
RETURN h, e.date_début, e.date_fin
UNION
MATCH (h:HOMME)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'}),
(f)-[:MARIAGE]-(h),
(ff)-[fdf:`FRÈRE_DE`]-(f), (ff)-[:EXERCE]->(a)
RETURN h, e.date_début, e.date_fin
UNION
MATCH (h:HOMME)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'}),
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


# --- Tous les agents de change entre 1815 et 1852
query = """
MATCH (h:HOMME)-[e:EXERCE]->(a:ACTIVITÉ {nom:'Agent de change'})
WHERE (e.date_début.year >= 1815 AND e.date_début.year <= 1852)
OR (e.date_fin.year >= 1815 AND e.date_fin.year <= 1852)
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


# ******************************
# Histogramme : moyenne des durées de charge par année
# ******************************

# Recalcul des moyennes avec les bonnes colonnes
moyennes = {}
moyennes_fam = {}
moyennes_other = {}

# Pour chaque année de 1815 à 1852
for year in range(1815, 1853):
    # Filtrer les individus dont l'année est comprise entre year_debut et year_fin
    df_filtered = df[(df['year_debut'] <= year) & (df['year_fin'].fillna(float('inf')) >= year)]
    df_filtered_fam = df_fam[(df_fam['year_debut'] <= year) & (df_fam['year_fin'].fillna(float('inf')) >= year)]
    df_filtered_other = df_other[(df_other['year_debut'] <= year) & (df_other['year_fin'].fillna(float('inf')) >= year)]

    # Calculer la durée de charge pour ces individus
    df_filtered['duration'] = year - df_filtered['year_debut']
    df_filtered_fam['duration'] = year - df_filtered_fam['year_debut']
    df_filtered_other['duration'] = year - df_filtered_other['year_debut']
    
    # Calculer la moyenne de la durée de charge pour cette année
    moyenne = df_filtered['duration'].mean()
    moyenne_fam = df_filtered_fam['duration'].mean()
    moyenne_other = df_filtered_other['duration'].mean()

    moyennes[year] = moyenne
    moyennes_fam[year] = moyenne_fam
    moyennes_other[year] = moyenne_other

# Convertir le dictionnaire en DataFrame pour la visualisation
df_moyennes = pd.DataFrame(list(moyennes.items()), columns=['Year', 'Average Duration'])
df_moyennes_fam = pd.DataFrame(list(moyennes_fam.items()), columns=['Year', 'Average Duration Fam'])
df_moyennes_other = pd.DataFrame(list(moyennes_other.items()), columns=['Year', 'Average Duration Other'])


# Création du graphique
figg = go.Figure()

# Ajout de la première série
figg.add_trace(go.Scatter(x=df_moyennes['Year'], y=df_moyennes['Average Duration'],
                         mode='lines', name='Average Duration'))

# Ajout de la seconde série
figg.add_trace(go.Scatter(x=df_moyennes_fam['Year'], y=df_moyennes_fam['Average Duration Fam'],
                         mode='lines', name='Average Duration Fam'))

# Ajout de la troisème série
figg.add_trace(go.Scatter(x=df_moyennes_other['Year'], y=df_moyennes_other['Average Duration Other'],
                         mode='lines', name='Average Duration Other'))

# Configuration du titre et des axes
figg.update_layout(title='Moyenne des Durées de Charge par Année',
                  xaxis_title='Year',
                  yaxis_title='Average Duration',
                  hovermode='x unified')


st.plotly_chart(figg, use_container_width=True)


# ******************************
# Histogramme : distribution des âges entrée charge 1815 1852
# ******************************

# TODO: Ajouter une vérification des données d'entrée
# FIXME: Cette fonction ne renvoie pas la bonne valeur pour les entrées négatives

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
fig3 = go.Figure()
fig3.add_trace(go.Histogram(
    x=df_yn['age_charge'],
    name='Agents de change',
    opacity=1,
    marker=dict(color=px.colors.qualitative.Dark2[2]),
    xbins=dict(start=bins_start, end=bins_end, size=bins_size),
    hovertext=hover_text,
    hoverinfo='text'
))

fig3.update_layout(
    # title_text='Distribution des âges au moment de l\'entrée en charge sur l\'ensemble des agents de change (1815-1852)',
    xaxis_title_text='Âge au moment de l\'entrée en charge',
    yaxis_title_text='Nombre des agents de change'
)

col00, col01 = st.columns([2, 1])
with col00:
    st.plotly_chart(fig3, use_container_width=True)
with col01:
    st.markdown("""On observe que bla  \nbla  \nbli  \nbla  \nbla  \nbla""")


# ******************************
# Histogramme : distribution des âges entrée charge, DEUX GROUPES
# ******************************
st.write("df_fam_yn")
st.write(len(df_fam_yn))

st.write("df_other_yn")
st.write(len(df_other_yn))

# ---  Calcul des ages au moment de l'entrée en charge
df_fam_yn['age_debut'] = df_fam_yn['year_debut'] - df_fam_yn['year_naissance']
df_other_yn['age_debut'] = df_other_yn['year_debut'] - df_other_yn['year_naissance']

# --- Construction du graph
fig_dble = go.Figure()

fig_dble.add_trace(go.Histogram(
    x=df_fam_yn['age_debut'],
    name='Agents ayant un agent de change<br>dans leur famille proche',
    opacity=0.75,
    marker=dict(color=px.colors.qualitative.Dark2[0]),
    autobinx=False,
    xbins=dict(size=5)
))

fig_dble.add_trace(go.Histogram(
    x=df_other_yn['age_debut'],
    name='Reste des agents',
    opacity=0.5,
    marker=dict(color=px.colors.qualitative.Dark2[1]),
    autobinx=False,
    xbins=dict(size=5)
))

fig_dble.update_traces(histnorm='probability density') # Normalisation de l'histogramme (probability density function)

# Set layout details
fig_dble.update_layout(
    barmode='overlay',
    title_text='Distribution de la probabilité des âges au moment de l\'entrée en charge, séparation en deux groupes',
    xaxis_title_text='Âge au moment de l\'entrée en charge',
    xaxis_range=[15, 70],
    yaxis_title_text='Densité de probabilité',
    yaxis_range=[0, 0.06],
    bargap=0,
)

col10, col11 = st.columns([1, 2])

# --- Interprétation
with col10:
    st.markdown(f"""
            {len(df_fam)} agents de change ont au moins un membre de leur famille agent de change.\n
            La normalisation des histogrammes permet de les rendre comparables alors même que l'échantillon des agents de change 
            ayant un agent de change dans leur famille proche a un effectif bien plus faible.
            """)

with col11:
    st.plotly_chart(fig_dble, use_container_width=True)



# ******************************
# Histogramme : distribution des âges des 30 agents de change en fonction de l'année
# ******************************

first_year = 1815
last_year = 1852

# df_yn = df.dropna(subset=['year_naissance'])
# df_yn["age_charge"] = df_yn['year_debut'] - df_yn['year_naissance']

df_yc = df_yn.copy()

# Calcul de l'age pour chaque année
for year in range(first_year, last_year + 1):
    df_yn[f'age_{year}'] = year - df_yn['year_naissance']

for year in range(first_year, last_year + 1):
    df_yc[f'age_{year}'] = year - df_yc['year_debut']

col20, col21 = st.columns([2, 1])
# Slider de définition de l'année
with col20:
    year = st.slider("Sélection de l'année", min_value=1815, max_value=1852, value=1830)

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
fig.update_layout(title=f'Distribution des âges en {year}',
                  xaxis_title='Âge',
                  yaxis_title='Nombre des agents de change',
                  xaxis={'tickvals': bins},
                  yaxis_range=[0,8],
                  bargap=0,
                  width=1000,
                  height=500)


with col21:
    cola, colb, colc = st.columns(3)
    cola.metric(label="Nombre des agents de change", value=f"{len(df)}")
    colb.metric("Ceux dont nous connaissons la naissance", value=f"{len(df_yn)}")
    colc.metric(f"Dont en charge en {year}", f"{len(df_year)}")

st.plotly_chart(fig, use_container_width=True)

st.divider() # ------------------------------

df_yc_org = df_yc.copy()

year2 = st.slider("XSélection de l'année", min_value=1815, max_value=1852, value=1830)

@st.cache(allow_output_mutation=True)
def ma_fonction(year2):
    global df_yc
    for year in range(1815, 1853):
        for year in range(1815, 1853):
            df_yc[f'duration_{year}'] = np.where(
                (df_yc['year_debut'] <= year) & (df_yc['year_fin'] >= year),
                year - df_yc['year_debut'],
                np.nan  # Mettre NaN pour les individus qui ne correspondent pas aux critères
            )


    # Sélectionnez la colonne correspondant à l'année choisie
    df_yc = df_yc[['nom', f'duration_{year2}']].dropna().sort_values(by=f'duration_{year2}')

    figz = px.bar(df_yc, 
                x=f'duration_{year2}', 
                y='nom', 
                orientation='h',
                title=f'Durée par individu en {year2}',
                labels={f'duration_{year2}': 'Durée (années)', 'nom': 'Nom'},
                height=800)

    figz.update_layout(yaxis={'categoryorder': 'total ascending'})

    st.plotly_chart(figz, use_container_width=True)

ma_fonction(year2)


# # Filtrer pour ne conserver que les personnes dont "year_début" <= 1830 et "year_fin" >= 1830
# df_yc = df_yc_org[(df_yc_org['year_debut'] <= year2) & (df_yc_org['year_fin'] >= year2)].copy()

# df_yc['duration'] = year2 - df_yc['year_debut']

# df_yc = df_yc.sort_values(by="duration")
 
# # Créer le graphique
# figz = px.bar(df_yc, 
#                 x='duration', 
#                 y='nom', 
#                 orientation='h',
#                 title=f'Durée par individu en {year2}',
#                 labels={'duration': 'Durée (années)', 'nom': 'Nom'},
#                 height=800)

# # Inverser l'axe des ordonnées pour que les durées les plus longues soient en haut
# figz.update_layout(yaxis={'categoryorder': 'total ascending'})


# # Tester la fonction avec l'année 1815
# st.plotly_chart(figz, use_container_width=True)
