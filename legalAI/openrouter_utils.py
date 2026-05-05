import requests
from django.conf import settings
import time

_CACHED_FREE_MODELS = []
_LAST_FETCH_TIME = 0

def get_free_models():
    global _CACHED_FREE_MODELS, _LAST_FETCH_TIME
    if time.time() - _LAST_FETCH_TIME < 3600 and _CACHED_FREE_MODELS:
        return _CACHED_FREE_MODELS

    try:
        response = requests.get("https://openrouter.ai/api/v1/models")
        if response.status_code == 200:
            models = response.json().get('data', [])
            _CACHED_FREE_MODELS = [m['id'] for m in models if ':free' in m['id']]
            # Prioritize the absolute smartest models (400B+, 70B+) to prevent hallucinations
            preferred = [
                "nousresearch/hermes-3-llama-3.1-405b:free",
                "meta-llama/llama-3.3-70b-instruct:free",
                "qwen/qwen3-next-80b-a3b-instruct:free",
                "google/gemma-4-31b-it:free",
                "google/gemma-3-27b-it:free",
                "meta-llama/llama-3.2-3b-instruct:free"
            ]
            for p in preferred:
                if p in _CACHED_FREE_MODELS:
                    _CACHED_FREE_MODELS.insert(0, _CACHED_FREE_MODELS.pop(_CACHED_FREE_MODELS.index(p)))
            _LAST_FETCH_TIME = time.time()
            return _CACHED_FREE_MODELS
    except Exception:
        pass
    return [
        "nousresearch/hermes-3-llama-3.1-405b:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "qwen/qwen3-next-80b-a3b-instruct:free"
    ]

def call_openrouter_free(prompt, system_prompt="You are a helpful assistant.", max_tokens=2000):
    api_key = getattr(settings, 'OPENROUTER_API_KEY', None)
    if not api_key:
        import os
        api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return "Error: OPENROUTER_API_KEY is not set."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    free_models = get_free_models()
    
    last_error = ""
    # Try up to 5 models sequentially
    for model in free_models[:5]:
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens
        }

        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                last_error = f"{response.status_code} Error from {model}"
                print(f"Failed {model}: {response.text}")
        except Exception as e:
            last_error = str(e)
            
    # Ultimate Fallback: G4F if OpenRouter rate limits us
    try:
        from g4f.client import Client
        import g4f
        client = Client()
        g4f_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        answer = g4f_response.choices[0].message.content
        import re
        # Remove g4f ads and default provider identities
        if "Need proxies cheaper" in answer:
            answer = answer.split("Need proxies cheaper")[0].strip()
        if "https://op.wtf" in answer:
            answer = answer.replace("https://op.wtf", "").strip()
            
        # Replace Opera Aria intro with our Legal AI intro
        answer = re.sub(
            r"Hello there! I'm Aria.*?information you need[.!]*", 
            "Hello! I am your AI Legal Assistant, designed to provide quick and accurate information related to Indian laws.\n", 
            answer, 
            flags=re.IGNORECASE | re.DOTALL
        )
        
        return answer
    except Exception as e2:
        return f"Error connecting to AI service. Tried multiple free models. Please try again later. Last Error: {last_error} | Fallback Error: {str(e2)}"
