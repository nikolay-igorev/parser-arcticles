import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss

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

    # Инициализация модели SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Создание эмбеддингов для текстов
    embeddings = model.encode(texts, convert_to_tensor=False, show_progress_bar=True)

    # Создание Faiss индекса
    dimension = embeddings.shape[1]
    faiss_index = faiss.IndexFlatL2(dimension)

    # Добавление эмбеддингов в индекс
    faiss_index.add(embeddings)

    import pickle

    # Сохранение индекса в файл .faiss
    faiss.write_index(faiss_index, "index.faiss")
    print("Faiss индекс успешно создан и сохранен в 'faiss_knowledge_base.faiss'.")

    # Сохранение эмбеддингов и других данных в файл .pkl
    with open("index.pkl", "wb") as pkl_file:
        pickle.dump({"embeddings": embeddings, "texts": texts}, pkl_file)
    print("Данные эмбеддингов успешно сохранены в 'embeddings_data.pkl'.")

    print("Faiss индекс успешно создан и сохранен в 'faiss_knowledge_base.index'.")
else:
    print("Не удалось загрузить данные.")



