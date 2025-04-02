import aiohttp
import os
from typing import List, Dict
import asyncio

async def fetch_news(session: aiohttp.ClientSession, query: str, limit: int, gl: str, hl: str) -> List[Dict]:
    """Função auxiliar para fazer a requisição assíncrona"""
    url = "https://google.serper.dev/news"
    headers = {
        'X-API-KEY': os.getenv('SERPER_API_KEY'),  # Certifique-se de que a chave está configurada no arquivo .env
        'Content-Type': 'application/json'
    }

    payload = {
        'q': query,
        'num': limit,
        "gl": gl,
        "hl": hl,
        "type": "search",
        "page": 1,
        "autocorrect": True
    }

    try:
        async with session.post(url, headers=headers, json=payload) as response:
            data = await response.json()
            organic_results = data.get('organic', [])
            if not organic_results:
                organic_results = data.get('news', [])

            return [{
                'title': result.get('title', ''),
                'link': result.get('link', ''),
                'snippet': result.get('snippet', ''),
                'date': result.get('date', ''),
                'search_term': query
            } for result in organic_results]
    except Exception as e:
        print(f"Erro ao buscar notícias para '{query}': {e}")
        return []


async def get_serper_news_async(person_name: str, terms: List[str], limit: int = 10, gl: str = "br", hl: str = "pt-br", porte_empresa: str = None, nome_fantasia: str = None) -> List[Dict]:
    """Busca notícias de forma assíncrona para cada termo"""
    async with aiohttp.ClientSession() as session:
        queries = []
        if porte_empresa == 'MÉDIA E GRANDE EMPRESA':
            queries.extend([f'{person_name} {term}' for term in terms])
        else:
            queries.extend([f'"{person_name}" {term}' for term in terms])
        if nome_fantasia:
            queries.extend([f'"{nome_fantasia}" {term}' for term in terms])

        # Executar todas as buscas de forma assíncrona
        tasks = [fetch_news(session, query, limit, gl, hl) for query in queries]
        results = await asyncio.gather(*tasks)

        # Flatten a lista de resultados
        all_news = [news for sublist in results for news in sublist]
        return all_news

