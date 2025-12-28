import faiss
import numpy as np
import pickle
from langchain_ollama.embeddings import OllamaEmbeddings
from config import EMBEDDING_MODEL, TOP_K, KEYWORD_BOOST_CONFIG

class RagPipeline:
    def __init__(self):
        self.embedding_model = OllamaEmbeddings(model=EMBEDDING_MODEL)
        self.index = None
        self.documents = []

    def add_documents(self, docs):
        self.documents.extend(docs)

        valid_docs = [d for d in docs if d.strip()]
        if not valid_docs:
            print("Warning: No valid documents to add.")
            return

        embeddings = self.embedding_model.embed_documents(valid_docs)

        if self.index is None:
            dimension = len(embeddings[0])
            self.index = faiss.IndexFlatL2(dimension)

        self.index.add(np.array(embeddings, dtype='float32'))

    def retrieve(self, query):
        if not self.index or not self.documents:
            return ""

        query_embedding = self.embedding_model.embed_query(query)
        distances, indices = self.index.search(np.array([query_embedding], dtype='float32'), TOP_K)

        retrieved_docs_with_scores = []
        for i, doc_index in enumerate(indices[0]):
            if doc_index < len(self.documents):
                retrieved_docs_with_scores.append({
                    "doc": self.documents[doc_index],
                    "semantic_score": 1 / (1 + distances[0][i])
                })

        for item in retrieved_docs_with_scores:
            keyword_score = 0
            for keyword, boost in KEYWORD_BOOST_CONFIG.items():
                if keyword in item["doc"]:
                    keyword_score += boost

            item["final_score"] = item["semantic_score"] + keyword_score

        re_ranked_docs = sorted(retrieved_docs_with_scores, key=lambda x: x["final_score"], reverse=True)

        final_docs = [item["doc"] for item in re_ranked_docs]
        return "\n---\n".join(final_docs)

    def save(self, path):
        if self.index is None:
            return
        with open(path, "wb") as f:
            pickle.dump({
                "index": faiss.serialize_index(self.index),
                "documents": self.documents
            }, f)

    def load(self, path):
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.index = faiss.deserialize_index(data["index"])
            self.documents = data["documents"]
