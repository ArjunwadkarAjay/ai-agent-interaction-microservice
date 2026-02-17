import chromadb
from chromadb.config import Settings
from app.config import settings

class VectorStore:
    def __init__(self):
        # Use EphemeralClient for in-memory, non-persisted vector store
        self.client = chromadb.EphemeralClient(
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(name="knowledge_base")

    def add_documents(self, domain_name: str, documents: list[str], metadatas: list[dict], ids: list[str]):
        # Ensure metadata contains domain
        for meta in metadatas:
            meta["domain"] = domain_name
            
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def query_documents(self, domain_name: str | None, query_text: str, n_results: int = 3):
        try:
            where_filter = None
            if domain_name and domain_name.lower() != "all":
                where_filter = {"domain": domain_name}
                
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_filter
            )
            return results['documents'][0] if results['documents'] else []
        except Exception as e:
            print(f"Error querying ChromaDB: {e}")
            return []

vector_store = VectorStore()
