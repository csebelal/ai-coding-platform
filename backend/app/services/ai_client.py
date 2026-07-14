from dataclasses import dataclass
from typing import Optional, Dict, Any
import httpx
from app.config import settings

@dataclass
class AIResponse:
    content: str
    model: str
    usage: Dict[str, int]
    
    @property
    def total_tokens(self) -> int:
        return self.usage.get("total_tokens", 0)

class AIClient:
    """Client for calling AI provider APIs directly"""
    
    PROVIDERS = {
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1",
            "api_key": settings.DEEPSEEK_API_KEY,
        },
        "gemini": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta",
            "api_key": settings.GEMINI_API_KEY,
        },
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "api_key": settings.OPENAI_API_KEY,
        },
    }
    
    MODEL_COSTS = {
        "deepseek/deepseek-chat": {"input": 0.00014, "output": 0.00028},
        "deepseek/deepseek-coder": {"input": 0.00014, "output": 0.00028},
        "google/gemini-flash": {"input": 0.000075, "output": 0.0003},
        "openai/gpt-4o": {"input": 0.0025, "output": 0.01},
    }
    
    async def generate(
        self,
        system: str,
        user: str,
        model: str = "deepseek/deepseek-chat",
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> AIResponse:
        """Generate a completion from an AI model"""
        provider_name = model.split("/")[0]
        provider_config = self.PROVIDERS.get(provider_name)
        
        if not provider_config or not provider_config.get("api_key"):
            raise ValueError(f"Provider {provider_name} not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{provider_config['base_url']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {provider_config['api_key']}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model.split("/")[-1],
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=120.0,
            )
            
            if response.status_code != 200:
                raise Exception(f"AI API error: {response.status_code} - {response.text}")
            
            data = response.json()
            
            return AIResponse(
                content=data["choices"][0]["message"]["content"],
                model=model,
                usage=data.get("usage", {}),
            )
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a completion"""
        costs = self.MODEL_COSTS.get(model, {"input": 0.001, "output": 0.002})
        return (input_tokens * costs["input"] + output_tokens * costs["output"]) / 1000

# Singleton
ai_client = AIClient()
