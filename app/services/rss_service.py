import requests
import xmltodict
from typing import List, Dict, Any, Union

URL = "https://news.google.com/rss/search?q=saude+masculina&hl=pt-BR&gl=BR&ceid=BR:pt"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def _get_text(value: Union[str, Dict, List, None]) -> str:
    if isinstance(value, dict):
        return value.get('#text', '')
    elif isinstance(value, list) and value:
        for item in value:
            text = _get_text(item)
            if text: return text
        return ''
    return value if isinstance(value, str) else ''

def buscar_todas_rss() -> List[Dict[str, Any]]:
    resultados = []
    try:
        response = requests.get(URL, headers=HEADERS, timeout=10)
        response.raise_for_status()

        rss_dict = xmltodict.parse(response.content)
        
        items = []
        channel = rss_dict.get('rss', {}).get('channel', {})
        if channel:
            items = channel.get('item', [])
            if isinstance(items, dict):
                items = [items]
        
        if not items:
            return []

        for item in items:
            if isinstance(item, dict):
                title = _get_text(item.get("title"))
                description = _get_text(item.get("description"))
                link = _get_text(item.get("link"))
                
                image_url = ''
                
                # Tentativa 1: 'media:thumbnail'
                media_thumbnail = item.get('media:thumbnail')
                if media_thumbnail:
                    if isinstance(media_thumbnail, dict) and media_thumbnail.get('@url'):
                        image_url = media_thumbnail.get('@url')

                # Tentativa 2: 'media:content'
                if not image_url:
                    media_content = item.get('media:content')
                    if isinstance(media_content, dict) and media_content.get('@medium') == 'image':
                        image_url = media_content.get('@url')

                # Tentativa 3: 'enclosure' (outro padrão comum)
                if not image_url and item.get('enclosure') and item['enclosure'].get('@url'):
                    image_url = item['enclosure'].get('@url')

                if title and link:
                    noticia_padronizada = {
                        "title": title,
                        "description": description,
                        "link": link,
                        "imageUrl": image_url
                    }
                    resultados.append(noticia_padronizada)

    except requests.exceptions.HTTPError as e:
        print(f"Erro HTTP ao acessar {URL}: {e}")
        return [{"error": f"Erro ao acessar o feed de notícias (HTTP {e.response.status_code}). Tente novamente mais tarde."}]
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão ao acessar {URL}: {e}")
        return [{"error": f"Erro de conexão ao acessar o feed de notícias. Verifique sua conexão com a internet."}]
    except Exception as e:
        print(f"Erro ao processar o feed RSS: {e}")
        return [{"error": f"Erro interno ao processar o feed de notícias: {e}"}]
            
    return resultados