from neo4j import GraphDatabase
from unidecode import unidecode
import streamlit as st

# Case : fonctionnement en local
try:
    from credentials import *
    URI = AURA_CONNECTION_URI
    USER = AURA_USERNAME
    PASS = AURA_PASSWORD
except:
    pass

# Case : fonctionnement APP streamlit
try:
    URI = st.secrets["AURA_CONNECTION_URI"]
    USER = st.secrets["AURA_USERNAME"]
    PASS = st.secrets["AURA_PASSWORD"]
except:
    pass

def get_neo4j_results_of(query):
    # Driver instantiation
    driver = GraphDatabase.driver(URI, auth=(USER, PASS))

    # Create a driver session
    with driver.session() as session:
        # Use .data() to access the results array
        results = session.run(query)
        results_data = results.data()
        return(results_data)
    driver.close()

def simple_comparison(exp_in, base_exp):
    chars_to_del = " -()\'"
    def essentialize_str(word):
        word = word.strip()
        word = unidecode(word)
        word = word.lower()
        for char in chars_to_del:
            word = word.replace(char, "")
        return word

    exp_in = essentialize_str(exp_in)
    base_exp = essentialize_str(base_exp)

    if exp_in == base_exp:
        return exp_in, base_exp

def h_in_db(candidate): 
    fullnames = []
    names = []

    for record in results_data:
        fullname = record["h"]["nom"]
        name = fullname.split(",")[0].strip()

        fullnames.append(fullname)
        names.append(name)
    
    names = list(dict.fromkeys(names))
    fullnames = list(dict.fromkeys(fullnames))

    results = []
    for name in names:
        if simple_comparison(name, candidate):
            results.append(simple_comparison(name, candidate))
    if results:
        return results

