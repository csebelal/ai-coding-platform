from typing import List, Dict, Any, Optional
import httpx
import numpy as np
from app.config import settings

class EmbeddingService:
    """Service for generating code embeddings"""
    
    # Embedding model dimensions
    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = "text-embedding-3-small"
        self.dimensions = self.MODEL_DIMENSIONS[self.model]
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if not self.api_key:
            # Return random embedding for testing
            return list(np.random.rand(self.dimensions).astype(float))
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "input": text[:8191],  # Max tokens limit
                },
                timeout=30.0,
            )
            
            if response.status_code != 200:
                raise Exception(f"Embedding API error: {response.status_code}")
            
            data = response.json()
            return data["data"][0]["embedding"]
    
    async def generate_embeddings(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not self.api_key:
            return [list(np.random.rand(self.dimensions).astype(float)) for _ in texts]
        
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "input": [t[:8191] for t in batch],
                    },
                    timeout=60.0,
                )
                
                if response.status_code != 200:
                    raise Exception(f"Embedding API error: {response.status_code}")
                
                data = response.json()
                embeddings = [item["embedding"] for item in data["data"]]
                all_embeddings.extend(embeddings)
        
        return all_embeddings
    
    def prepare_symbol_text(self, symbol: Dict[str, Any]) -> str:
        """Prepare text for symbol embedding"""
        parts = [
            f"Name: {symbol.get('name', '')}",
            f"Type: {symbol.get('symbol_type', '')}",
            f"File: {symbol.get('file_path', '')}",
        ]
        
        if symbol.get("docstring"):
            parts.append(f"Documentation: {symbol['docstring'][:500]}")
        
        if symbol.get("parameters"):
            parts.append(f"Parameters: {symbol['parameters']}")
        
        if symbol.get("content"):
            # Include first 500 chars of content
            parts.append(f"Code: {symbol['content'][:500]}")
        
        return "\n".join(parts)
    
    def prepare_file_text(self, file_path: str, symbols: List[Dict[str, Any]]) -> str:
        """Prepare text for file embedding"""
        parts = [f"File: {file_path}"]
        
        for symbol in symbols[:10]:  # Limit to 10 symbols
            parts.append(f"- {symbol.get('symbol_type', 'unknown')}: {symbol.get('name', 'unknown')}")
        
        return "\n".join(parts)

# Singleton
embedding_service = EmbeddingService()
