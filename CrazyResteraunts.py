import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import requests
import base64
# Inizializzazione dei dati
if 'data' not in st.session_state:
    if os.path.exists("group_restaurant_data.json"):
        with open("group_restaurant_data.json", "r") as f:
            st.session_state['data'] = json.load(f)
    else:
        st.session_state['data'] = {}

# Funzione per fare un commit su GitHub
def upload_file_to_github(file_path, repo, path_in_repo, commit_message, branch="main"):
    # Inserisci il tuo token GitHub qui
    token = "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"
    url = f"https://api.github.com/repos/{repo}/contents/{path_in_repo}"

    # Carica il file da caricare
    with open(file_path, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf-8")
    
    # Ottieni le informazioni correnti del file (necessarie per aggiornare un file esistente)
    response = requests.get(url, headers={"Authorization": f"token {token}"})
    response_json = response.json()
    
    # Prepara i dati per il commit
    data = {
        "message": commit_message,
        "content": content,
        "branch": branch,
    }
    
    # Se il file esiste già, aggiungi il "sha" dell'ultimo commit
    if 'sha' in response_json:
        data["sha"] = response_json["sha"]
    
    # Esegui la richiesta PUT per aggiornare il file
    response = requests.put(url, json=data, headers={"Authorization": f"token {token}"})
    
    if response.status_code == 200 or response.status_code == 201:
        print("File uploaded successfully.")
    else:
        print(f"Error: {response.status_code} - {response.text}")


# Funzione per salvare i dati in un file JSON
def save_data():
    file_path = "group_restaurant_data.json"
    with open(file_path, "w") as f:
        json.dump(st.session_state['data'], f, indent=4)
    
    # Carica il file su GitHub
    repo = "Br2-1/CrazyRestaurants"  # Il tuo repository
    path_in_repo = "group_restaurant_data.json"
    commit_message = "Aggiornamento del file JSON"
    upload_file_to_github(file_path, repo, path_in_repo, commit_message)

# Funzione per creare un gruppo di amici
def create_group(group_name, members):
    if group_name not in st.session_state['data']:
        st.session_state['data'][group_name] = {'members': members, 'restaurants': {}}
        save_data()
        st.success(f"Group '{group_name}' successfully created!")
    else:
        st.warning(f"The group '{group_name}' already exists.")

# Funzione per aggiungere un ristorante a un gruppo
def add_restaurant_to_group(group_name, restaurant_name, lat, lon):
    group_data = st.session_state['data'][group_name]
    if restaurant_name not in group_data['restaurants']:
        group_data['restaurants'][restaurant_name] = {'lat': lat, 'lon': lon, 'reviews': []}
        save_data()
        st.success(f"Restaurant '{restaurant_name}' added to the group '{group_name}'!")
    else:
        st.warning(f"The restaurant '{restaurant_name}' already exists in the group '{group_name}'.")

# Funzione per votare un ristorante in un gruppo
def vote_restaurant(group_name, restaurant_name, reviewer, votes, comments, comment):
    group_data = st.session_state['data'][group_name]
    restaurant_data = group_data['restaurants'][restaurant_name]

    # Cerca se il recensore ha già votato questo ristorante
    found = False
    for review in restaurant_data['reviews']:
        if review['reviewer'] == reviewer:
            review['votes'] = votes
            review['comments'] = comments
            review['comment'] = comment
            found = True
            break

    if not found:
        restaurant_data['reviews'].append({'reviewer': reviewer, 'votes': votes, 'comments': comments, 'comment': comment,'comment_votes': 0})

    save_data()
    st.success(f"Updated review for {restaurant_name} by {reviewer}!")

# Funzione per votare un commento
def vote_comment(group_name, restaurant_name, reviewer_name):
    restaurant_data = st.session_state['data'][group_name]['restaurants'][restaurant_name]
    
    # Visualizza i commenti lasciati dagli altri amici
    comments_list = [f"{review['reviewer']}: {review['comment']}" for review in restaurant_data['reviews'] if review['comment']]
    selected_comment = st.selectbox("Select the best sentence", comments_list)
    
    if selected_comment and st.button("Vote Sentence"):
        for review in restaurant_data['reviews']:
            if f"{review['reviewer']}: {review['comment']}" == selected_comment:
                review['comment_votes'] += 1
                st.success("You vote this sentence!")
                save_data()
                break

# Funzione per ottenere il commento con più voti
def get_top_comment(reviews):
    top_comment = None
    max_votes = -1
    for review in reviews:
        if review['comment_votes'] > max_votes:
            top_comment = review['comment']
            max_votes = review['comment_votes']
    return top_comment

# Funzione per creare lo spider plot
def create_spider_plot(data, comments, categories, restaurant_name, top_comment=None):
    fig = go.Figure()

    # Aggiungiamo le traiettorie per ogni recensore
    for person, scores in data.items():
        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=categories,
            fill='toself',
            name=person,
            hovertext=[f"{category}: {comments[person][i]}" for i, category in enumerate(categories)],  # Mostra il commento per ogni categoria
            hoverinfo='text',  # Mostra il testo al passaggio del mouse
        ))
    
    # Aggiungi il commento più votato come annotazione (facoltativo)
    if top_comment:
        fig.add_annotation(
            text=f"Sentence of the evening: {top_comment}",
            xref="paper", yref="paper",
            x=0.5, y=-0.3, showarrow=False,
            font=dict(size=18),
            align="center"
        )
    
    # Configurazione del layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )),
        showlegend=True,
        title=f"{restaurant_name} Spider Plot",
        hovermode='closest'  # Attiva l'hover sulla traiettoria più vicina
    )
    
    return fig

# Sezione per creare un nuovo gruppo di amici
st.header("Create a new group")
group_name = st.text_input("Group's Name")
group_members = st.text_area("Insert friends name, separated by comma").split(',')

if st.button("Create Group"):
    create_group(group_name, group_members)

# Sezione per aggiungere un ristorante a un gruppo
st.header("Add a restaurant to the group")
group_list = list(st.session_state['data'].keys())
selected_group = st.selectbox("Select a group", group_list)

restaurant_name = st.text_input("Restaurant's Name")
latitude = st.number_input("Latitude", format="%.6f")
longitude = st.number_input("Longitude", format="%.6f")

if st.button("Add a restaurant"):
    add_restaurant_to_group(selected_group, restaurant_name, latitude, longitude)

# Sezione per votare un ristorante
st.header("Review the restaurant")
selected_group = st.selectbox("Select a group for the review", group_list)
if selected_group:
    restaurants_list = list(st.session_state['data'][selected_group]['restaurants'].keys())
    selected_restaurant = st.selectbox("Select a restaurant", restaurants_list)

    reviewer = st.text_input("Insert your name")
    categories = ['Price', 'Quality','Quantity', 'Service', 'Location', 'Happiness']
    votes = [st.slider(f"{category} (0-10)", 0, 10, 5) for category in categories]
    comments = [st.text_area(f"{category} Comment") for category in categories]
    comment = st.text_area("Sentence of the evening")

    if st.button("Add Review"):
        vote_restaurant(selected_group, selected_restaurant, reviewer, votes, comments, comment)

# Sezione per votare il miglior commento
st.header("Vote the best sentence of the evening")
selected_group_for_comment = st.selectbox("Select a group to vote", group_list)
if selected_group_for_comment:
    restaurants_list = list(st.session_state['data'][selected_group_for_comment]['restaurants'].keys())
    selected_restaurant_for_comment = st.selectbox("Select a restaurant to vote", restaurants_list)

    if selected_restaurant_for_comment:
        reviewer_name = st.text_input("Insert your name to vote")
        vote_comment(selected_group_for_comment, selected_restaurant_for_comment, reviewer_name)

# Sezione per visualizzare lo spider plot di un ristorante
st.header("Visualize Reviews of a Restaurant")
selected_group = st.selectbox("Select a group for the visualization", group_list)
if selected_group:
    restaurants_list = list(st.session_state['data'][selected_group]['restaurants'].keys())
    selected_restaurant_for_plot = st.selectbox("Select a restaurant to visualize the reviews", restaurants_list)

    if selected_restaurant_for_plot:
        reviews = st.session_state['data'][selected_group]['restaurants'][selected_restaurant_for_plot]['reviews']
        if reviews:
            plot_data = {review['reviewer']: review['votes'] for review in reviews}
            write_data = {review['reviewer']: review['comments'] for review in reviews}
            top_comment = get_top_comment(reviews)
            spider_fig = create_spider_plot(plot_data,write_data, categories, selected_restaurant_for_plot, top_comment)
            st.plotly_chart(spider_fig)
        else:
            st.warning(f"Zero reviews for {selected_restaurant_for_plot}.")

# Funzione per confrontare i ristoranti
# Funzione per calcolare il total score per un ristorante
def calculate_total_score(reviews, categories):
    if not reviews:
        return 0

    # Sommiamo tutti i voti, separati per categorie
    num_categories = len(categories)  # Numero di categorie (supponendo che tutte le review abbiano lo stesso numero di voti)
    
    # Somma dei voti per ogni categoria
    total_score = sum([sum(review['votes']) for review in reviews])
    
    # Calcoliamo il numero totale di voti (numero di recensioni * numero di categorie)
    total_votes = len(reviews) * num_categories
    
    # Calcoliamo la media su tutte le categorie e recensioni
    average_score = total_score / total_votes
    
    # Moltiplichiamo la media per 100
    total_score_scaled = average_score * 10

    return total_score_scaled

# Funzione per confrontare i ristoranti, aggiungendo il total score
import plotly.graph_objs as go

def compare_restaurants(group_name, categories, restaurant_names):
    # Crea una nuova figura
    fig = go.Figure()

    for restaurant in restaurant_names:
        reviews = st.session_state['data'][group_name]['restaurants'][restaurant]['reviews']
        if reviews:
            # Calcola la media dei voti per ciascuna categoria
            avg_scores = [sum([review['votes'][i] for review in reviews]) / len(reviews) for i in range(len(categories))]
            total_score = calculate_total_score(reviews, categories)  # Calcola il total score
            
            # Crea i commenti per ogni categoria raggruppati per recensore
            hover_texts = []
            for i, category in enumerate(categories):
                comments_by_person = [f"{review['reviewer']}: {review['comments'][i]}" for review in reviews]
                hover_text = "<br>".join(comments_by_person)  # Commenti separati da una nuova riga
                hover_texts.append(hover_text)
            
            # Aggiungi il tracciato della barra per il ristorante
            fig.add_trace(go.Bar(
                x=categories,
                y=avg_scores,
                name=f"{restaurant} (Total Score: {total_score:.3f})",  # Aggiungi il Total Score nel nome del ristorante
                hovertext=hover_texts,  # Aggiungi il testo dell'hover personalizzato
                hoverinfo='text'  # Mostra il testo personalizzato nell'hover
            ))

    # Configura il layout del grafico
    fig.update_layout(
        barmode='group',
        title="Restaurants Comparison",
        xaxis_title="Categories",
        yaxis_title="Average Scores"
    )

    return fig


# Sezione per confrontare i ristoranti
st.header("Compare Restaurants")
selected_group = st.selectbox("Select the group for the comparisonr", group_list)
if selected_group:
    restaurants_list = list(st.session_state['data'][selected_group]['restaurants'].keys())
    selected_restaurants_for_comparison = st.multiselect("Select the restaurants to compare", restaurants_list)

    if selected_restaurants_for_comparison:
        comparison_fig = compare_restaurants(selected_group, categories, selected_restaurants_for_comparison)
        st.plotly_chart(comparison_fig)



st.header("Restaurants Map Visualization")
if selected_group:
    map_data = pd.DataFrame({
        'lat': [st.session_state['data'][selected_group]['restaurants'][r]['lat'] for r in restaurants_list],
        'lon': [st.session_state['data'][selected_group]['restaurants'][r]['lon'] for r in restaurants_list],
        'name': restaurants_list,
        'total_score': [calculate_total_score(st.session_state['data'][selected_group]['restaurants'][r]['reviews'], categories) for r in restaurants_list],  # Total score per ristorante
        'top_comment': [get_top_comment(st.session_state['data'][selected_group]['restaurants'][r]['reviews']) for r in restaurants_list]
    })

    map_data['score'] = map_data['total_score'].map('{:.3f}'.format)

    if not map_data.empty:
        fig_map = px.scatter_mapbox(
            map_data, 
            lat="lat", 
            lon="lon", 
            hover_name="name",  # Mostra solo il nome del ristorante nell'hover
            hover_data={
                "name": False,
                "total_score": False,
                #"size": False,  # Escludiamo "name" da hover_data poiché è già in hover_name
                "score": True,  # Mostra il punteggio totale formattato
                "top_comment": True,  # Mostra il commento migliore
                "lat": False,  # Escludi latitudine dai dati hover
                "lon": False,  # Escludi longitudine dai dati hover
            },
            zoom=10,
            color="total_score",  # Colora i marker in base al punteggio
            color_continuous_scale=[(0, "darkred"), (1, "darkgreen")],  # Scala di colori dal rosso al verde
            range_color=[10, 100],  # Scala di colori da 10 a 100 (punteggio)
            #size=[15] * len(map_data),  # Dimensione dei marker più grandi
        )
        fig_map.update_traces(marker=dict(size=15))
        # Configura lo stile della mappa come satellite
        fig_map.update_layout(mapbox_style="open-street-map")

        # Personalizziamo l'etichetta hover (ingrandiamo il testo)
        fig_map.update_traces(hoverlabel=dict(
            font_size=16,  # Dimensione più grande del testo
            font_family="Arial"
        ))

        # Rendi i punti della mappa più visibili, con una barra dei colori
        fig_map.update_layout(
            coloraxis_colorbar=dict(
                title="Total Score",
                tickvals=[10, 50, 100],  # Valori intermedi per la barra dei colori
                ticktext=["Never Again", "One night stand", "See you tomorrow"]
            )
        )

        # Mostra la mappa
        st.plotly_chart(fig_map)
