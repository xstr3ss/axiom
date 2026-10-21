import os
import re
import json
import uuid
import logging
import subprocess
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from fastembed import TextEmbedding
from datasets import load_dataset

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("fable.harvester")

STATE_FILE = "memory_state.json"
COLLECTION_NAME = "fable_ast_memory"
VECTOR_DIM = 768

client = QdrantClient(host="localhost", port=6333)
embedding_model = TextEmbedding(model_name="BAAI/bge-base-en-v1.5")

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"processed_commits": [], "processed_external_ids": []}

def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def ensure_collection():
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        log.info(f"📦 Creating collection '{COLLECTION_NAME}' (dim={VECTOR_DIM})...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE)
        )

def upsert_points(items: list[dict]):
    if not items:
        return
    texts = [item["context"] for item in items]
    embeddings = list(embedding_model.embed(texts))
    points = []
    for item, vec in zip(items, embeddings):
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vec.tolist(),
            payload=item
        ))
    client.upsert(collection_name=COLLECTION_NAME, points=points)

def harvest_local_git_history(state: dict):
    log.info("🔍 [1/2] Scanning local repository history for historic bug fixes...")
    cmd = [
        "git", "log", "--grep=fix\\|bug\\|patch\\|resolve\\|error",
        "-i", "--pretty=format:%H%x00%s%x00", "-p"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 or not res.stdout.strip():
        log.info("ℹ️ No local bugfix commits found or not a git repository.")
        return

    raw_commits = res.stdout.split("\x00")
    items_to_store = []
    
    i = 0
    while i < len(raw_commits) - 2:
        commit_sha = raw_commits[i].strip()
        subject = raw_commits[i+1].strip()
        body_and_diff = raw_commits[i+2].strip()
        i += 2

        if not commit_sha or commit_sha in state["processed_commits"]:
            continue

        items_to_store.append({
            "signature": f"git_fix:{commit_sha[:8]}:{subject[:100]}",
            "context": f"Issue/Commit: {subject}\n\nDiff:\n{body_and_diff[:1500]}",
            "solution_patch": body_and_diff[:4000],
            "language": "python",
            "tags": ["local_git_history", "verified_fix"],
            "type": "episodic",
            "verified": True
        })
        state["processed_commits"].append(commit_sha)

    if items_to_store:
        upsert_points(items_to_store)
        save_state(state)
        log.info(f"✅ Ingested {len(items_to_store)} historical local bug fixes.")
    else:
        log.info("✅ All historical local commits are already up to date.")

def harvest_external_datasets(state: dict, batch_limit: int = 40):
    log.info(f"🌐 [2/2] Streaming verified external bugs (batch limit: {batch_limit})...")
    try:
        dataset = load_dataset("SWE-bench/SWE-bench", split="test", streaming=True)
    except Exception as e:
        log.warning(f"⚠️ Could not connect to Hugging Face dataset: {e}")
        return

    items_to_store = []
    count = 0

    for row in dataset:
        instance_id = row.get("instance_id")
        if not instance_id or instance_id in state["processed_external_ids"]:
            continue

        problem = row.get("problem_statement", "")
        patch = row.get("patch", "")
        if not problem or not patch:
            continue

        items_to_store.append({
            "signature": f"swebench:{instance_id}",
            "context": problem[:2000],
            "solution_patch": patch,
            "language": "python",
            "tags": ["swe_bench_lite", row.get("repo", "python")],
            "type": "episodic",
            "verified": True
        })
        state["processed_external_ids"].append(instance_id)
        count += 1

        if count >= batch_limit:
            break

    if items_to_store:
        upsert_points(items_to_store)
        save_state(state)
        log.info(f"✅ Ingested {len(items_to_store)} new verified bugs into memory.")
    else:
        log.info("✅ External dataset backlog is up to date.")

if __name__ == "__main__":
    ensure_collection()
    state = load_state()
    harvest_local_git_history(state)
    harvest_external_datasets(state, batch_limit=2500)
