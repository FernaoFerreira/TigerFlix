import os
import requests
from googletrans import Translator

API_KEY = os.getenv("OMDB_API_KEY")
BASE_URL = "http://www.omdbapi.com/"
translator = Translator()  # Initialize translator

def get_movie_info(movie_title, lang="pt"):  # Default: Portuguese
    params = {"t": movie_title, "apikey": API_KEY}
    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        if data.get("Response") == "True":
            # Translate summary
            translated_plot = translator.translate(data.get("Plot"), dest=lang).text

            return (
                f"🎬 *{data.get('Title')}* ({data.get('Year')})\n"
                f"⏳ Duração: {data.get('Runtime')}\n"
                f"📖 Resumo: {translated_plot}\n"
                f"🖼 Poster: {data.get('Poster')}"
            )
        else:
            return "❌ Filme não encontrado."
    else:
        return "⚠️ Falha na solicitação da API."

if __name__ == "__main__":
    movie_name = input("Digite o nome do filme: ")
    lang_code = input("Digite o código do idioma (ex: 'pt' para português, 'es' para espanhol): ").strip()
    message = get_movie_info(movie_name, lang=lang_code)
    print("\n" + message)
