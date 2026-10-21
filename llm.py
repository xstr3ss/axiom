from __future__ import annotations
import os, requests, time, logging, json, re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import Config

def get_evolved_local_model(default_model: str = "qwen2.5-coder:3b") -> str:
    return os.getenv("FABLE_LOCAL_MODEL", default_model)

log = logging.getLogger("fable.llm")

class LLMClient:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._local_down_until = 0.0
        self.session = requests.Session()
        retry = Retry(total=2, backoff_factor=0.5, status_forcelist=(500, 502, 503, 504))
        adapter = HTTPAdapter(max_retries=retry, pool_connections=4, pool_maxsize=8)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.system_prompt = (
            "You are Fable, an autonomous AI software engineering engine. "
            "Follow instructions strictly. Output no conversational filler."
        )

    def _detect_agent_role(self, prompt: str) -> str:
        """🧠 SMART ROUTER: Identifies which Agent is asking for compute."""
        p = prompt.lower()
        if "ls -la" in p or "cat " in p or "investigate" in p:
            return "Explorer"
        elif "constructive analysis" in p or "review" in p:
            return "Critic"
        elif "fix the code" in p or "repair" in p:
            return "Healer"
        elif "implement this feature" in p or "interface contract" in p:
            return "Coder"
        return "General"

    def get_local_response(self, prompt: str, agent_role: str = "General", timeout: int = 300) -> str:
        url = "http://localhost:11434/api/chat"
        model_name = get_evolved_local_model(self.cfg.local_model)
        payload = {"model": model_name, "messages": [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": prompt}], "options": {"temperature": 0.1, "num_ctx": 8192, "num_predict": 4096}, "stream": True}
        try:
            print(f"\n🧠 [Local SLM (3B) | {agent_role}] Context loaded...", flush=True)
            res = self.session.post(url, json=payload, timeout=timeout, stream=True)
            res.raise_for_status()
            full_response = ""
            for line in res.iter_lines():
                if line:
                    chunk = json.loads(line).get("message", {}).get("content", "")
                    full_response += chunk
            return full_response
        except Exception as e:
            return ""

    def get_cloud_response(self, prompt: str, agent_role: str = "General") -> str:
        api_key = os.getenv("GROQ_API_KEY", self.cfg.groq_api_key).strip()
        if not api_key: return ""

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        
        # 🚀 STRICT BLUEPRINT ROUTING: The high-IQ models handle the heavy lifting
        queue = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b", "allam-2-7b"]

        for current_model in queue:
            max_tokens = 512 if "guard" in current_model.lower() else 2048
            payload = {"model": current_model, "messages": [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": prompt}], "temperature": self.cfg.temperature, "max_tokens": max_tokens}
            
            for attempt in range(5):
                try:
                    res = self.session.post(self.cfg.cloud_url, headers=headers, json=payload, timeout=self.cfg.cloud_timeout)
                    if res.status_code == 200:
                        return res.json()["choices"][0]["message"]["content"]

                    err_msg = res.text.lower()
                    if res.status_code == 429:
                        wait_match = re.search(r'try again in ([0-9.]+)s', err_msg)
                        wait_time = float(wait_match.group(1)) + 1.0 if wait_match else 5.0
                        log.warning(f"⏳ [Cloud Brain (120B) | {agent_role}] TPM Limit hit for {current_model}. Groq acting as supporter, resting for {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        continue 
                    
                    if res.status_code == 413 or "length" in err_msg or "too large" in err_msg:
                        content = payload["messages"][-1]["content"]
                        payload["messages"][-1]["content"] = content[:1500] + "\n\n...[TRUNCATED]...\n\n" + content[-1500:]
                        continue 
                            
                    if res.status_code in [400, 404]:
                        break 
                    break 
                except Exception as e:
                    break 
        return ""

    def generate(self, prompt: str, force_cloud: bool = False, slow: bool = False) -> str:
        """The main router utilized by Explorer, Coder, and Critic."""
        if len(prompt) > 15000:
            prompt = prompt[:5000] + "\n\n...[TRUNCATED REPO CONTEXT]...\n\n" + prompt[-5000:]

        agent_role = self._detect_agent_role(prompt)
        has_cloud_key = bool(os.getenv("GROQ_API_KEY", self.cfg.groq_api_key).strip())
        
        skip_local = self.cfg.prefer_cloud or (force_cloud and has_cloud_key)
        
        # Override for high-logic roles if cloud keys exist
        if agent_role in ["Coder", "Critic", "Healer"] and has_cloud_key:
            skip_local = True

        raw_output = ""

        if not skip_local and time.monotonic() >= self._local_down_until:
            for attempt in range(1, self.cfg.local_retries + 1):
                try:
                    raw_output = self.get_local_response(prompt, agent_role, self.cfg.local_timeout)
                    if raw_output.strip(): break
                except: pass
                time.sleep(0.5 * attempt)
            if not raw_output.strip():
                self._local_down_until = time.monotonic() + self.cfg.local_cooldown

        if not raw_output.strip() and has_cloud_key:
            raw_output = self.get_cloud_response(prompt, agent_role)

        if "<tool_call>" in raw_output:
            raw_output = raw_output.split("<tool_call>")[0]
        return raw_output
