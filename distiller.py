import json
import logging
import os

log = logging.getLogger(__name__)

class Distiller:
    def __init__(self, dataset_path="distillation_dataset.jsonl", dpo_path="dpo_dataset.jsonl"):
        self.dataset_path = dataset_path
        self.dpo_path = dpo_path

    def save_golden_record(self, instruction: str, successful_code: str):
        """Backwards-compatible single-turn saver."""
        record = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are Fable, an autonomous AI coding agent. You MUST output code modifications using surgical SEARCH/REPLACE blocks."
                },
                {"role": "user", "content": instruction},
                {"role": "assistant", "content": successful_code}
            ]
        }
        with open(self.dataset_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        log.info("💧 [Distiller] Golden record captured for weight distillation.")

    def save_trajectory(self, conversation_messages: list[dict]):
        """Saves full step-by-step multi-turn tool and thought execution."""
        record = {"messages": conversation_messages}
        with open(self.dataset_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        log.info("💧 [Distiller] Full multi-turn agent trajectory recorded.")

    def save_dpo_pair(self, prompt: str, chosen: str, rejected: str):
        """Saves contrastive pairs from Z3/Critic rejections for preference training."""
        record = {
            "prompt": prompt,
            "chosen": chosen,
            "rejected": rejected
        }
        with open(self.dpo_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        log.info("⚖️ [Distiller] DPO preference pair recorded.")

# Backward compatibility alias for engine.py
DistillationEngine = Distiller

