import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_user(client: AsyncClient):
    # Register first
    await client.post("/api/v1/auth/register", json={
        "email": "login@example.com",
        "password": "testpassword123",
        "full_name": "Login User"
    })

    # Login
    response = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "testpassword123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient):
    # Register and get token
    reg_response = await client.post("/api/v1/auth/register", json={
        "email": "me@example.com",
        "password": "testpassword123",
        "full_name": "Me User"
    })
    token = reg_response.json()["access_token"]

    # Get current user
    response = await client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_protected_route_without_token(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    reg_response = await client.post("/api/v1/auth/register", json={
        "email": "proj@example.com",
        "password": "testpassword123",
        "full_name": "Proj User"
    })
    token = reg_response.json()["access_token"]

    response = await client.post("/api/v1/projects", json={
        "name": "Test Project",
        "description": "A test project"
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Project"


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient):
    reg_response = await client.post("/api/v1/auth/register", json={
        "email": "list@example.com",
        "password": "testpassword123",
        "full_name": "List User"
    })
    token = reg_response.json()["access_token"]

    # Create a project
    await client.post("/api/v1/projects", json={
        "name": "Project 1",
        "description": "First"
    }, headers={"Authorization": f"Bearer {token}"})

    # List projects
    response = await client.get("/api/v1/projects", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient):
    reg_response = await client.post("/api/v1/auth/register", json={
        "email": "task@example.com",
        "password": "testpassword123",
        "full_name": "Task User"
    })
    token = reg_response.json()["access_token"]

    # Create project
    proj_response = await client.post("/api/v1/projects", json={
        "name": "Task Project",
        "description": "For tasks"
    }, headers={"Authorization": f"Bearer {token}"})
    project_id = proj_response.json()["id"]

    # Create task
    response = await client.post("/api/v1/tasks", json={
        "project_id": project_id,
        "title": "Test Task",
        "description": "Add a hello world function",
        "budget_limit": 0.05
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_preferences_crud(client: AsyncClient):
    reg_response = await client.post("/api/v1/auth/register", json={
        "email": "prefs@example.com",
        "password": "testpassword123",
        "full_name": "Prefs User"
    })
    token = reg_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get default preferences
    response = await client.get("/api/v1/preferences", headers=headers)
    assert response.status_code == 200
    prefs = response.json()
    assert prefs["preferred_provider"] == "deepseek"

    # Update preferences
    response = await client.put("/api/v1/preferences", json={
        "preferred_provider": "openai",
        "preferred_model": "openai/gpt-4o",
        "temperature": 0.5
    }, headers=headers)
    assert response.status_code == 200
    updated = response.json()
    assert updated["preferred_provider"] == "openai"
    assert updated["temperature"] == 0.5
