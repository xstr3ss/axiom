import os
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="Axiom Pro Cloud Gateway")

# In production, validate against Polar.sh API or your database of active subscribers
VALID_PRO_KEYS = {
    "AXIOM-PRO-DEMO-2026": {"plan": "pro", "tokens_used": 0, "monthly_limit": 500000}
}

class ProInferenceRequest(BaseModel):
    prompt: str
    agent_role: str = "Cloud_Brain"

@app.post("/v1/pro/complete")
def pro_completion(req: ProInferenceRequest, x_axiom_key: str = Header(None)):
    if not x_axiom_key or x_axiom_key not in VALID_PRO_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or expired Axiom Pro License Key.")

    sub = VALID_PRO_KEYS[x_axiom_key]
    est_tokens = len(req.prompt) // 4
    if sub["tokens_used"] + est_tokens > sub["monthly_limit"]:
        raise HTTPException(status_code=429, detail="Monthly Axiom Pro token quota exceeded.")

    sub["tokens_used"] += est_tokens

    # Execute using your Master Backend Groq/OpenAI Key
    from groq import Groq
    master_client = Groq(api_key=os.getenv("MASTER_GROQ_API_KEY") or os.getenv("GROQ_API_KEY"))
    completion = master_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": req.prompt}],
        temperature=0.1
    )
    return {
        "response": completion.choices[0].message.content,
        "tokens_remaining": sub["monthly_limit"] - sub["tokens_used"]
    }
