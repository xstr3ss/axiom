import os
import shutil
import torch
from datetime import datetime
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTTrainer, SFTConfig
from peft import LoraConfig, get_peft_model

MODEL_PATH = "fable_evolved_weights"
DAILY_DATA = "distillation_dataset.jsonl"
ARCHIVE_DIR = "dataset_archives"

# 1. Check if there is actually anything to learn today
if not os.path.exists(DAILY_DATA) or os.path.getsize(DAILY_DATA) == 0:
    print(f"[{datetime.now()}] 💤 No new code logs today. Fable is resting.")
    exit(0)

print(f"[{datetime.now()}] 🧠 Waking up Fable. Loading local evolved brain...")

# 2. Load YOUR custom brain (Not the internet one)
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, torch_dtype=torch.float32)

# Attach LoRA adapters so your CPU doesn't melt
lora_config = LoraConfig(r=8, target_modules=["q_proj", "v_proj"], bias="none")
model = get_peft_model(model, lora_config)

# 3. Format today's logs
ds = load_dataset("json", data_files=DAILY_DATA, split="train")
def convert(ex):
    if "messages" in ex and ex["messages"]:
        return {"text": "".join([f"<|im_start|>{m.get('role','user')}\n{m.get('content','')}<|im_end|>\n" for m in ex["messages"]])}
    return {"text": ""}
ds = ds.map(convert, remove_columns=ds.column_names)

# 4. Do the Quick CPU Workout
print(f"[{datetime.now()}] ⚡ Training on {len(ds)} new records...")
sft_config = SFTConfig(
    output_dir="daily_outputs",
    max_seq_length=512,
    dataset_text_field="text",
    num_train_epochs=1, # Just runs through today's logs exactly once
    per_device_train_batch_size=1,
    learning_rate=2e-4,
    use_cpu=True,
    save_strategy="no"
)

trainer = SFTTrainer(model=model, processing_class=tokenizer, train_dataset=ds, args=sft_config)
trainer.train()

# 5. Save the smarter brain and archive the logs
print(f"[{datetime.now()}] 💾 Saving slightly smarter brain...")
model.save_pretrained(MODEL_PATH)
tokenizer.save_pretrained(MODEL_PATH)

os.makedirs(ARCHIVE_DIR, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.move(DAILY_DATA, os.path.join(ARCHIVE_DIR, f"distillation_{timestamp}.jsonl"))

print(f"[{datetime.now()}] ✅ Daily evolution complete. Shutting down forge.")
