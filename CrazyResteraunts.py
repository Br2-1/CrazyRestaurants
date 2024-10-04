import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# Inizializzazione dei dati
if 'data' not in st.session_state:
    if os.path.exists("group_restaurant_data.json"):
        with open("group_restaurant_data.json", "r") as f:
            st.session_state['data'] = json.load(f)
    else:
        st.session_state['data'] = {}

# Funzione per salvare i dati in un file JSON
def save_data():
    with open("group_restaurant_data.json", "w") as f:
        json.dump(st.session_state['data'], f, indent=4)

# Funzione per creare un gruppo di amici
def create_group(group_name, members):
    if group_name not in st.session_state['data']:
        st.session_state['data'][group_name] = {'members': members, 'restaurants': {}}
        save_data()
        st.success(f"Gruppo '{group_name}' creato con successo!")
    else:
        st.warning(f"Il gruppo '{group_name}' esiste già.")

# Funzione per aggiungere un ristorante a un gruppo
def add_restaurant_to_group(group_name, restaurant_name, lat, lon):
    group_data = st.session_state['data'][group_name]
    if restaurant_name not in group_data['restaurants']:
        group_data['restaurants'][restaurant_name] = {'lat': lat, 'lon': lon, 'reviews': []}
        save_data()
        st.success(f"Ristorante '{restaurant_name}' aggiunto al gruppo '{group_name}'!")
    else:
        st.warning(f"Il ristorante '{restaurant_name}' esiste già nel gruppo '{group_name}'.")

# Funzione per votare un ristorante in un gruppo
def vote_restaurant(group_name, restaurant_name, reviewer, votes, comments):
    group_data = st.session_state['data'][group_name]
    restaurant_data = group_data['restaurants'][restaurant_name]

    # Cerca se il recensore ha già votato questo ristorante
    found = False
    for review in restaurant_data['reviews']:
        if review['reviewer'] == reviewer:
            review['votes'] = votes
            review['comments'] = comments
            found = True
            break

    if not found:
        restaurant_data['reviews'].append({'reviewer': reviewer, 'votes': votes, 'comments': comments, 'comment_votes': 0})

    save_data()
    st.success(f"Votazione aggiornata per {restaurant_name} da {reviewer}!")

# Funzione per votare un commento
def vote_comment(group_name, restaurant_name, reviewer_name):
    restaurant_data = st.session_state['data'][group_name]['restaurants'][restaurant_name]
    
    # Visualizza i commenti lasciati dagli altri amici
    comments_list = [f"{review['reviewer']}: {review['comments']}" for review in restaurant_data['reviews'] if review['comments']]
    selected_comment = st.selectbox("Seleziona un commento da votare", comments_list)
    
    if selected_comment and st.button("Vota commento"):
        for review in restaurant_data['reviews']:
            if f"{review['reviewer']}: {review['comments']}" == selected_comment and reviewer_name != review['reviewer']:
                review['comment_votes'] += 1
                st.success("Hai votato questo commento!")
                save_data()
                break

# Funzione per ottenere il commento con più voti
def get_top_comment(reviews):
    top_comment = None
    max_votes = -1
    for review in reviews:
        if review['comment_votes'] > max_votes:
            top_comment = review['comments']
            max_votes = review['comment_votes']
    return top_comment

# Funzione per creare lo spider plot
def create_spider_plot(data, categories, restaurant_name, top_comment=None):
    fig = go.Figure()
    for person, scores in data.items():
        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=categories,
            fill='toself',
            name=person
        ))
    
    # Aggiungi il commento più votato come annotazione
    if top_comment:
        fig.add_annotation(
            text=f"Commento più votato: {top_comment}",
            xref="paper", yref="paper",
            x=0.5, y=1.1, showarrow=False,
            font=dict(size=12, color="black"),
            align="center"
        )
    
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

# Sezione per creare un nuovo gruppo di amici
st.header("Crea un gruppo di amici")
group_name = st.text_input("Nome del gruppo")
group_members = st.text_area("Inserisci i nomi degli amici separati da virgole").split(',')

if st.button("Crea gruppo"):
    create_group(group_name, group_members)

# Sezione per aggiungere un ristorante a un gruppo
st.header("Aggiungi un ristorante a un gruppo")
group_list = list(st.session_state['data'].keys())
selected_group = st.selectbox("Seleziona un gruppo", group_list)

restaurant_name = st.text_input("Nome del ristorante")
latitude = st.number_input("Latitudine", format="%.6f")
longitude = st.number_input("Longitudine", format="%.6f")

if st.button("Aggiungi ristorante"):
    add_restaurant_to_group(selected_group, restaurant_name, latitude, longitude)

# Sezione per votare un ristorante
st.header("Vota un ristorante")
selected_group = st.selectbox("Seleziona un gruppo per votare", group_list)
if selected_group:
    restaurants_list = list(st.session_state['data'][selected_group]['restaurants'].keys())
    selected_restaurant = st.selectbox("Seleziona un ristorante", restaurants_list)

    reviewer = st.text_input("Inserisci il tuo nome")
    categories = ['Prezzo', 'Qualità', 'Servizio', 'Location']
    votes = [st.slider(f"{category} (0-10)", 0, 10, 5) for category in categories]
    comment = st.text_area("Commento (opzionale)")

    if st.button("Aggiungi Voto"):
        vote_restaurant(selected_group, selected_restaurant, reviewer, votes, comment)

# Sezione per votare il miglior commento
st.header("Vota il miglior commento")
selected_group_for_comment = st.selectbox("Seleziona un gruppo per votare i commenti", group_list)
if selected_group_for_comment:
    restaurants_list = list(st.session_state['data'][selected_group_for_comment]['restaurants'].keys())
    selected_restaurant_for_comment = st.selectbox("Seleziona un ristorante per votare i commenti", restaurants_list)

    if selected_restaurant_for_comment:
        reviewer_name = st.text_input("Inserisci il tuo nome per votare")
        vote_comment(selected_group_for_comment, selected_restaurant_for_comment, reviewer_name)

# Sezione per visualizzare lo spider plot di un ristorante
st.header("Visualizza Spider Plot di un Ristorante")
selected_group = st.selectbox("Seleziona un gruppo per visualizzare", group_list)
if selected_group:
    restaurants_list = list(st.session_state['data'][selected_group]['restaurants'].keys())
    selected_restaurant_for_plot = st.selectbox("Seleziona ristorante per visualizzare lo spider plot", restaurants_list)

    if selected_restaurant_for_plot:
        reviews = st.session_state['data'][selected_group]['restaurants'][selected_restaurant_for_plot]['reviews']
        if reviews:
            plot_data = {review['reviewer']: review['votes'] for review in reviews}
            top_comment = get_top_comment(reviews)
            spider_fig = create_spider_plot(plot_data, categories, selected_restaurant_for_plot, top_comment)
            st.plotly_chart(spider_fig)
        else:
            st.warning(f"Nessuna votazione per {selected_restaurant_for_plot}.")

# Funzione per confrontare i ristoranti
# Funzione per calcolare il total score per un ristorante
def calculate_total_score(reviews):
    total_score = sum([sum(review['votes']) for review in reviews])
    return total_score

# Funzione per confrontare i ristoranti, aggiungendo il total score
def compare_restaurants(group_name, restaurant_names):
    categories = ['Prezzo', 'Qualità', 'Servizio', 'Location']
    fig = go.Figure()

    for restaurant in restaurant_names:
        reviews = st.session_state['data'][group_name]['restaurants'][restaurant]['reviews']
        if reviews:
            # Calcolo la media dei voti per ciascuna categoria
            avg_scores = [sum([review['votes'][i] for review in reviews]) / len(reviews) for i in range(4)]
            total_score = calculate_total_score(reviews)  # Calcola il total score
            fig.add_trace(go.Bar(
                x=categories,
                y=avg_scores,
                name=f"{restaurant} (Total Score: {total_score})"  # Aggiungi il Total Score nel nome del ristorante
            ))

    fig.update_layout(
        barmode='group',
        title="Confronto dei ristoranti (con Total Score)"
    )
    return fig

# Sezione per confrontare i ristoranti
st.header("Confronta Ristoranti")
selected_group = st.selectbox("Seleziona un gruppo per confrontare", group_list)
if selected_group:
    restaurants_list = list(st.session_state['data'][selected_group]['restaurants'].keys())
    selected_restaurants_for_comparison = st.multiselect("Seleziona ristoranti da confrontare", restaurants_list)

    if selected_restaurants_for_comparison:
        comparison_fig = compare_restaurants(selected_group, selected_restaurants_for_comparison)
        st.plotly_chart(comparison_fig)

# Sezione per visualizzare la mappa
st.header("Visualizza mappa dei ristoranti")
if selected_group:
    map_data = pd.DataFrame({
        'lat': [st.session_state['data'][selected_group]['restaurants'][r]['lat'] for r in restaurants_list],
        'lon': [st.session_state['data'][selected_group]['restaurants'][r]['lon'] for r in restaurants_list],
        'name': restaurants_list,
        'total_score': [calculate_total_score(st.session_state['data'][selected_group]['restaurants'][r]['reviews']) for r in restaurants_list],  # Total score per ristorante
        'top_comment': [get_top_comment(st.session_state['data'][selected_group]['restaurants'][r]['reviews']) for r in restaurants_list]
    })

    if not map_data.empty:
        fig_map = px.scatter_mapbox(
            map_data, 
            lat="lat", 
            lon="lon", 
            hover_name="name", 
            hover_data=["total_score", "top_comment"],  # Aggiungi total_score nei dati hover
            zoom=10
        )
        fig_map.update_layout(mapbox_style="open-street-map")
        st.plotly_chart(fig_map)


