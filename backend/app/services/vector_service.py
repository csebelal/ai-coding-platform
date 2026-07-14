from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PointStruct, 
    Filter, FieldCondition, MatchValue
)
from app.config import settings
import uuid
import logging

logger = logging.getLogger(__name__)

class VectorService:
    """Service for storing and searching code embeddings in Qdrant"""
    
    def __init__(self):
        self.client = QdrantClient(url=settings.QDRANT_URL)
    
    def ensure_collection(self, collection_name: str, vector_size: int = 1536):
        """Create collection if it doesn't exist"""
        try:
            self.client.get_collection(collection_name)
        except Exception:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection: {collection_name}")
    
    def upsert_symbols(self, collection_name: str, symbols: List[Dict[str, Any]], 
                       embeddings: List[List[float]]):
        """Store symbols with their embeddings"""
        points = []
        
        for symbol, embedding in zip(symbols, embeddings):
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "name": symbol.get("name"),
                    "symbol_type": symbol.get("symbol_type"),
                    "file_path": symbol.get("file_path"),
                    "start_line": symbol.get("start_line"),
                    "end_line": symbol.get("end_line"),
                    "content": symbol.get("content", "")[:1000],  # Limit content size
                    "parent_name": symbol.get("parent_name"),
                    "docstring": symbol.get("docstring", "")[:500] if symbol.get("docstring") else None,
                    "language": symbol.get("language"),
                    "line_count": symbol.get("line_count"),
                }
            )
            points.append(point)
        
        # Upsert in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=collection_name,
                points=batch
            )
        
        logger.info(f"Upserted {len(points)} points to {collection_name}")
    
    def upsert_files(self, collection_name: str, files: List[Dict[str, Any]], 
                     embeddings: List[List[float]], prefix: str = "file"):
        """Store file summaries with their embeddings"""
        points = []
        
        for file_data, embedding in zip(files, embeddings):
            point = PointStruct(
                id=f"{prefix}_{uuid.uuid4().hex[:8]}",
                vector=embedding,
                payload={
                    "file_path": file_data.get("file_path"),
                    "line_count": file_data.get("line_count"),
                    "symbol_count": len(file_data.get("symbols", [])),
                    "type": "file"
                }
            )
            points.append(point)
        
        if points:
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
        
        logger.info(f"Upserted {len(points)} file points to {collection_name}")
    
    def search(self, collection_name: str, query_embedding: List[float], 
               limit: int = 10, symbol_type: Optional[str] = None,
               language: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        query_filter = None
        
        conditions = []
        if symbol_type:
            conditions.append(FieldCondition(
                key="symbol_type",
                match=MatchValue(value=symbol_type)
            ))
        if language:
            conditions.append(FieldCondition(
                key="language",
                match=MatchValue(value=language)
            ))
        
        if conditions:
            query_filter = Filter(must=conditions)
        
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=limit,
            query_filter=query_filter
        )
        
        return [
            {
                "id": str(result.id),
                "score": result.score,
                **result.payload
            }
            for result in results
        ]
    
    def delete_collection(self, collection_name: str):
        """Delete a collection"""
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection information"""
        try:
            info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status,
            }
        except Exception:
            return {"name": collection_name, "vectors_count": 0, "points_count": 0}

# Singleton
vector_service = VectorService()
