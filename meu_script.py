import requests
from bs4 import BeautifulSoup
import re

def download_gif_from_tweet(tweet_url):
    # Cabeçalhos para emular um navegador e evitar bloqueios
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # Fazer o pedido HTTP para a URL do tweet
    response = requests.get(tweet_url, headers=headers)

    # Verificar se a requisição foi bem-sucedida
    if response.status_code != 200:
        print("Erro ao acessar o tweet")
        return

    # Analisar o HTML da página do tweet
    soup = BeautifulSoup(response.text, 'html.parser')

    # Procurar todos os scripts embutidos no HTML
    scripts = soup.find_all('script')

    # Buscar o link do vídeo MP4 no conteúdo JavaScript
    for script in scripts:
        script_text = script.string
        if script_text and 'video_url' in script_text:
            # Usar regex para encontrar o URL do vídeo MP4
            match = re.search(r'"video_url":"([^"]+)"', script_text)
            if match:
                video_url = match.group(1).replace("\\u0026", "&")
                print(f"Baixando GIF de: {video_url}")
                
                # Nome do arquivo para salvar
                file_name = "x_gif.mp4"

                # Baixar o arquivo de vídeo (MP4)
                video_response = requests.get(video_url)

                with open(file_name, 'wb') as f:
                    f.write(video_response.content)

                print(f"GIF baixado com sucesso como {file_name}")
                return

    print("Nenhum GIF encontrado nesse tweet.")

# Exemplo de uso
tweet_url = "https://x.com/i/status/1844195606576918758"  # Insira a URL do tweet de x.com
download_gif_from_tweet(tweet_url)
