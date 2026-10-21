import os
import uuid
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from fastembed import TextEmbedding

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("fable.seeder")

COLLECTION_NAME = "fable_ast_memory"
VECTOR_DIM = 768  # Standard size for lightweight fastembed models (e.g., BAAI/bge-small-en-v1.5)

client = QdrantClient(host="localhost", port=6333)
embedding_model = TextEmbedding(model_name="BAAI/bge-base-en-v1.5")

def ensure_collection():
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        log.info(f"📦 Creating Qdrant collection: {COLLECTION_NAME}")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE)
        )

def seed_problem_solution_batch(items: list[dict]):
    """
    items should be a list of dicts with:
    {
        "problem_description": str,
        "language": "python",
        "patch_code": str,
        "tags": list[str]
    }
    """
    texts_to_embed = [item["problem_description"] for item in items]
    
    # Generate vectors in one fast CPU batch using SIMD acceleration
    embeddings = list(embedding_model.embed(texts_to_embed))
    
    points = []
    for item, vector in zip(items, embeddings):
        point_id = str(uuid.uuid4())
        payload = {
            "signature": item["problem_description"][:200],
            "context": item["problem_description"],
            "solution_patch": item["patch_code"],
            "language": item.get("language", "python"),
            "tags": item.get("tags", ["verified_seed"]),
            "verified": True
        }
        points.append(PointStruct(id=point_id, vector=vector.tolist(), payload=payload))
        
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    log.info(f"✅ Ingested batch of {len(points)} records into Fable's memory.")

if __name__ == "__main__":
    ensure_collection()

    # Example: Injecting a curated algorithmic and bug-fix pair
    curated_knowledge = [
        {
            "problem_description": "Fix ZeroDivisionError when calculating average metric over empty query results.",
            "language": "python",
            "patch_code": "return sum(values) / len(values) if values else 0.0",
            "tags": ["edge_case", "math", "zero_division"]
        },
        {
            "problem_description": "Implement LRU Cache with O(1) get and put complexity using OrderedDict or doubly linked list.",
            "language": "python",
            "patch_code": "from collections import OrderedDict\nclass LRUCache:\n    def __init__(self, capacity: int):\n        self.cache = OrderedDict()\n        self.cap = capacity\n    def get(self, key: int) -> int:\n        if key not in self.cache:\n            return -1\n        self.cache.move_to_end(key)\n        return self.cache[key]\n    def put(self, key: int, value: int) -> None:\n        if key in self.cache:\n            self.cache.move_to_end(key)\n        self.cache[key] = value\n        if len(self.cache) > self.cap:\n            self.cache.popitem(last=False)",
            "tags": ["data_structures", "lru_cache", "algorithms"]
        }
    ]

    seed_problem_solution_batch(curated_knowledge)
