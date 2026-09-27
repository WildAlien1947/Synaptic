import chromadb
import time

chroma_client = chromadb.PersistentClient(path="./synaptic_memory")
memory_store = chroma_client.get_or_create_collection(name="episodic_traces")

def remember(text, context="chat"):
    doc_id = f"trace_{int(time.time() * 1000)}"
    memory_store.add(
        documents=[text],
        metadatas=[{"context": context, "timestamp": time.time()}],
        ids=[doc_id]
    )

def recall(query_text, limit=3):
    results = memory_store.query(query_texts=[query_text], n_results=limit)
    if results and results.get("documents") and len(results["documents"][0]) > 0:
        return "\n".join(results["documents"][0])
    return "No relevant past memories."