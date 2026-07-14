from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import os
import logging

from app.services.symbol_extractor import SymbolExtractor, Symbol
from app.services.git_service import git_service

logger = logging.getLogger(__name__)

@dataclass
class FileIndex:
    """Index data for a single file"""
    file_path: str
    language: str
    symbols: List[Symbol]
    line_count: int
    size_bytes: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "language": self.language,
            "symbols": [s.to_dict() for s in self.symbols],
            "line_count": self.line_count,
            "size_bytes": self.size_bytes
        }

@dataclass
class RepositoryIndex:
    """Complete index of a repository"""
    project_id: str
    repo_path: str
    files: List[FileIndex]
    total_symbols: int = 0
    total_lines: int = 0
    languages: Dict[str, int] = field(default_factory=dict)
    summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "repo_path": self.repo_path,
            "files": [f.to_dict() for f in self.files],
            "total_symbols": self.total_symbols,
            "total_lines": self.total_lines,
            "languages": self.languages,
            "summary": self.summary
        }

class RepositoryIndexer:
    """Index a repository for code search and analysis"""
    
    def __init__(self):
        self.symbol_extractor = SymbolExtractor()
    
    def index_repository(self, project_id: str, repo_path: str) -> RepositoryIndex:
        """
        Index an entire repository.
        
        Args:
            project_id: Unique project identifier
            repo_path: Local path to the repository
            
        Returns:
            RepositoryIndex with all symbols and metadata
        """
        logger.info(f"Starting repository index for {project_id}")
        
        files = []
        total_symbols = 0
        total_lines = 0
        languages = {}
        
        # Get all files in the repository
        file_paths = git_service.get_file_tree(repo_path)
        
        for file_path in file_paths:
            # Read the file
            content = git_service.read_file(repo_path, file_path)
            if not content:
                continue
            
            # Extract symbols
            symbols = self.symbol_extractor.extract_symbols(file_path, content)
            
            # Get file info
            full_path = os.path.join(repo_path, file_path)
            try:
                size_bytes = os.path.getsize(full_path)
            except OSError:
                size_bytes = 0
            
            line_count = content.count('\n') + 1
            
            # Detect language
            language = self._detect_language(file_path)
            
            # Create file index
            file_index = FileIndex(
                file_path=file_path,
                language=language,
                symbols=symbols,
                line_count=line_count,
                size_bytes=size_bytes
            )
            files.append(file_index)
            
            # Update stats
            total_symbols += len(symbols)
            total_lines += line_count
            languages[language] = languages.get(language, 0) + 1
        
        # Create repository index
        repo_index = RepositoryIndex(
            project_id=project_id,
            repo_path=repo_path,
            files=files,
            total_symbols=total_symbols,
            total_lines=total_lines,
            languages=languages
        )
        
        # Generate summary
        repo_index.summary = self._generate_summary(repo_index)
        
        logger.info(f"Index complete: {total_symbols} symbols in {len(files)} files")
        
        return repo_index
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".sql": "sql",
            ".sh": "shell",
            ".bash": "shell",
            ".md": "markdown",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".xml": "xml",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
        }
        ext = os.path.splitext(file_path)[1].lower()
        return ext_map.get(ext, "other")
    
    def _generate_summary(self, index: RepositoryIndex) -> str:
        """Generate a summary of the repository"""
        # Count symbols by type
        symbol_counts = {}
        for file_index in index.files:
            for symbol in file_index.symbols:
                symbol_counts[symbol.symbol_type] = symbol_counts.get(symbol.symbol_type, 0) + 1
        
        # Build summary
        summary_parts = [
            f"Repository with {len(index.files)} files",
            f"{index.total_symbols} symbols",
            f"{index.total_lines} lines of code",
            f"Languages: {', '.join(f'{k} ({v})' for k, v in index.languages.items())}",
        ]
        
        if symbol_counts:
            symbol_summary = ", ".join(f"{count} {sym_type}s" for sym_type, count in symbol_counts.items())
            summary_parts.append(f"Symbols: {symbol_summary}")
        
        return ". ".join(summary_parts)
    
    def search_symbols(self, index: RepositoryIndex, query: str, 
                       symbol_type: Optional[str] = None,
                       language: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for symbols in the index.
        
        Args:
            index: Repository index to search
            query: Search query (matches name)
            symbol_type: Filter by symbol type
            language: Filter by language
            
        Returns:
            List of matching symbols
        """
        results = []
        query_lower = query.lower()
        
        for file_index in index.files:
            # Filter by language if specified
            if language and file_index.language != language:
                continue
            
            for symbol in file_index.symbols:
                # Filter by symbol type if specified
                if symbol_type and symbol.symbol_type != symbol_type:
                    continue
                
                # Match query against name
                if query_lower in symbol.name.lower():
                    results.append({
                        **symbol.to_dict(),
                        "relevance": self._calculate_relevance(symbol, query_lower)
                    })
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance"], reverse=True)
        
        return results
    
    def _calculate_relevance(self, symbol: Symbol, query: str) -> float:
        """Calculate relevance score for a symbol match"""
        score = 0.0
        
        # Exact match
        if symbol.name.lower() == query:
            score += 100
        # Starts with query
        elif symbol.name.lower().startswith(query):
            score += 50
        # Contains query
        elif query in symbol.name.lower():
            score += 25
        
        # Boost for shorter names (more specific)
        score += max(0, 20 - len(symbol.name))
        
        return score
    
    def get_file_symbols(self, index: RepositoryIndex, file_path: str) -> List[Symbol]:
        """Get all symbols in a specific file"""
        for file_index in index.files:
            if file_index.file_path == file_path:
                return file_index.symbols
        return []
    
    def get_context_for_task(self, index: RepositoryIndex, task_description: str, 
                             max_files: int = 10) -> List[Dict[str, Any]]:
        """
        Get relevant context for a task description.
        
        This is a simple keyword-based relevance matcher.
        For production, use vector embeddings for better matching.
        """
        # Extract keywords from task description
        keywords = task_description.lower().split()
        keywords = [w for w in keywords if len(w) > 3]  # Filter short words
        
        scored_files = []
        
        for file_index in index.files:
            score = 0
            
            # Check file path for keywords
            for keyword in keywords:
                if keyword in file_index.file_path.lower():
                    score += 10
            
            # Check symbols for keywords
            for symbol in file_index.symbols:
                for keyword in keywords:
                    if keyword in symbol.name.lower():
                        score += 5
                    if symbol.docstring and keyword in symbol.docstring.lower():
                        score += 2
            
            if score > 0:
                scored_files.append({
                    "file_path": file_index.file_path,
                    "score": score,
                    "symbols": [s.to_dict() for s in file_index.symbols[:5]],  # Top 5 symbols
                    "line_count": file_index.line_count
                })
        
        # Sort by score and return top files
        scored_files.sort(key=lambda x: x["score"], reverse=True)
        return scored_files[:max_files]

# Singleton
repository_indexer = RepositoryIndexer()
