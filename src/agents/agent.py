import json
from langgraph.graph import StateGraph
from typing import TypedDict, List, Dict
from src.news.fetch_news import get_serper_news_async
from src.validation.validate_person import validate_person_data
from src.classification.scoring import score_news


# Definição de estado inicial do Agente
class AgentState(TypedDict):
    person_name: str
    news: List[Dict]
    filtered_news: List[Dict]


# Funções do agente


async def search_news(state: AgentState):
    news = await get_serper_news_async(
        person_name=state["person_name"],
        terms=["crime", "corrupção", "lavagem de dinheiro"],
        limit=10,
    )
    state["news"] = news
    return state


async def validate_person(state: AgentState):
    if await validate_person_data(state["person_name"], state["filtered_news"]):
        state["filtered_news"] = [{"status": "Pessoa validada"}]
    else:
        state["filtered_news"] = [{"status": "Pessoa não validada"}]
    return state


def filter_news(news: List[Dict], keywords: List[str]) -> List[Dict]:
    """Filtra as notícias com base nas palavras-chave"""
    filtered_news = []
    for noticia in news:
        if any(keyword.lower() in noticia["snippet"].lower() for keyword in keywords):
            filtered_news.append(noticia)
    return filtered_news


async def validate_person(state: Dict):
    # Placeholder para validação de pessoa com datasets externos
    # Simulando a validação
    person_name = state["person_name"]
    if person_name == "João Silva":  # Exemplificando
        state["status"] = "Pessoa validada"
        return True
    else:
        state["status"] = "Pessoa não validada"
        return False


async def score_news(state: AgentState):
    for noticia in state["filtered_news"]:
        noticia["nota"] = 9  # Atribui uma nota 9 por exemplo
    return state


# Criar o fluxo de execução do agente
workflow = StateGraph(AgentState)
workflow.add_node("search_news", search_news)
workflow.add_node("filter_news", filter_news)
workflow.add_node("validate_person", validate_person)
workflow.add_node("score_news", score_news)

workflow.set_entry_point("search_news")
workflow.add_edge("search_news", "filter_news")
workflow.add_edge("filter_news", "validate_person")
workflow.add_edge("validate_person", "score_news")
workflow.set_finish_point("score_news")


# Função principal do agente
async def run_agent():
    # Solicita o nome da pessoa no terminal
    person_name = input("Digite o nome da pessoa: ")
    # Define os termos de pesquisa
    terms = ["crime", "corrupção", "lavagem de dinheiro"]

    # Etapa 1: Buscar notícias
    news = await get_serper_news_async(person_name, terms)

    # Etapa 2: Filtrar notícias com palavras-chave
    filtered_news = filter_news(news, terms)

    # Etapa 3: Validar se a pessoa é a central
    state = {"person_name": person_name, "filtered_news": filtered_news}
    is_valid = await validate_person(state)

    if is_valid:
        # Etapa 4: Atribuir notas às notícias
        state = await score_news(state)

    # Salvar o resultado final em um arquivo JSON
    with open("resultado.json", "w", encoding="utf-8") as json_file:
        json.dump(state, json_file, ensure_ascii=False, indent=4)

    print("Resultado salvo em 'resultado.json'")
