import pandas as pd
import faiss
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
import os
from constants import OPEN_API_KEY

# Загрузка данных с гибкими параметрами
def load_data(file_path):
    try:
        data = pd.read_csv(file_path, on_bad_lines='skip')
        return data
    except Exception as e:
        print(f"Ошибка загрузки данных: {e}")
        return None

# Укажите путь к вашему CSV-файлу
file_path = "combined_articles.csv"
data = load_data(file_path)

if data is not None:
    # Удаление пустых значений в колонке content
    texts = data['content'].dropna().tolist()

    # Инициализация OpenAI эмбеддингов
    embeddings = OpenAIEmbeddings(openai_api_key=OPEN_API_KEY)

    # Создание FAISS индекса через LangChain
    faiss_index = FAISS.from_texts(texts, embeddings)

    # Сохранение индекса локально
    faiss_dir = 'faiss_indexes'
    faiss_index.save_local(faiss_dir)
    print(f"FAISS индекс успешно создан и сохранен в директории '{faiss_dir}'.")
else:
    print("Не удалось загрузить данные.")
