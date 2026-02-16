import chromadb
from chromadb.config import Settings
from app.config import settings

class VectorStore:
    def __init__(self):
        # Use EphemeralClient for in-memory, non-persisted vector store
        self.client = chromadb.EphemeralClient(
            settings=Settings(anonymized_telemetry=False)
        )

    def get_collection(self, domain_name: str):
        # Create or get collection ensuring names are safe (basic sanitization)
        safe_name = domain_name.replace(" ", "_").replace(".", "_")
        return self.client.get_or_create_collection(name=safe_name)

    def add_documents(self, domain_name: str, documents: list[str], metagenadat: list[dict], ids: list[str]):
        collection = self.get_collection(domain_name)
        collection.add(
            documents=documents,
            metadatas=metagenadat,
            ids=ids
        )

    def query_documents(self, domain_name: str, query_text: str, n_results: int = 3):
        try:
            collection = self.get_collection(domain_name)
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            return results['documents'][0] if results['documents'] else []
        except Exception as e:
            print(f"Error querying ChromaDB: {e}")
            return []

vector_store = VectorStore()
