from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    """A single memory entry"""
    id: str
    content: str
    entry_type: str  # "conversation", "decision", "error", "learning"
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "entry_type": self.entry_type,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

class ConversationMemory:
    """Manages conversation history and learning"""
    
    def __init__(self):
        self.entries: List[MemoryEntry] = []
        self.max_entries = 100
    
    def add_entry(self, content: str, entry_type: str, 
                  metadata: Optional[Dict[str, Any]] = None) -> MemoryEntry:
        """Add a new memory entry"""
        import uuid
        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            content=content,
            entry_type=entry_type,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        self.entries.append(entry)
        
        # Trim if too many entries
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]
        
        return entry
    
    def get_recent(self, count: int = 10, entry_type: Optional[str] = None) -> List[MemoryEntry]:
        """Get recent memory entries"""
        entries = self.entries
        if entry_type:
            entries = [e for e in entries if e.entry_type == entry_type]
        return entries[-count:]
    
    def get_context_summary(self) -> str:
        """Get a summary of recent context"""
        recent = self.get_recent(5)
        if not recent:
            return "No recent context."
        
        summary_parts = []
        for entry in recent:
            summary_parts.append(f"- {entry.entry_type}: {entry.content[:100]}")
        
        return "\n".join(summary_parts)

class RepositoryMemory:
    """Manages repository-specific memory and context"""
    
    def __init__(self):
        self.repositories: Dict[str, Dict[str, Any]] = {}
    
    def store_repository_card(self, project_id: str, card: Dict[str, Any]):
        """Store a repository card"""
        self.repositories[project_id] = {
            "card": card,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def get_repository_card(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a repository card"""
        if project_id in self.repositories:
            return self.repositories[project_id].get("card")
        return None
    
    def store_file_summary(self, project_id: str, file_path: str, summary: Dict[str, Any]):
        """Store a file summary"""
        if project_id not in self.repositories:
            self.repositories[project_id] = {"files": {}}
        
        if "files" not in self.repositories[project_id]:
            self.repositories[project_id]["files"] = {}
        
        self.repositories[project_id]["files"][file_path] = summary
    
    def get_file_summary(self, project_id: str, file_path: str) -> Optional[Dict[str, Any]]:
        """Get a file summary"""
        repo = self.repositories.get(project_id, {})
        files = repo.get("files", {})
        return files.get(file_path)

# Singletons
conversation_memory = ConversationMemory()
repository_memory = RepositoryMemory()
