import os
import glob
import uuid
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from fastembed import TextEmbedding

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("fable.semantic")

COLLECTION_NAME = "fable_ast_memory"
client = QdrantClient(host="localhost", port=6333)
embedding_model = TextEmbedding(model_name="BAAI/bge-base-en-v1.5")

DOC_TARGETS = ["README.md", "requirements.txt", "pyproject.toml", "Dockerfile"]

def index_project_semantics():
    log.info("📐 [Semantic] Indexing project architecture and configuration...")
    items = []

    # 1. Configuration & documentation files
    for filename in DOC_TARGETS:
        if os.path.exists(filename):
            with open(filename, "r", errors="ignore") as f:
                content = f.read().strip()
            if content:
                items.append({
                    "signature": f"doc:{filename}",
                    "context": f"Project Document ({filename}):\n{content[:2000]}",
                    "solution_patch": "",
                    "language": "text",
                    "tags": ["semantic_doc", filename],
                    "type": "semantic",
                    "verified": True
                })

    # 2. Key Python file signatures and interfaces
    py_files = glob.glob("*.py")
    for py_file in py_files:
        if py_file in ["harvester.py", "semantic_watcher.py", "reflection_logger.py"]:
            continue
        with open(py_file, "r", errors="ignore") as f:
            lines = [l for l in f.readlines() if l.startswith("def ") or l.startswith("class ") or l.startswith("import ") or l.startswith("from ")]
        summary = "".join(lines)
        if summary.strip():
            items.append({
                "signature": f"module_api:{py_file}",
                "context": f"Module Interface for {py_file}:\n{summary[:1500]}",
                "solution_patch": "",
                "language": "python",
                "tags": ["semantic_api", py_file],
                "type": "semantic",
                "verified": True
            })

    if not items:
        return

    texts = [i["context"] for i in items]
    embeddings = list(embedding_model.embed(texts))
    points = [
        PointStruct(id=str(uuid.uuid4()), vector=vec.tolist(), payload=item)
        for item, vec in zip(items, embeddings)
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    log.info(f"✅ Successfully updated {len(points)} architectural records in memory.")

if __name__ == "__main__":
    index_project_semantics()
