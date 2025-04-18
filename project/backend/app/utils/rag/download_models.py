import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModel


def download_model(local_model_path="./app/models/beg-m3"):
    if not os.path.exists(local_model_path):
        print(f"Model not found at {local_model_path}, downloading...")
        tokenizer = AutoTokenizer.from_pretrained(
            "BAAI/bge-m3", cache_dir=local_model_path
        )
        model = AutoModel.from_pretrained(
            "BAAI/bge-m3", cache_dir=local_model_path
        )
    else:
        print(f"Model found at {local_model_path}")







