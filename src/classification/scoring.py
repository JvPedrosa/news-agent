from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from typing import Dict

async def score_news(state: Dict):
    model = ChatOpenAI(model="gpt-3.5-turbo")
    for noticia in state["filtered_news"]:
        resposta = await model.ainvoke([
            HumanMessage(content=f"Classifique a relevância dessa notícia sobre '{state['person_name']}' em relação aos termos 'crime', 'corrupção', 'lavagem de dinheiro': {noticia['snippet']} (Nota 0-10)")
        ])
        noticia["nota"] = resposta.content
    return state
