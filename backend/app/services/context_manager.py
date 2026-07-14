from typing import List, Dict, Any, Optional
import json
import logging

from app.agents.base import AgentContext, ContextBudget
from app.services.vector_service import vector_service
from app.services.embedding_service import embedding_service
from app.memory import conversation_memory, repository_memory

logger = logging.getLogger(__name__)

class ContextManager:
    """
    Manages context for agents.
    
    Responsibilities:
    - Build minimal context for agents
    - Manage token budgets
    - Retrieve relevant files and symbols
    - Maintain conversation history
    """
    
    def __init__(self):
        self.context_cache: Dict[str, AgentContext] = {}
    
    async def build_context(
        self,
        task_id: str,
        project_id: str,
        description: str,
        agent_type: str,
        previous_results: Optional[Dict[str, Any]] = None,
        token_budget: int = 8000
    ) -> AgentContext:
        """
        Build context for an agent.
        
        This is the main entry point for context building.
        """
        logger.info(f"Building context for task {task_id}, agent {agent_type}")
        
        # Get project info
        project = self._get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Create context
        context = AgentContext(
            task_id=task_id,
            project_id=project_id,
            description=description,
            repository_path=project.get("local_path"),
            previous_results=previous_results or {},
            token_budget=ContextBudget(total_tokens=token_budget)
        )
        
        # Get repository card
        context.repository_card = await self._get_repository_card(project_id)
        
        # Get relevant files
        context.relevant_files = await self._get_relevant_files(
            project_id, description, context.token_budget
        )
        
        # Get relevant symbols
        context.relevant_symbols = await self._get_relevant_symbols(
            project_id, description, context.token_budget
        )
        
        # Get conversation history
        context.conversation_history = self._get_conversation_history()
        
        # Cache context
        self.context_cache[task_id] = context
        
        logger.info(f"Context built: {context.token_budget.used_tokens} tokens used")
        
        return context
    
    def _get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project info"""
        # This would normally query the database
        # For now, return a basic structure
        return {"id": project_id, "local_path": None}
    
    async def _get_repository_card(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get or generate repository card"""
        # Check memory first
        card = repository_memory.get_repository_card(project_id)
        if card:
            return card
        
        # Generate new card
        collection_name = f"repo_{project_id}"
        try:
            info = vector_service.get_collection_info(collection_name)
            card = {
                "project_id": project_id,
                "indexed": info.get("points_count", 0) > 0,
                "total_symbols": info.get("points_count", 0),
                "collection": collection_name
            }
            repository_memory.store_repository_card(project_id, card)
            return card
        except Exception as e:
            logger.error(f"Failed to get repository card: {e}")
            return None
    
    async def _get_relevant_files(
        self, project_id: str, description: str, budget: ContextBudget
    ) -> List[Dict[str, Any]]:
        """Get files relevant to the task"""
        relevant_files = []
        
        # Generate query embedding
        query_embedding = await embedding_service.generate_embedding(description)
        
        # Search for relevant files
        collection_name = f"repo_{project_id}"
        try:
            results = vector_service.search(
                collection_name=collection_name,
                query_embedding=query_embedding,
                limit=5
            )
            
            for result in results:
                # Estimate token count
                estimated_tokens = len(json.dumps(result)) // 4
                if budget.allocate(estimated_tokens):
                    relevant_files.append(result)
        except Exception as e:
            logger.error(f"Failed to get relevant files: {e}")
        
        return relevant_files
    
    async def _get_relevant_symbols(
        self, project_id: str, description: str, budget: ContextBudget
    ) -> List[Dict[str, Any]]:
        """Get symbols relevant to the task"""
        relevant_symbols = []
        
        # Generate query embedding
        query_embedding = await embedding_service.generate_embedding(description)
        
        # Search for relevant symbols
        collection_name = f"repo_{project_id}"
        try:
            results = vector_service.search(
                collection_name=collection_name,
                query_embedding=query_embedding,
                limit=10
            )
            
            for result in results:
                # Estimate token count
                estimated_tokens = len(json.dumps(result)) // 4
                if budget.allocate(estimated_tokens):
                    relevant_symbols.append(result)
        except Exception as e:
            logger.error(f"Failed to get relevant symbols: {e}")
        
        return relevant_symbols
    
    def _get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        entries = conversation_memory.get_recent(5)
        return [e.to_dict() for e in entries]
    
    def get_cached_context(self, task_id: str) -> Optional[AgentContext]:
        """Get cached context for a task"""
        return self.context_cache.get(task_id)
    
    def clear_cache(self, task_id: Optional[str] = None):
        """Clear context cache"""
        if task_id:
            self.context_cache.pop(task_id, None)
        else:
            self.context_cache.clear()

# Singleton
context_manager = ContextManager()
