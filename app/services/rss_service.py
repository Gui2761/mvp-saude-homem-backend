import feedparser
import requests
import random
import re

# Lista de Feeds de Saúde (Fontes mais estáveis e variadas)
URLS = [
    "https://g1.globo.com/rss/g1/saude/",              # G1 Saúde (Excelente)
    "https://drauziovarella.uol.com.br/feed/",         # Dr. Drauzio Varella (Dicas e Prevenção)
    "https://www.gov.br/saude/pt-br/rss/rss-noticias", # Ministério da Saúde (Oficial)
    "https://vidasaudavel.einstein.br/feed/",          # Hospital Einstein (Qualidade de Vida)
]

def buscar_rss():
    resultados = []
    
    # User-Agent de navegador para evitar bloqueios
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml'
    }

    for url in URLS:
        try:
            # 1. Baixa o conteúdo
            response = requests.get(url, headers=headers, timeout=8)
            
            if response.status_code != 200:
                print(f"⚠️ Link indisponível: {url} (Status {response.status_code})")
                continue

            # 2. Processa o XML com feedparser
            feed = feedparser.parse(response.content)

            if not feed.entries:
                continue

            for entry in feed.entries:
                try:
                    # Título
                    title = entry.get('title', '')
                    if not title: continue

                    # Link
                    link = entry.get('link', '')

                    # Descrição (Limpeza de HTML mais robusta)
                    raw_description = entry.get('summary', '') or entry.get('description', '') or ''
                    
                    # Remove tags HTML (<p>, <a>, <img>, etc) da descrição para ficar texto puro
                    clean_description = re.sub('<[^<]+?>', '', raw_description).strip()

                    # Busca de Imagem (Várias tentativas para garantir)
                    image_url = ''
                    
                    # Tenta 'media_content' (Padrão G1)
                    if 'media_content' in entry:
                        media = entry.media_content
                        if isinstance(media, list) and len(media) > 0:
                            image_url = media[-1].get('url', '') # Pega a maior imagem
                    
                    # Tenta 'media_thumbnail' (Youtube/Blogs)
                    if not image_url and 'media_thumbnail' in entry:
                         thumb = entry.media_thumbnail
                         if isinstance(thumb, list) and len(thumb) > 0:
                             image_url = thumb[0].get('url', '')

                    # Tenta extrair do HTML da descrição (comum em Wordpress como Drauzio/Einstein)
                    if not image_url and 'src=' in raw_description:
                        match = re.search(r'src="([^"]+jpg|[^"]+png|[^"]+jpeg)"', raw_description)
                        if match:
                            image_url = match.group(1)

                    # Se ainda não tem imagem, tenta links de enclosure
                    if not image_url and 'links' in entry:
                        for l in entry.links:
                            if l.get('rel') == 'enclosure' and 'image' in l.get('type', ''):
                                image_url = l.get('href', '')
                                break

                    # Adiciona à lista apenas se tiver o básico
                    if title and link:
                        resultados.append({
                            "title": title,
                            "description": clean_description[:140] + "..." if len(clean_description) > 140 else clean_description,
                            "link": link,
                            "imageUrl": image_url
                        })

                except Exception:
                    continue

        except Exception as e:
            print(f"❌ Erro no feed {url}: {e}")
            continue

    # Embaralha para variar as notícias na tela inicial
    if resultados:
        random.shuffle(resultados)
    
    return resultados