import httpx
from typing import Optional
from app.config import settings

class GitHubOAuth:
    AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_INFO_URL = "https://api.github.com/user"
    
    @staticmethod
    def get_authorize_url() -> str:
        return f"{GitHubOAuth.AUTHORIZE_URL}?client_id={settings.GITHUB_CLIENT_ID}&redirect_uri={settings.GITHUB_REDIRECT_URI}&scope=user:email"
    
    @staticmethod
    async def get_access_token(code: str) -> Optional[str]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GitHubOAuth.TOKEN_URL,
                json={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GITHUB_REDIRECT_URI
                },
                headers={"Accept": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("access_token")
            return None
    
    @staticmethod
    async def get_user_info(access_token: str) -> Optional[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GitHubOAuth.USER_INFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            return None

class GoogleOAuth:
    AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    @staticmethod
    def get_authorize_url() -> str:
        return f"{GoogleOAuth.AUTHORIZE_URL}?client_id={settings.GOOGLE_CLIENT_ID}&redirect_uri={settings.GOOGLE_REDIRECT_URI}&response_type=code&scope=openid%20email%20profile"
    
    @staticmethod
    async def get_access_token(code: str) -> Optional[str]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GoogleOAuth.TOKEN_URL,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("access_token")
            return None
    
    @staticmethod
    async def get_user_info(access_token: str) -> Optional[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GoogleOAuth.USER_INFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            return None
