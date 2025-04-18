import faiss
import numpy as np
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import torch
from transformers import AutoTokenizer, AutoModel
_INDEX_CACHE = None
_LINES_CACHE = None

def load_dataset_embedding(index_file: str = "../../data/expert_index.index", text_file: str = "../../data/expert_texts.txt"):   
    global _INDEX_CACHE, _LINES_CACHE 
    
    delimiter = "<<<DOC>>>"
    if _INDEX_CACHE is None:
        index_path = index_file
        try:
            _INDEX_CACHE = faiss.read_index(index_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load FAISS index from {index_path}: {e}")

    if _LINES_CACHE is None:
        try:
            with open(text_file, "r", encoding="utf-8") as f:
                content = f.read()
                _LINES_CACHE = [seg.strip() for seg in content.split(delimiter) if seg.strip()]
        except Exception as e:
            raise RuntimeError(f"Failed to load text file {text_file}: {e}")
    return _INDEX_CACHE, _LINES_CACHE
    


def search_from_index(query,  k=5):

    tokenizer = AutoTokenizer.from_pretrained("./app/models/bge-m3")
    model = AutoModel.from_pretrained("./app/models/bge-m3")
    model.eval()


    def encode(text, tokenizer, model):
        with torch.no_grad():
            encoded_input = tokenizer(text, return_tensors='pt', padding=True, truncation=True, max_length=512)
            model_output = model(**encoded_input)
            embeddings = model_output.last_hidden_state[:, 0, :] 
            return embeddings.squeeze(0).numpy()
    query_vector =encode(query, tokenizer, model)
    query_vector = np.array(query_vector, dtype=np.float32).reshape(1, -1)

    distances, indices = _INDEX_CACHE.search(query_vector, k)
    print(indices[0])
    print(len(_LINES_CACHE))
    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(_LINES_CACHE):
            results.append((_LINES_CACHE[idx], distances[0][i]))

    print(f"Example results: {results}")
    return results