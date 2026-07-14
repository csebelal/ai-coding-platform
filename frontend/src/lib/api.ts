import { TokenResponse } from './types';

const API_BASE = '/api/v1';

class ApiClient {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    if (typeof window !== 'undefined') {
      this.accessToken = localStorage.getItem('access_token');
      this.refreshToken = localStorage.getItem('refresh_token');
    }
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = { 'Content-Type': 'application/json' };
    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }
    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (response.status === 401 && this.refreshToken) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        const retryResponse = await fetch(response.url, {
          headers: this.getHeaders(),
        });
        return retryResponse.json();
      }
    }
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || 'Request failed');
    }
    return response.json();
  }

  private async refreshAccessToken(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      });
      if (response.ok) {
        const data: TokenResponse = await response.json();
        this.setTokens(data);
        return true;
      }
    } catch {}
    this.clearTokens();
    return false;
  }

  setTokens(data: TokenResponse) {
    this.accessToken = data.access_token;
    this.refreshToken = data.refresh_token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
    }
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  }

  isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  // Auth
  async register(email: string, password: string, fullName: string) {
    const response = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
    return this.handleResponse<TokenResponse>(response);
  }

  async login(email: string, password: string) {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    return this.handleResponse<TokenResponse>(response);
  }

  async getCurrentUser() {
    const response = await fetch(`${API_BASE}/auth/me`, { headers: this.getHeaders() });
    return this.handleResponse<any>(response);
  }

  // Projects
  async getProjects() {
    const response = await fetch(`${API_BASE}/projects`, { headers: this.getHeaders() });
    return this.handleResponse<any[]>(response);
  }

  async getProject(id: string) {
    const response = await fetch(`${API_BASE}/projects/${id}`, { headers: this.getHeaders() });
    return this.handleResponse<any>(response);
  }

  async createProject(data: { name: string; description: string; repository_url?: string }) {
    const response = await fetch(`${API_BASE}/projects`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse<any>(response);
  }

  async deleteProject(id: string) {
    const response = await fetch(`${API_BASE}/projects/${id}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  // Tasks
  async getTasks(projectId: string) {
    const response = await fetch(`${API_BASE}/tasks?project_id=${projectId}`, { headers: this.getHeaders() });
    return this.handleResponse<any[]>(response);
  }

  async getTask(taskId: string) {
    const response = await fetch(`${API_BASE}/tasks/${taskId}`, { headers: this.getHeaders() });
    return this.handleResponse<any>(response);
  }

  async createTask(data: { project_id: string; title: string; description: string; budget_limit?: number }) {
    const response = await fetch(`${API_BASE}/tasks`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse<any>(response);
  }

  async executeTask(taskId: string) {
    const response = await fetch(`${API_BASE}/tasks/${taskId}/execute`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  async cancelTask(taskId: string) {
    const response = await fetch(`${API_BASE}/tasks/${taskId}/cancel`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    return this.handleResponse<any>(response);
  }

  async getTaskStatus(taskId: string) {
    const response = await fetch(`${API_BASE}/tasks/${taskId}/status`, { headers: this.getHeaders() });
    return this.handleResponse<any>(response);
  }

  // Repository
  async cloneRepository(projectId: string, repositoryUrl: string) {
    const response = await fetch(`${API_BASE}/repository/clone`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ project_id: projectId, repository_url: repositoryUrl }),
    });
    return this.handleResponse<any>(response);
  }

  async indexRepository(projectId: string) {
    const response = await fetch(`${API_BASE}/repository/index`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ project_id: projectId }),
    });
    return this.handleResponse<any>(response);
  }

  async searchRepository(projectId: string, query: string) {
    const response = await fetch(`${API_BASE}/repository/search`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ project_id: projectId, query }),
    });
    return this.handleResponse<any>(response);
  }

  // Preferences
  async getPreferences() {
    const response = await fetch(`${API_BASE}/preferences`, { headers: this.getHeaders() });
    return this.handleResponse<any>(response);
  }

  async updatePreferences(data: any) {
    const response = await fetch(`${API_BASE}/preferences`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse<any>(response);
  }
}

export const api = new ApiClient();
