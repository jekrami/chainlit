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
        self.document_sources = []  # Track which document each chunk came from

    def add_documents(self, docs, source_name="Unknown"):
        """Add documents with source tracking."""
        self.documents.extend(docs)
        # Track the source for each chunk
        self.document_sources.extend([source_name] * len(docs))

        valid_docs = [d for d in docs if d.strip()]
        if not valid_docs:
            print("Warning: No valid documents to add.")
            return

        embeddings = self.embedding_model.embed_documents(valid_docs)

        if self.index is None:
            dimension = len(embeddings[0])
            self.index = faiss.IndexFlatL2(dimension)

        self.index.add(np.array(embeddings, dtype='float32'))

    def retrieve(self, query, return_sources=False):
        """Retrieve relevant documents with optional source tracking."""
        if not self.index or not self.documents:
            return "" if not return_sources else ("", [])

        query_embedding = self.embedding_model.embed_query(query)
        distances, indices = self.index.search(np.array([query_embedding], dtype='float32'), TOP_K)

        retrieved_docs_with_scores = []
        for i, doc_index in enumerate(indices[0]):
            if doc_index < len(self.documents):
                retrieved_docs_with_scores.append({
                    "doc": self.documents[doc_index],
                    "source": self.document_sources[doc_index] if doc_index < len(self.document_sources) else "Unknown",
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
        sources = [item["source"] for item in re_ranked_docs]

        if return_sources:
            return "\n---\n".join(final_docs), sources
        return "\n---\n".join(final_docs)

    def delete_document(self, source_name):
        """Delete all chunks from a specific source document."""
        if not self.documents:
            return False

        # Find indices to keep (not from the source to delete)
        indices_to_keep = [i for i, src in enumerate(self.document_sources) if src != source_name]

        if len(indices_to_keep) == len(self.documents):
            return False  # Document not found

        # Keep only the documents and sources that don't match
        self.documents = [self.documents[i] for i in indices_to_keep]
        self.document_sources = [self.document_sources[i] for i in indices_to_keep]

        # Rebuild the index
        if self.documents:
            valid_docs = [d for d in self.documents if d.strip()]
            embeddings = self.embedding_model.embed_documents(valid_docs)
            dimension = len(embeddings[0])
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(np.array(embeddings, dtype='float32'))
        else:
            self.index = None

        return True

    def get_loaded_documents(self):
        """Get list of unique source documents."""
        return list(set(self.document_sources))

    def get_document_stats(self):
        """Get statistics about loaded documents."""
        stats = {}
        for source in self.document_sources:
            stats[source] = stats.get(source, 0) + 1
        return stats

    def save(self, path):
        if self.index is None:
            return
        with open(path, "wb") as f:
            pickle.dump({
                "index": faiss.serialize_index(self.index),
                "documents": self.documents,
                "document_sources": self.document_sources
            }, f)

    def load(self, path):
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.index = faiss.deserialize_index(data["index"])
            self.documents = data["documents"]
            self.document_sources = data.get("document_sources", ["Unknown"] * len(self.documents))
