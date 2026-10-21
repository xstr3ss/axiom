import uuid
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from fastembed import TextEmbedding

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("fable.reflection")

COLLECTION_NAME = "fable_ast_memory"
client = QdrantClient(host="localhost", port=6333)
embedding_model = TextEmbedding(model_name="BAAI/bge-base-en-v1.5")

def log_failure_reflection(failed_code: str, error_trace: str, context_goal: str):
    log.info("💡 [Reflective] Recording execution failure to prevent future regressions...")
    context = (
        f"FAILED EXECUTION ATTEMPT:\n"
        f"Goal: {context_goal}\n\n"
        f"Error Trace / Sandbox Crash:\n{error_trace[:1500]}\n\n"
        f"Failed Code Snippet:\n{failed_code[:1500]}"
    )
    vector = list(embedding_model.embed([context]))[0]

    payload = {
        "signature": f"failure_trap:{error_trace.splitlines()[-1][:100] if error_trace else 'unknown'}",
        "context": context,
        "solution_patch": "",
        "language": "python",
        "tags": ["reflection", "sandbox_failure", "trap_to_avoid"],
        "type": "reflective",
        "verified": False
    }

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[PointStruct(id=str(uuid.uuid4()), vector=vector.tolist(), payload=payload)]
    )
    log.info("✅ Reflection logged to Qdrant.")
