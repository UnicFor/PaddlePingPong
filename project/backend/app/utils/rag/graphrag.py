import networkx as nx
import spacy
import os
import re
import torch
import chardet
import numpy as np
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain.retrievers import EnsembleRetriever
from langchain.docstore.document import Document
from rank_bm25 import BM25Okapi
INDEX_FILE = "./app/data/faiss_index"
device = "cuda" if torch.cuda.is_available() else "cpu"
retrieval_pipeline = None

nlp = spacy.load("en_core_web_lg")  # python -m spacy download en_core_web_lg

def build_knowledge_graph(docs):
    G = nx.Graph()
    for doc in docs:
        spacy_doc = nlp(doc.page_content)
        entities = [ent.text for ent in spacy_doc.ents]
        if len(entities) > 1:
            for i in range(len(entities) - 1):
                G.add_edge(entities[i], entities[i + 1])
    return G

def retrieve_from_graph(query, G, top_k=5):
    query_doc = nlp(query)
    query_vector = query_doc.vector  

    similarity_scores = []
    for node in G.nodes:
        node_doc = nlp(node)
        node_vector = node_doc.vector  
        norm_q = np.linalg.norm(query_vector)
        norm_n = np.linalg.norm(node_vector)

        if norm_q == 0 or norm_n == 0:
            similarity = 0
        else:
            similarity = query_vector @ node_vector / (norm_q * norm_n)
        similarity_scores.append((node, similarity))

    similarity_scores.sort(key=lambda x: x[1], reverse=True)

    matched_nodes = [node for node, _ in similarity_scores[:top_k]]  

    if matched_nodes:
        related_nodes = []
        for node in matched_nodes:
            related_nodes.extend(list(G.neighbors(node)))
        return related_nodes[:top_k]
    return []


def save_uploaded_file(file, upload_dir):
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    file_path = os.path.join(upload_dir, file.filename)
    file.save(file_path)
    return file_path


def load_documents_from_file(file_path, filename):
    if filename.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
        return loader.load()
    elif filename.endswith(".docx"):
        loader = Docx2txtLoader(file_path)
        return loader.load()
    elif filename.endswith(".txt"):
        with open(file_path, "rb") as f:
            raw = f.read(4096)
            enc = chardet.detect(raw)["encoding"] or "utf-8"
        try:
            with open(file_path, "r", encoding=enc, errors="ignore") as f:
                text = f.read()
        except Exception as e:
            raise ValueError(f"Error loading {file_path}: {e}")
        if not text.strip():
            raise ValueError(f"{filename} 读出来是空的，请检查文件内容。")

        docs = [Document(page_content=text, metadata={"source": filename})]
        return docs
    else:
        return []


def process_uploaded_files(files):
    documents = []
    temp_dir = "./temp"
    for file in files:
        try:
            file_path = save_uploaded_file(file, temp_dir)
            docs = load_documents_from_file(file_path, file.filename)
            documents.extend(docs)
            os.remove(file_path)
        except Exception as e:
            raise Exception(f"Error processing {file.filename}: {str(e)}")
    return documents


def split_documents(documents, chunk_size=1000, chunk_overlap=200, separator="\n"):
    text_splitter = CharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, separator=separator
    )
    texts = text_splitter.split_documents(documents)
    return texts


def build_vector_store(texts, embeddings):
    if os.path.exists(INDEX_FILE):
        vector_store = FAISS.load_local(
            INDEX_FILE, embeddings, allow_dangerous_deserialization=True
        )
        new_vector_store = FAISS.from_documents(texts, embeddings)
        vector_store.merge_from(new_vector_store)
    else:
        vector_store = FAISS.from_documents(texts, embeddings)
    vector_store.save_local(INDEX_FILE)
    return vector_store


def build_retrieval_pipeline(texts, vector_store):
    text_contents = [doc.page_content for doc in texts]
    bm25_retriever = BM25Retriever.from_texts(
        text_contents,
        bm25_impl=BM25Okapi,
        preprocess_func=lambda text: re.sub(r"\W+", " ", text).lower().split(),
    )
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, vector_store.as_retriever(search_kwargs={"k": 5})],
        weights=[0.4, 0.6],
    )
    knowledge_graph = build_knowledge_graph(texts)
    return {
        "ensemble": ensemble_retriever,
        "texts": text_contents,
        # "reranker": reranker,
        "knowledge_graph": knowledge_graph,
    }