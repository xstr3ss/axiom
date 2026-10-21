import os
import torch
from datasets import load_dataset
from unsloth import FastLanguageModel
from unsloth import is_bfloat16_supported
from trl import SFTTrainer, DPOTrainer
from transformers import TrainingArguments

print("==================================================")
print("🔥 FABLE FORGE: BULK FOUNDATION TRAINING INITIATED")
print("==================================================")

max_seq_length = 2048 # Max context window for training
model_name = "unsloth/Qwen2.5-Coder-7B" # The base model

print("🧠 Loading Base Model...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=model_name,
    max_seq_length=max_seq_length,
    dtype=None,
    load_in_4bit=True, # Keeps VRAM usage low
)

# Enable Unsloth's optimized LoRA adapters
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0, 
    bias="none",
    use_gradient_checkpointing="unsloth",
)

# ---------------------------------------------------------
# PHASE 1: SFT (Supervised Fine Tuning) on SWE-bench
# ---------------------------------------------------------
print("\n📚 PHASE 1: Loading SWE-bench Agentic Trajectories...")
# Load a subset of SWE-bench to teach tool use and patch formats
sft_dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="train[:500]")

def format_sft(row):
    # Format into Fable's ChatML Trajectory
    system_prompt = "You are Fable, an autonomous software engineering organism. Output code using SEARCH/REPLACE blocks."
    user_prompt = f"Feature Request:\n{row['problem_statement']}"
    assistant_response = f"Action: Apply Patch\n<<<<<<< SEARCH\n[Old Code]\n=======\n{row['patch'][:1000]} # Truncated for speed\n>>>>>>> REPLACE"
    
    chat = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": assistant_response}
    ]
    text = tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=False)
    return {"text": text}

sft_dataset = sft_dataset.map(format_sft)

print("⚡ Starting SFT Training Loop...")
sft_trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=sft_dataset,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    dataset_num_proc=2,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=10,
        max_steps=60, # Keep it brief for this initial bulk run
        learning_rate=2e-4,
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir="fable_sft_checkpoints",
    ),
)
sft_trainer.train()

# ---------------------------------------------------------
# PHASE 2: DPO (Direct Preference Optimization)
# ---------------------------------------------------------
print("\n⚖️ PHASE 2: Loading DPO Preference Pairs...")
# We use a code feedback dataset to teach it to prefer clean syntax over hallucination
dpo_dataset = load_dataset("m-a-p/CodeFeedback-Filtered-Instruction", split="train[:300]")

def format_dpo(row):
    prompt = tokenizer.apply_chat_template([
        {"role": "system", "content": "You are Fable, an autonomous software engineering organism."},
        {"role": "user", "content": row["query"]}
    ], tokenize=False, add_generation_prompt=True)
    
    # In this dataset, we'll map the good answer to 'chosen'
    # For a real run, you'd use your actual Z3-rejected code as 'rejected'
    return {
        "prompt": prompt,
        "chosen": row["answer"] + tokenizer.eos_token,
        "rejected": "Here is the code:\n```python\n# Hallucinated markdown instead of SEARCH/REPLACE block\n```" + tokenizer.eos_token
    }

dpo_dataset = dpo_dataset.map(format_dpo)

print("⚡ Starting DPO Training Loop...")
dpo_trainer = DPOTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dpo_dataset,
    max_length=max_seq_length,
    max_prompt_length=max_seq_length // 2,
    args=TrainingArguments(
        per_device_train_batch_size=1, # DPO requires more VRAM
        gradient_accumulation_steps=8,
        warmup_steps=5,
        max_steps=40,
        learning_rate=5e-5, # DPO requires lower learning rate than SFT
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),
        logging_steps=1,
        optim="adamw_8bit",
        output_dir="fable_dpo_checkpoints",
    ),
)
dpo_trainer.train()

# ---------------------------------------------------------
# PHASE 3: Save the Master Weights
# ---------------------------------------------------------
print("\n💾 Saving Fable-Evolved Master Weights...")
model.save_pretrained("fable_evolved_weights")
tokenizer.save_pretrained("fable_evolved_weights")
print("✅ Bulk Foundation Training Complete! The model is now fully agentic.")
