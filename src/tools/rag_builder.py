import os
import pandas as pd
from typing import Any, List
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document
from src.helpers.conf_loader import RAG_CONF, MODELS_CONF

class RAGBuilder:
    def __init__(self, name: str, config: dict, embedding_model: str, chunk_size: int, chunk_overlap: int, top_k: int = 3):
        self.name = name
        self.source_data = config["source_data"]
        self.vector_db = config["vector_db"]
        self.track_file = config["track_file"]
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        self.embedding = OpenAIEmbeddings(model=embedding_model)

    def _load_documents(self) -> List[Document]:
        df = pd.read_excel(self.source_data)
        docs = [
            Document(
                page_content=f"Question: {row['Question']}\nAnswer: {row['Answer']}",
                metadata={"Category": row.get("Category", ""), "Source": self.name},
            )
            for _, row in df.iterrows()
        ]
        return docs

    def _split_documents(self, docs: List[Document]) -> List[Document]:
        splitter = CharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        return [Document(page_content=chunk, metadata=doc.metadata)
                for doc in docs for chunk in splitter.split_text(doc.page_content)]

    def _get_file_timestamp(self) -> str:
        return str(os.path.getmtime(self.source_data))

    def _is_updated(self) -> bool:
        current = self._get_file_timestamp()
        if not os.path.exists(self.track_file):
            return True
        with open(self.track_file, "r") as f:
            old = f.read().strip()
        return current != old

    def _save_timestamp(self):
        with open(self.track_file, "w") as f:
            f.write(self._get_file_timestamp())

    def create_or_load_vectorstore(self):
        if os.path.exists(self.vector_db) and not self._is_updated():
            print(f"[{self.name}] Loading existing FAISS index...")
            faiss_store = FAISS.load_local(self.vector_db, self.embedding, allow_dangerous_deserialization=True)
        else:
            print(f"[{self.name}] Creating new FAISS index...")
            docs = self._split_documents(self._load_documents())
            faiss_store = FAISS.from_documents(docs, self.embedding)
            faiss_store.save_local(self.vector_db)
            self._save_timestamp()
        return faiss_store.as_retriever(search_kwargs={"k": self.top_k})

def build_all_retrievers():
    retrievers = {}
    for dataset in RAG_CONF["datasets"]:
        builder = RAGBuilder(
            name=dataset["name"],
            config=dataset,
            embedding_model=MODELS_CONF["embedding"]["model_name"],
            chunk_size=MODELS_CONF["embedding"]["chunk_size"],
            chunk_overlap=MODELS_CONF["embedding"]["chunk_overlap"],
            top_k=MODELS_CONF["embedding"].get("top_k", 3),
        )
        retrievers[dataset["name"]] = builder.create_or_load_vectorstore()
    return retrievers