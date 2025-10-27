import requests
import xmltodict

URLS = [
    "https://rss.app/feeds/zuLqVABUuWY1LVA8.xml"  # feed de saúde masculina
]

def buscar_rss():
    resultados = []
    for url in URLS:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                rss_dict = xmltodict.parse(response.content)
                items = rss_dict.get('rss', {}).get('channel', {}).get('item', [])
                if isinstance(items, dict):
                    items = [items]
                # Padronizar campos para o frontend
                for item in items:
                    if isinstance(item, dict):
                        # Garantir campos consistentes
                        item['source'] = url
                resultados.extend(items)
            else:
                resultados.append({"error": f"Não foi possível acessar {url}"})
        except requests.exceptions.RequestException as e:
            resultados.append({"error": f"Erro ao acessar {url}: {str(e)}"})
    return resultados