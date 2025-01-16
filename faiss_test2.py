import asyncio

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from openai import AsyncOpenAI
import os

OPEN_API_KEY = '<YOUR_API_KEY>'

class Faiss:
    loaded_vectorstore: FAISS
    def __init__(self, OPENAI_KEY: str, chatgpt_client):
        embeddings = OpenAIEmbeddings(api_key=OPENAI_KEY, async_client=AsyncOpenAI,)
        faiss_dir = 'faiss_indexes'
        self.loaded_vectorstore = FAISS.load_local(
            faiss_dir,
            embeddings,
            allow_dangerous_deserialization=True  # Разрешаем опасную десериализацию
        )
        self.chatgpt_client = chatgpt_client

    async def ask_neuro_consultant(self, topic: str):
        results = self.loaded_vectorstore.similarity_search(topic, k=5)
        context = "\n\n".join([doc.page_content for doc in results])
        return topic, context

    async def chatbot_chat(self, text: str):
        topic, context = await self.ask_neuro_consultant(text)
        messages = [
            {"role": "system", "content": f"Контекст для релевантного ответа:\n{context}"},
            {"role": "user", "content": f"""
        Ответь :\n{text}
    """}
        ]
        return await self.chatgpt_client.answer(self.loaded_vectorstore.embeddings.api_key, messages)

def main():
    chatgpt_client = AsyncOpenAI(api_key=OPEN_API_KEY)
    f = Faiss(OPEN_API_KEY, chatgpt_client)

    topic = "Help me"
    response = asyncio.run(f.chatbot_chat(topic))
    print(response)


if __name__ == '__main__':
    main()
