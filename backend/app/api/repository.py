from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.services.auth import get_current_user
from app.services.git_service import git_service
from app.services.repository_indexer import repository_indexer
from app.services.vector_service import vector_service
from app.services.embedding_service import embedding_service

router = APIRouter()

class RepositoryCloneRequest(BaseModel):
    repo_url: str

class RepositoryIndexResponse(BaseModel):
    project_id: str
    total_files: int
    total_symbols: int
    total_lines: int
    languages: dict
    summary: str

class SymbolSearchRequest(BaseModel):
    query: str
    symbol_type: Optional[str] = None
    language: Optional[str] = None
    limit: int = 10

class SymbolResponse(BaseModel):
    name: str
    symbol_type: str
    file_path: str
    start_line: int
    end_line: int
    content: str
    parent_name: Optional[str]
    docstring: Optional[str]
    language: str
    line_count: int

@router.post("/{project_id}/clone")
async def clone_repository(
    project_id: str,
    request: RepositoryCloneRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clone a git repository for a project"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    try:
        local_path = git_service.clone_repository(request.repo_url, str(project_id))
        
        # Update project with repo info
        project.repo_url = request.repo_url
        project.local_path = local_path
        db.commit()
        
        return {
            "project_id": str(project_id),
            "local_path": local_path,
            "message": "Repository cloned successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to clone repository: {str(e)}"
        )

@router.post("/{project_id}/index", response_model=RepositoryIndexResponse)
async def index_repository(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Index a cloned repository for code search"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if not project.local_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository not cloned yet"
        )
    
    try:
        # Index the repository
        repo_index = repository_indexer.index_repository(
            project_id=str(project_id),
            repo_path=project.local_path
        )
        
        # Prepare vectors for storage
        collection_name = f"repo_{project_id}"
        vector_service.ensure_collection(collection_name)
        
        # Generate embeddings for symbols
        all_symbols = []
        for file_index in repo_index.files:
            all_symbols.extend([s.to_dict() for s in file_index.symbols])
        
        if all_symbols:
            # Prepare texts for embedding
            texts = [embedding_service.prepare_symbol_text(s) for s in all_symbols]
            embeddings = await embedding_service.generate_embeddings(texts)
            
            # Store in vector database
            vector_service.upsert_symbols(collection_name, all_symbols, embeddings)
        
        return RepositoryIndexResponse(
            project_id=str(project_id),
            total_files=len(repo_index.files),
            total_symbols=repo_index.total_symbols,
            total_lines=repo_index.total_lines,
            languages=repo_index.languages,
            summary=repo_index.summary
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to index repository: {str(e)}"
        )

@router.post("/{project_id}/search", response_model=List[SymbolResponse])
async def search_symbols(
    project_id: str,
    request: SymbolSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search for symbols in a repository"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    collection_name = f"repo_{project_id}"
    
    try:
        # Generate query embedding
        query_embedding = await embedding_service.generate_embedding(request.query)
        
        # Search vector database
        results = vector_service.search(
            collection_name=collection_name,
            query_embedding=query_embedding,
            limit=request.limit,
            symbol_type=request.symbol_type,
            language=request.language
        )
        
        return [SymbolResponse(**r) for r in results]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Search failed: {str(e)}"
        )

@router.get("/{project_id}/files")
async def list_files(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all files in a project repository"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if not project.local_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository not cloned yet"
        )
    
    files = git_service.get_file_tree(project.local_path)
    return {"project_id": str(project_id), "files": files}

@router.get("/{project_id}/files/{file_path:path}")
async def get_file_content(
    project_id: str,
    file_path: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get content of a specific file"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if not project.local_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository not cloned yet"
        )
    
    content = git_service.read_file(project.local_path, file_path)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return {"file_path": file_path, "content": content}

@router.post("/{project_id}/sync")
async def sync_repository(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync repository with latest changes"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if not project.local_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository not cloned yet"
        )
    
    success = git_service.pull_latest(project.local_path)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to sync repository"
        )
    
    return {"project_id": str(project_id), "message": "Repository synced"}

@router.delete("/{project_id}")
async def delete_repository(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a project's repository"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if project.local_path:
        git_service.delete_repository(project.local_path)
        
        # Delete vector collection
        collection_name = f"repo_{project_id}"
        vector_service.delete_collection(collection_name)
        
        # Update project
        project.local_path = None
        db.commit()
    
    return {"project_id": str(project_id), "message": "Repository deleted"}
