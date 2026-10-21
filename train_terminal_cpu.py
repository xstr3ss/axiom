import os
import inspect
import torch
from datasets import load_dataset, concatenate_datasets
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTTrainer, SFTConfig

print("==================================================")
print("💻 TERMINAL CPU TRAINING: 5-PILLAR UNIFIED MERGE")
print("==================================================")

model_id = "Qwen/Qwen2.5-Coder-1.5B"
print(f"🧠 Loading base model ({model_id}) for CPU execution...")

tokenizer = AutoTokenizer.from_pretrained(model_id)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    dtype=torch.float32,
    device_map="cpu"
)

# Attach lightweight LoRA adapters if PEFT is available to speed up CPU training
try:
    from peft import LoraConfig, get_peft_model
    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    model = get_peft_model(model, lora_config)
    print("⚡ LoRA adapters attached for faster CPU training!")
except Exception as e:
    print(f"ℹ️ Running standard CPU fine-tuning ({e})")

target_files = {
    "Pillar 1 (Trajectories)": "sft_1_trajectories.jsonl",
    "Pillar 2 (Traceback Recovery)": "sft_2_recovery.jsonl",
    "Pillar 3 (DPO Preferences)": "dpo_3_preferences.jsonl",
    "Pillar 4 (Z3 Logic Proofs)": "sft_4_z3_logic.jsonl",
    "Pillar 5 (Live Distillation)": "distillation_dataset.jsonl"
}

def normalize_to_text(example):
    # Handle standard SFT ChatML format (Pillars 1, 2, 4, 5)
    if "messages" in example and example["messages"]:
        text = ""
        for m in example["messages"]:
            text += f"<|im_start|>{m.get('role', 'user')}\n{m.get('content', '')}<|im_end|>\n"
        return {"text": text}
    # Handle DPO Preference format (Pillar 3)
    elif "prompt" in example and "chosen" in example:
        return {
            "text": f"<|im_start|>user\n{example['prompt']}<|im_end|>\n<|im_start|>assistant\n{example['chosen']}<|im_end|>\n"
        }
    return {"text": ""}

normalized_datasets = []

print("\n📚 Loading and normalizing each pillar individually to prevent column clashes...")
for pillar_name, path in target_files.items():
    if os.path.exists(path) and os.path.getsize(path) > 0:
        ds = load_dataset("json", data_files=path, split="train")
        # Strip original columns so every dataset shares the exact same {"text": string} schema
        ds_clean = ds.map(normalize_to_text, remove_columns=ds.column_names)
        normalized_datasets.append(ds_clean)
        print(f"   ✅ {pillar_name}: {len(ds_clean):,} records normalized")
    else:
        print(f"   ⚠️ {pillar_name} ({path}): Not found or empty, skipping")

if not normalized_datasets:
    print("❌ No valid datasets found.")
    exit(1)

print("\n📦 Concatenating all normalized pillars into master corpus...")
full_dataset = concatenate_datasets(normalized_datasets)
full_dataset = full_dataset.shuffle(seed=42)
print(f"🏆 Successfully merged {len(full_dataset):,} total records across all active pillars!")

# Dynamically build SFTConfig parameters to match your exact TRL version
sft_kwargs = {
    "output_dir": "fable_cpu_terminal_checkpoints",
    "per_device_train_batch_size": 1,
    "gradient_accumulation_steps": 4,
    "warmup_steps": 2,
    "max_steps": 20,
    "learning_rate": 2e-4,
    "logging_steps": 1,
    "use_cpu": True,
}

valid_sft_params = inspect.signature(SFTConfig.__init__).parameters
if "dataset_text_field" in valid_sft_params:
    sft_kwargs["dataset_text_field"] = "text"
if "max_length" in valid_sft_params:
    sft_kwargs["max_length"] = 512
elif "max_seq_length" in valid_sft_params:
    sft_kwargs["max_seq_length"] = 512

sft_config = SFTConfig(**sft_kwargs)

print("\n⚡ Starting Native CPU Training Loop...")
trainer = SFTTrainer(
    model=model,
    processing_class=tokenizer,
    train_dataset=full_dataset,
    args=sft_config,
)

trainer.train()

print("\n💾 Saving Fully Evolved 5-Pillar Weights...")
model.save_pretrained("fable_evolved_weights")
tokenizer.save_pretrained("fable_evolved_weights")
print("✅ All active pillars successfully baked into 'fable_evolved_weights'!")
