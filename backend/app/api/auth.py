from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.config import settings
from app.schemas.auth import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    TokenRefresh, PasswordChange
)
from app.services.auth import (
    PasswordService, TokenService, AuthService, get_current_user
)
from app.services.oauth import GitHubOAuth, GoogleOAuth
from app.models.user import User

router = APIRouter()

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    
    existing_user = auth_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = auth_service.create_user(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name
    )
    
    return auth_service.create_tokens(user)

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    
    user = auth_service.authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    return auth_service.create_tokens(user)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
    payload = TokenService.decode_token(token_data.refresh_token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    auth_service = AuthService(db)
    return auth_service.create_tokens(user)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_me(
    full_name: Optional[str] = None,
    avatar_url: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if full_name is not None:
        current_user.full_name = full_name
    if avatar_url is not None:
        current_user.avatar_url = avatar_url
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password not set for this account"
        )
    
    if not PasswordService.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    current_user.hashed_password = PasswordService.hash_password(password_data.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}

@router.get("/github")
async def github_login():
    return RedirectResponse(url=GitHubOAuth.get_authorize_url())

@router.get("/github/callback")
async def github_callback(code: str = Query(...), db: Session = Depends(get_db)):
    access_token = await GitHubOAuth.get_access_token(code)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get GitHub access token"
        )
    
    user_info = await GitHubOAuth.get_user_info(access_token)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user info from GitHub"
        )
    
    email = user_info.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not available from GitHub"
        )
    
    auth_service = AuthService(db)
    user = auth_service.get_user_by_email(email)
    
    if not user:
        user = auth_service.create_user(
            email=email,
            full_name=user_info.get("name"),
            auth_provider="github",
            avatar_url=user_info.get("avatar_url")
        )
    elif user.auth_provider != "github":
        user.auth_provider = "github"
        user.avatar_url = user_info.get("avatar_url")
        db.commit()
    
    tokens = auth_service.create_tokens(user)
    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/auth/callback?access_token={tokens['access_token']}&refresh_token={tokens['refresh_token']}"
    )

@router.get("/google")
async def google_login():
    return RedirectResponse(url=GoogleOAuth.get_authorize_url())

@router.get("/google/callback")
async def google_callback(code: str = Query(...), db: Session = Depends(get_db)):
    access_token = await GoogleOAuth.get_access_token(code)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get Google access token"
        )
    
    user_info = await GoogleOAuth.get_user_info(access_token)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user info from Google"
        )
    
    email = user_info.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not available from Google"
        )
    
    auth_service = AuthService(db)
    user = auth_service.get_user_by_email(email)
    
    if not user:
        user = auth_service.create_user(
            email=email,
            full_name=user_info.get("name"),
            auth_provider="google",
            avatar_url=user_info.get("picture")
        )
    elif user.auth_provider != "google":
        user.auth_provider = "google"
        user.avatar_url = user_info.get("picture")
        db.commit()
    
    tokens = auth_service.create_tokens(user)
    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/auth/callback?access_token={tokens['access_token']}&refresh_token={tokens['refresh_token']}"
    )
