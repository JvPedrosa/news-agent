import aiohttp
import os
from typing import List, Dict
import asyncio
import time
import json
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Lista de termos proibidos nas URLs
FORBIDDEN_TERMS = [
    "webjudicial",
    ".lu/",
    ".fr/",
    ".be/",
    "casadosdados",
    "empresalistacnpj",
    "busca",
    "b2bleads",
    "situacaocadastral",
    "estrategiaconcursos",
    ".def.br",
    "/profile/",
    "/download/",
    "slideshare",
    "/tag/",
    "pdfcoffee",
    "mindjuscriminal",
    "wordpress",
    "cnpjempresalistabr",
    "buscasocio",
    "listacnpjbr.com",
    "x.com",
    "jogo=",
    "mercadolivre.com",
    "dx.com",
    "aliexpress",
    "shopee",
    "arquivei",
    "funetec",
    "linkedin.com",
    "advocacia",
    "contabilidade-financeira.com",
    "ptdocz.com",
    "offshorealert.com",
    "kwai",
    "gauchazh",
    "jota.info",
    "travessa.com.br",
    "sympla",
    "museudalavajato.com.br",
    "eventou.com.br",
    "eleicoes-monitor",
    "conjur.com.br",
    "listamais.com.br",
    "inteligen.com.br",
    "serasaexperian.com.br",
    "sociosbrasil.com",
    "consultasocio.com",
    "iberleague.com",
    "justicaemfoco.info",
    "topico.justicaeletronica.com",
    "jusbrasil.com",
    "jus.br",
    "books.google",
    "escavador.com",
    "transparencia.cc",
    "legjur.com",
    "linkedin.com",
    "pamelasproducts.com",
    "twitter.com",
    "jornaldotocantins.com",
    "isisaho",
    "107.170.96.141",
    "moovitapp.com",
    "edu.br",
    "gov.br",
    "document",
    "vriconsulting",
    "dadosprocessuais.com",
    "datalegis.net",
    ".pdf",
    "docplayer.com",
    "bovespa.com",
    "wikipedia.org",
    "facebook.com",
    "instagram.com",
    "pinterest.com",
    "tiktok.com",
    "sistemas",
    "repositorio",
    "periodicos",
    "solutudo.com",
    "cba.org",
    "biagio.blogs",
    "licitacoes.compagas",
    "uniline.com",
    "arquivojudicial.org",
    "busca?",
    "busca=",
    "Busca?",
    "Busca=",
    "issuu.com",
    "mp.br",
    "consultacnpj.com",
    "vlex.com",
    "processoestadual.com",
    "consultarprocesso.com",
    "researchgate.net",
    "consciousplaza.com",
    ".org.br",
    "livraria.com",
    "senado.leg",
    "reclameaqui.com",
    "scielo.org",
    ".php",
    ".leg.br",
    ".org",
    "amazon.com",
    "indeed.com",
    "passeidireto.com",
    "youtube.com",
    "ibict.br",
    "livrariart",
    "livraria",
    ".livraria",
    "advogados",
    "associados",
    "adv",
    "direito",
    "//slide",
    ".slide",
    "/vagas-emprego",
    "estantevitrual",
    "criminalista",
    "blogspot",
]


# Função para fazer o scraping da notícia e verificar se a pessoa é a principal
async def scrape_and_check_if_person_is_main(url: str, person_name: str) -> bool:
    """Função para fazer o scraping da notícia e verificar se a pessoa é a principal"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                # Tenta detectar o encoding diretamente a partir do cabeçalho
                encoding = response.headers.get("Content-Type", "").lower()

                # Se o encoding não for informado, tenta as codificações mais comuns
                if "charset=" in encoding:
                    encoding = encoding.split("charset=")[-1]
                else:
                    encoding = "utf-8"  # Fallback para UTF-8

                # Agora tenta obter o conteúdo com a codificação detectada
                html = await response.text(encoding=encoding)

                soup = BeautifulSoup(html, "html.parser")

                # Verifica se o nome da pessoa aparece de maneira destacada na página
                body_text = soup.get_text().lower()
                return body_text.count(person_name.lower()) > 3
    except Exception as e:
        print(f"Erro ao fazer scraping da URL {url}: {e}")
        return False


async def fetch_news(
    session: aiohttp.ClientSession,
    query: str,
    limit: int,
    gl: str,
    hl: str,
    person_name: str,
) -> List[Dict]:
    """Função auxiliar para fazer a requisição assíncrona"""
    url = "https://google.serper.dev/news"
    load_dotenv()
    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json",
    }

    payload = {
        "q": query,
        "num": limit,
        "gl": gl,
        "hl": hl,
        "type": "search",
        "page": 1,
        "autocorrect": True,
    }

    failed_urls = []  # Armazenar URLs onde o scraping falhou

    try:
        async with session.post(url, headers=headers, json=payload) as response:
            data = await response.json()
            organic_results = data.get("organic", [])
            if not organic_results:
                organic_results = data.get("news", [])

            # Filtra os resultados para não retornar notícias com links que contenham os termos proibidos
            filtered_results = []

            for result in organic_results:
                link = result.get("link", "")

                # Verificar se o link contém algum termo proibido
                if any(forbidden_term in link for forbidden_term in FORBIDDEN_TERMS):
                    continue

                # Verificar se a pessoa é a principal da notícia
                is_person_main = await scrape_and_check_if_person_is_main(
                    link, person_name
                )

                if is_person_main:
                    filtered_results.append(
                        {
                            "title": result.get("title", ""),
                            "link": link,
                            "snippet": result.get("snippet", ""),
                            "date": result.get("date", ""),
                            "search_term": query,
                        }
                    )
                else:
                    failed_urls.append(
                        link
                    )  # Caso o scraping não consiga identificar a pessoa como principal

            return filtered_results, failed_urls
    except Exception as e:
        print(f"Erro ao buscar notícias para '{query}': {e}")
        return [], []


async def get_serper_news_async(
    person_name: str,
    terms: List[str],
    limit: int = 10,
    gl: str = "br",
    hl: str = "pt-br",
    porte_empresa: str = None,
    nome_fantasia: str = None,
) -> Dict:
    """Busca notícias de forma assíncrona para cada termo, capturando tempo de execução e URLs falhas"""
    start_time = time.time()  # Tempo de início do processo

    async with aiohttp.ClientSession() as session:
        queries = []

        # Constrói as consultas baseadas no tipo de empresa e termos
        if porte_empresa == "MÉDIA E GRANDE EMPRESA":
            queries.extend([f"{person_name} {term}" for term in terms])
        else:
            queries.extend([f'"{person_name}" {term}' for term in terms])

        if nome_fantasia:
            queries.extend([f'"{nome_fantasia}" {term}' for term in terms])

        # Executa todas as buscas de forma assíncrona
        tasks = [
            fetch_news(session, query, limit, gl, hl, person_name) for query in queries
        ]
        results = await asyncio.gather(*tasks)

        # Flatten a lista de resultados e falhas
        all_news = [news for sublist in results for news in sublist[0]]
        failed_urls = [url for sublist in results for url in sublist[1]]

        end_time = time.time()  # Tempo de término do processo
        process_duration = end_time - start_time

        # Estrutura do JSON
        result_json = {
            "process_start_time": start_time,
            "process_end_time": end_time,
            "process_duration_seconds": process_duration,
            "news_results": all_news,
            "failed_urls": failed_urls,
        }

        # Retorna o JSON formatado
        return result_json
