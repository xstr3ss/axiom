import time
import logging
from datasets import load_dataset
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from fastembed import TextEmbedding
import uuid

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("fable.harvester")

# Connect to Fable's existing brain
client = QdrantClient(host="localhost", port=6333)
embedding_model = TextEmbedding(model_name="BAAI/bge-base-en-v1.5")
COLLECTION_NAME = "fable_ast_memory"

def harvest_global_intelligence():
    log.info("🌐 [Harvester] Waking up. Connecting to global datasets...")
    
    # Stream the dataset instead of downloading it all at once to save RAM
    # Using a subset of SWE-bench (real-world GitHub issues)
    dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test", streaming=True)
    
    batch = []
    batch_size = 50
    total_ingested = 0
    
    for row in dataset:
        # Extract the problem and the verified solution from the dataset
        problem_desc = row.get("problem_statement", "")
        solution_patch = row.get("patch", "")
        
        if not problem_desc or not solution_patch:
            continue
            
        batch.append({
            "problem": problem_desc,
            "patch": solution_patch,
            "repo": row.get("repo", "unknown")
        })
        
        if len(batch) >= batch_size:
            _process_and_store(batch)
            total_ingested += len(batch)
            log.info(f"🧠 [Harvester] Successfully digested {total_ingested} total experiences...")
            batch = []
            
            # Sleep briefly to prevent overloading the CPU during embedding
            time.sleep(2)

def _process_and_store(batch):
    texts_to_embed = [item["problem"] for item in batch]
    embeddings = list(embedding_model.embed(texts_to_embed))
    
    points = []
    for item, vector in zip(batch, embeddings):
        payload = {
            "signature": item["problem"][:200],
            "context": item["problem"],
            "solution_patch": item["patch"],
            "language": "python",
            "tags": ["autonomous_harvest", item["repo"]],
            "verified": True
        }
        points.append(PointStruct(id=str(uuid.uuid4()), vector=vector.tolist(), payload=payload))
        
    client.upsert(collection_name=COLLECTION_NAME, points=points)

if __name__ == "__main__":
    log.info("🚀 [Harvester] Zero-Human Autonomous Training Daemon Started.")
    while True:
        try:
            harvest_global_intelligence()
            # Sleep for 24 hours after a full harvest before looking for new data
            log.info("💤 [Harvester] Knowledge base updated. Sleeping for 24 hours.")
            time.sleep(86400)
        except Exception as e:
            log.error(f"⚠️ [Harvester] Network glitch, retrying in 1 hour: {e}")
            time.sleep(3600)
