import os
import shutil
from datetime import datetime
import torch
from datasets import load_dataset, concatenate_datasets
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
from peft import LoraConfig, get_peft_model

print("==================================================")
print("🚀 FABLE MASTER FORGE: 5-PILLAR PURE PYTORCH CPU ENGINE")
print("==================================================")

model_id = "Qwen/Qwen2.5-Coder-1.5B"
weights_dir = "fable_evolved_weights"

print(f"🧠 Loading base model ({model_id}) for pure PyTorch CPU execution...")
tokenizer = AutoTokenizer.from_pretrained(model_id)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    dtype=torch.float32,
    device_map="cpu"
)

lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, lora_config)
print("⚡ LoRA adapters attached!")

target_files = {
    "Pillar 1 (Trajectories)": "sft_1_trajectories.jsonl",
    "Pillar 2 (Traceback Recovery)": "sft_2_recovery.jsonl",
    "Pillar 3 (DPO Preferences)": "dpo_3_preferences.jsonl",
    "Pillar 4 (Z3 Logic Proofs)": "sft_4_z3_logic.jsonl",
    "Pillar 5 (Live Distillation)": "distillation_dataset.jsonl"
}

def normalize_to_text(example):
    if "messages" in example and example["messages"]:
        text = ""
        for m in example["messages"]:
            text += f"<|im_start|>{m.get('role', 'user')}\n{m.get('content', '')}<|im_end|>\n"
        return {"text": text}
    elif "prompt" in example and "chosen" in example:
        return {
            "text": f"<|im_start|>user\n{example['prompt']}<|im_end|>\n<|im_start|>assistant\n{example['chosen']}<|im_end|>\n"
        }
    return {"text": ""}

normalized_datasets = []
print("\n📚 Loading and normalizing all 5 pillars...")
for pillar_name, path in target_files.items():
    if os.path.exists(path) and os.path.getsize(path) > 0:
        ds = load_dataset("json", data_files=path, split="train")
        ds_clean = ds.map(normalize_to_text, remove_columns=ds.column_names)
        normalized_datasets.append(ds_clean)
        print(f"   ✅ {pillar_name}: {len(ds_clean):,} records normalized")

if not normalized_datasets:
    print("⚠️ No datasets found to train. Exiting cleanly.")
    exit(0)

full_dataset = concatenate_datasets(normalized_datasets).shuffle(seed=42)
print(f"\n🏆 Merged {len(full_dataset):,} total records across all 5 pillars!")

# On-the-fly tokenizer collator (skips 2-minute upfront tokenization & avoids Triton)
def cpu_data_collator(features):
    texts = [f["text"] for f in features]
    batch = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt"
    )
    labels = batch["input_ids"].clone()
    if tokenizer.pad_token_id is not None:
        labels[labels == tokenizer.pad_token_id] = -100
    batch["labels"] = labels
    return batch

print("\n⚡ Starting Pure PyTorch CPU Training Loop (No Triton Kernels)...")
training_args = TrainingArguments(
    output_dir="fable_cpu_terminal_checkpoints",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    warmup_steps=2,
    max_steps=20,
    learning_rate=2e-4,
    logging_steps=1,
    use_cpu=True,
    remove_unused_columns=False,
    report_to="none"
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=full_dataset,
    data_collator=cpu_data_collator,
)

trainer.train()

print(f"\n💾 Saving Evolved 5-Pillar Weights to '{weights_dir}'...")
model.save_pretrained(weights_dir)
tokenizer.save_pretrained(weights_dir)

# Archive live distillation dataset so future reboots don't retrain on duplicate daily logs
archive_dir = "dataset_archives"
os.makedirs(archive_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

if os.path.exists("distillation_dataset.jsonl") and os.path.getsize("distillation_dataset.jsonl") > 0:
    archive_name = os.path.join(archive_dir, f"distillation_archive_{timestamp}.jsonl")
    shutil.move("distillation_dataset.jsonl", archive_name)
    print(f"🗄️ Archived live distillation log to: {archive_name}")

print("✅ ALL 5 PILLARS TRAINED AND SAVED SUCCESSFULLY!")
