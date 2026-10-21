import os
import glob
import subprocess
import torch
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

print("🔨 [Forge] Starting public dataset training process...")

# 1. Load existing LoRA weights if present so daily training is cumulative
if os.path.exists("fable_evolved_weights"):
    print("🧠 Found existing weights! Resuming training...")
    model_path = "fable_evolved_weights"
else:
    print("🌱 No previous weights found. Starting from Qwen2.5-Coder-7B base...")
    model_path = "unsloth/Qwen2.5-Coder-7B"

max_seq_length = 2048
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=model_path,
    max_seq_length=max_seq_length,
    dtype=None,
    load_in_4bit=True,
)

if not os.path.exists("fable_evolved_weights"):
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
    )

# 2. Read bookmark for today's 200-row slice
bookmark_file = "dataset_bookmark.txt"
if os.path.exists(bookmark_file):
    with open(bookmark_file, "r") as f:
        start_idx = int(f.read().strip())
else:
    start_idx = 0

batch_size = 200
end_idx = start_idx + batch_size

print(f"📥 Pulling public dataset rows {start_idx} to {end_idx}...")
# Train directly on Fable's distilled local dataset (0 API tokens consumed)
dataset_file = "distillation_dataset.jsonl"
if not os.path.exists(dataset_file) or os.path.getsize(dataset_file) == 0:
    print("⚠️ No local distillation records found. Nothing to train.")
    exit(0)

dataset = load_dataset("json", data_files=dataset_file, split="train"), split=f"train[{start_idx}:{end_idx}]")

def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    inputs       = examples["input"]
    outputs      = examples["output"]
    texts = []
    for instr, inp, out in zip(instructions, inputs, outputs):
        text = f"### Instruction:\n{instr}\n\n### Input:\n{inp}\n\n### Response:\n{out}"
        texts.append(text)
    return {"text": texts}

formatted_dataset = dataset.map(formatting_prompts_func, batched=True)

# 3. Train on today's chunk
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=formatted_dataset,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    dataset_num_proc=2,
    packing=False,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        max_steps=60,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=10,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir="outputs",
    ),
)

trainer.train()

# 4. Save checkpoint for tomorrow's Unsloth resume
model.save_pretrained("fable_evolved_weights")
tokenizer.save_pretrained("fable_evolved_weights")

with open(bookmark_file, "w") as f:
    f.write(str(end_idx))

print(f"✅ [Forge] Checkpoint saved! Bookmark moved to {end_idx}.")

# 5. Export to GGUF & auto-register with local Ollama for Fable Tier 1 Inference
try:
    print("📦 [Forge] Exporting 4-bit GGUF for Ollama...")
    model.save_pretrained_gguf("fable_gguf", tokenizer, quantization_method="q4_k_m")
    
    gguf_files = glob.glob("fable_gguf/*.gguf")
    if gguf_files:
        gguf_path = os.path.abspath(gguf_files[0])
        modelfile_content = f'''FROM {gguf_path}
PARAMETER temperature 0.2
SYSTEM """You are Fable, an autonomous self-healing software engineering model."""
'''
        with open("Modelfile.fable", "w") as mf:
            mf.write(modelfile_content)
            
        subprocess.run(["ollama", "create", "fable-evolved", "-f", "Modelfile.fable"], check=True)
        print("🚀 [Forge] Ollama model 'fable-evolved' updated and live for Tier 1 routing!")
except Exception as e:
    print(f"⚠️ [Forge] GGUF/Ollama export skipped or failed: {e}")
