export interface User {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string;
  auth_provider: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  repository_url?: string;
  local_path?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  project_id: string;
  title: string;
  description: string;
  status: string;
  workflow_state: string;
  current_agent?: string;
  current_cost: number;
  budget_limit: number;
  tokens_used: number;
  result_json?: any;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface AgentRun {
  agent_type: string;
  status: string;
  cost: number;
  started_at?: string;
}

export interface TaskStatus {
  task_id: string;
  status: string;
  workflow_state: string;
  current_agent?: string;
  cost: number;
  budget_limit: number;
  tokens_used: number;
  started_at?: string;
  completed_at?: string;
  runs: AgentRun[];
}

export interface ContextBuildRequest {
  task_id: string;
  project_id: string;
  description: string;
  agent_type: string;
  token_budget?: number;
}
