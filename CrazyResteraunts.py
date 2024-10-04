import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from geopy.geocoders import Nominatim

# Inizializzazione dei dati
# Simuliamo una base dati iniziale
if 'restaurants' not in st.session_state:
    st.session_state['restaurants'] = {}

# Funzione per creare uno spider plot
def create_spider_plot(data, categories, restaurant_name):
    fig = go.Figure()
    for person, scores in data.items():
        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=categories,
            fill='toself',
            name=person
        ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )),
        showlegend=True,
        title=f"Spider Plot per {restaurant_name}"
    )
    return fig

# Funzione per aggiungere un nuovo ristorante
def add_restaurant(name, lat, lon):
    if name not in st.session_state['restaurants']:
        st.session_state['restaurants'][name] = {'lat': lat, 'lon': lon, 'reviews': []}
        st.success(f"Ristorante '{name}' aggiunto con successo!")

# Sezione per aggiungere un nuovo ristorante
st.header("Aggiungi un nuovo ristorante")

# Inserisci il nome del ristorante e le coordinate (latitudine, longitudine)
restaurant_name = st.text_input("Nome del ristorante")
latitude = st.number_input("Latitudine", format="%.6f")
longitude = st.number_input("Longitudine", format="%.6f")

# Bottone per aggiungere il ristorante
if st.button("Aggiungi ristorante"):
    add_restaurant(restaurant_name, latitude, longitude)

# Funzione per votare un ristorante
def vote_restaurant(restaurant_name, reviewer, votes, comments):
    st.session_state['restaurants'][restaurant_name]['reviews'].append(
        {'reviewer': reviewer, 'votes': votes, 'comments': comments}
    )
    st.success(f"Votazione aggiunta per {restaurant_name} da {reviewer}!")

# Sezione per votare un ristorante
st.header("Vota un ristorante")

# Seleziona un ristorante tra quelli aggiunti
restaurants_list = list(st.session_state['restaurants'].keys())
selected_restaurant = st.selectbox("Seleziona un ristorante", restaurants_list)

# Nome del recensore
reviewer = st.text_input("Inserisci il tuo nome")

# Inserimento voti per ciascuna categoria
categories = ['Prezzo', 'Qualità', 'Servizio', 'Location']
votes = []
for category in categories:
    votes.append(st.slider(f"{category} (0-10)", min_value=0, max_value=10, value=5))

# Commento opzionale
comment = st.text_area("Commento (opzionale)")

# Bottone per aggiungere il voto
if st.button("Aggiungi Voto"):
    vote_restaurant(selected_restaurant, reviewer, votes, comment)

# Sezione per visualizzare lo spider plot di un ristorante
st.header("Visualizza Spider Plot di un Ristorante")

selected_restaurant_for_plot = st.selectbox("Seleziona ristorante per visualizzare lo spider plot", restaurants_list)

if selected_restaurant_for_plot:
    # Prepara i dati per lo spider plot
    reviews = st.session_state['restaurants'][selected_restaurant_for_plot]['reviews']
    if reviews:
        plot_data = {review['reviewer']: review['votes'] for review in reviews}
        spider_fig = create_spider_plot(plot_data, categories, selected_restaurant_for_plot)
        st.plotly_chart(spider_fig)
    else:
        st.warning(f"Nessuna votazione per {selected_restaurant_for_plot}.")

# Funzione per confrontare ristoranti
def compare_restaurants(restaurant_names):
    fig = go.Figure()
    for restaurant in restaurant_names:
        reviews = st.session_state['restaurants'][restaurant]['reviews']
        if reviews:
            # Calcola la media dei voti per ristorante
            avg_scores = [sum([review['votes'][i] for review in reviews]) / len(reviews) for i in range(4)]
            fig.add_trace(go.Bar(
                x=categories,
                y=avg_scores,
                name=restaurant
            ))
    fig.update_layout(
        barmode='group',
        title="Confronto dei ristoranti"
    )
    return fig

# Sezione per confrontare ristoranti
st.header("Confronta Ristoranti")

# Seleziona due o più ristoranti per il confronto
selected_restaurants_for_comparison = st.multiselect("Seleziona ristoranti da confrontare", restaurants_list)

if selected_restaurants_for_comparison:
    comparison_fig = compare_restaurants(selected_restaurants_for_comparison)
    st.plotly_chart(comparison_fig)

# Sezione per visualizzare la mappa (placeholder)
st.header("Visualizza mappa dei ristoranti")

# Utilizzo di plotly per mostrare i ristoranti su una mappa
map_data = pd.DataFrame({
    'lat': [st.session_state['restaurants'][r]['lat'] for r in restaurants_list],
    'lon': [st.session_state['restaurants'][r]['lon'] for r in restaurants_list],
    'name': restaurants_list
})

if not map_data.empty:
    fig_map = px.scatter_mapbox(map_data, lat="lat", lon="lon", hover_name="name", zoom=10)
    fig_map.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig_map)
