import os
import logging
import requests
import subprocess
import time
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import uuid

log = logging.getLogger("axiom.memory")

class VectorMemory:
    def __init__(self, collection_name: str = "axiom_ast_memory"):
        self.collection_name = collection_name
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        
        self._ensure_qdrant_running()
        
        self.client = QdrantClient(url=self.qdrant_url)
        self.ollama_url = os.getenv("OLLAMA_EMBED_URL", "http://localhost:11434/api/embeddings")
        self.embed_model = os.getenv("EMBED_MODEL", "nomic-embed-text") 
        
        self._ensure_collection()

    def _ensure_qdrant_running(self):
        """Pings Qdrant and forcibly starts the Docker container if offline."""
        try:
            requests.get(self.qdrant_url, timeout=2)
        except requests.ConnectionError:
            log.warning("⚠️ [Memory] Qdrant is offline. Auto-starting Docker container...")
            subprocess.run(["docker", "start", "fable_qdrant"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3) # Give the database 3 seconds to spin up

    def _ensure_collection(self):
        if not self.client.collection_exists(self.collection_name):
            log.info(f"🧠 [Memory] Bootstrapping new Qdrant collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )

    def _get_embedding(self, text: str) -> List[float]:
        try:
            payload = {"model": self.embed_model, "prompt": text}
            res = requests.post(self.ollama_url, json=payload, timeout=10)
            res.raise_for_status()
            return res.json().get("embedding", [])
        except Exception as e:
            log.error(f"❌ [Memory] Embedding failed (Is Ollama running?): {e}")
            return []

    def store_repair_context(self, error_signature: str, successful_code: str, file_path: str):
        text_to_embed = f"Error: {error_signature}\nFix: {successful_code}"
        vector = self._get_embedding(text_to_embed)

        if not vector:
            return

        # --- CROSS-PROJECT SCHEMA UPGRADE ---
        project_id = os.path.basename(os.getcwd())
        ext = os.path.splitext(file_path)[1].lower()
        language_map = {".py": "python", ".js": "javascript", ".ts": "typescript", ".go": "go", ".rs": "rust"}
        language = language_map.get(ext, "unknown")

        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "project_id": project_id,
                "language": language,
                "error_signature": error_signature,
                "file_path": file_path,
                "code_snapshot": successful_code,
                "type": "successful_repair"
            }
        )

        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        log.info(f"💾 [Memory] Repair indexed globally (Project: {project_id} | Lang: {language}).")

    def recall_similar_errors(self, current_error: str, limit: int = 1) -> List[Dict[str, Any]]:
        vector = self._get_embedding(current_error)
        if not vector:
            return []

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=limit
        ).points
        
        return [hit.payload for hit in results if hit.score > 0.75]


# FABLE_MEMORY_FALLBACK_PATCHED
for _ClassName in ["VectorMemory", "BugResolutionStore", "MemoryStore"]:
    _cls = globals().get(_ClassName)
    if _cls:
        for _mname in ["retrieve_similar", "save_resolution", "save_antipattern", "search"]:
            if hasattr(_cls, _mname):
                _orig_m = getattr(_cls, _mname)
                def _make_safe(fn):
                    def _wrapped(self, *a, **kw):
                        try:
                            return fn(self, *a, **kw)
                        except Exception as e:
                            return [] if "retrieve" in fn.__name__ or "search" in fn.__name__ else None
                    return _wrapped
                setattr(_cls, _mname, _make_safe(_orig_m))
