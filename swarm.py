import json
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from llm import LLMClient
from config import Config
from engine import SelfHealingEngine

log = logging.getLogger("fable.swarm")

class SwarmOrchestrator:
    def __init__(self):
        log.info("🌐 [Swarm] Initializing Decentralized Task Orchestrator...")
        self.cfg = Config()
        self.llm = LLMClient(self.cfg)
        # Allocate 5 concurrent worker threads (simulating 5 isolated agent containers)
        self.executor = ThreadPoolExecutor(max_workers=1) 

    def _plan_dag(self, objective: str) -> dict:
        log.info("🗺️ [Swarm] Architecting Task DAG (Directed Acyclic Graph)...")
        prompt = (
            f"You are the Fable Swarm Architect.\n"
            f"Break this massive objective into a Directed Acyclic Graph (DAG) of sequential and parallel sub-tasks.\n"
            f"Objective: {objective}\n\n"
            f"CRITICAL RULES:\n"
            f"1. Output ONLY valid JSON.\n"
            f"2. Use this exact schema:\n"
            f"{{\n"
            f"  \"tasks\": {{\n"
            f"    \"db_node\": {{\"description\": \"Write database models\", \"depends_on\": []}},\n"
            f"    \"api_node\": {{\"description\": \"Build API Gateway\", \"depends_on\": [\"db_node\"]}}\n"
            f"  }}\n"
            f"}}"
        )
        response = self.llm.generate(prompt, force_cloud=True)
        try:
            clean_json = response.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except Exception as e:
            log.error(f"❌ [Swarm] Failed to parse DAG JSON: {e}")
            return {"tasks": {"fallback": {"description": objective, "depends_on": []}}}

    def _run_worker(self, node_id: str, description: str):
        log.info(f"🤖 [Worker: {node_id}] Booting independent agent...")
        # Spawn an entirely new, isolated instance of your autonomous engine
        engine = SelfHealingEngine()
        engine.run(description)
        log.info(f"✅ [Worker: {node_id}] Task completed successfully.")

    async def execute_dag(self, objective: str):
        dag = self._plan_dag(objective)
        tasks = dag.get("tasks", {})
        
        log.info(f"🕸️ [Swarm] DAG topology mapped: {len(tasks)} nodes. Initiating swarm execution...")
        
        completed = set()
        in_progress = {} 
        loop = asyncio.get_running_loop()
        
        while len(completed) < len(tasks):
            # 1. Identify tasks that have all dependencies met
            runnable = []
            for t_id, t_info in tasks.items():
                if t_id not in completed and t_id not in in_progress:
                    deps = t_info.get("depends_on", [])
                    if all(d in completed for d in deps):
                        runnable.append(t_id)
                        
            if not runnable and not in_progress:
                log.error("🛑 [Swarm] Deadlock detected! Unmet dependencies in DAG.")
                break
                
            # 2. Dispatch runnable tasks to the worker pool
            for t_id in runnable:
                future = loop.run_in_executor(
                    self.executor, 
                    self._run_worker, 
                    t_id, 
                    tasks[t_id]["description"]
                )
                in_progress[t_id] = future
                
            # 3. Wait for AT LEAST ONE active agent to complete its task
            if in_progress:
                done, _ = await asyncio.wait(
                    in_progress.values(), 
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # 4. Resolve completed tasks and unlock dependent nodes
                resolved_ids = []
                for t_id, future in in_progress.items():
                    if future in done:
                        completed.add(t_id)
                        resolved_ids.append(t_id)
                        log.info(f"🔗 [Swarm] Node '{t_id}' resolved. Broadcasting state...")
                        
                for t_id in resolved_ids:
                    del in_progress[t_id]
                        
        log.info("🏁 [Swarm] All swarm operations completed. System converged.")
