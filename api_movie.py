import requests
import random

API_KEY = "395841fe9669368a2b773c2870a5b63e"
BASE_URL = "https://api.themoviedb.org/3"

def get_popular_movie():
    page = random.randint(1, 20) 
    url = f"{BASE_URL}/movie/popular"

    response = requests.get(url, params={
        "api_key": API_KEY,
        "page": page
    }).json()

    movie = random.choice(response["results"])

    title = movie["title"]
    poster_url = "https://image.tmdb.org/t/p/w500" + movie["poster_path"]

    
    return title, poster_url
