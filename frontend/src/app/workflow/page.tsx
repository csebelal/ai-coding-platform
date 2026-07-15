'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import WorkflowDiagram, { AgentNode } from '@/components/WorkflowDiagram';
import { Project, Task } from '@/lib/types';

const AGENT_STATES: AgentNode[] = [
  { id: 'initialized', label: 'Initialized', icon: '⚙️', description: 'Task created and ready', status: 'pending' },
  { id: 'planning', label: 'Planning', icon: '📋', description: 'Analyzing requirements', status: 'pending' },
  { id: 'researching', label: 'Researching', icon: '🔍', description: 'Gathering context', status: 'pending' },
  { id: 'writing_tests', label: 'Writing Tests', icon: '🧪', description: 'Creating test cases', status: 'pending' },
  { id: 'coding', label: 'Coding', icon: '💻', description: 'Writing implementation', status: 'pending' },
  { id: 'verifying', label: 'Verifying', icon: '✅', description: 'Validating output', status: 'pending' },
  { id: 'debugging', label: 'Debugging', icon: '🐛', description: 'Fixing issues', status: 'pending' },
  { id: 'reviewing', label: 'Reviewing', icon: '👁️', description: 'Code review', status: 'pending' },
  { id: 'documenting', label: 'Documenting', icon: '📝', description: 'Generating docs', status: 'pending' },
  { id: 'completed', label: 'Completed', icon: '🎉', description: 'Task finished', status: 'pending' },
];

const STATE_ORDER = AGENT_STATES.map(s => s.id);

export default function WorkflowPage() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState('');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [workflowState, setWorkflowState] = useState(AGENT_STATES);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [statusMsg, setStatusMsg] = useState('');

  const pollRef = useState<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!isAuthenticated) { router.push('/login'); return; }
    loadProjects();
  }, [isAuthenticated]);

  const loadProjects = async () => {
    try {
      const projs = await api.getProjects();
      setProjects(projs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadTasks = async (projectId: string) => {
    try {
      const ts = await api.getTasks(projectId);
      setTasks(ts);
    } catch (err) {
      console.error(err);
    }
  };

  const pollTaskStatus = useCallback(async (taskId: string) => {
    try {
      const status = await api.getTaskStatus(taskId);
      setStatusMsg(`Agent: ${status.current_agent || '-'} | Cost: $${Number(status.cost).toFixed(4)} | Tokens: ${status.tokens_used}`);

      setWorkflowState(prev => prev.map(node => {
        const idx = STATE_ORDER.indexOf(node.id);
        const currentIdx = status.workflow_state ? STATE_ORDER.indexOf(status.workflow_state) : -1;

        if (idx < currentIdx) return { ...node, status: 'completed' as const };
        if (idx === currentIdx) return { ...node, status: (status.status === 'failed' ? 'error' : 'active') as const };
        return { ...node, status: 'pending' as const };
      }));

      if (status.status === 'completed' || status.status === 'failed') {
        setSelectedTask(prev => prev ? { ...prev, status: status.status, workflow_state: status.workflow_state, current_cost: status.cost } : prev);
        setStatusMsg(status.status === 'completed' ? 'Task completed successfully!' : 'Task failed');
        if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
      }
    } catch (err) {
      console.error(err);
    }
  }, []);

  const handleProjectChange = async (projectId: string) => {
    setSelectedProject(projectId);
    setSelectedTask(null);
    setWorkflowState(AGENT_STATES);
    setStatusMsg('');
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
    if (projectId) await loadTasks(projectId);
  };

  const handleTaskSelect = (task: Task) => {
    setSelectedTask(task);
    setWorkflowState(prev => prev.map(node => {
      const idx = STATE_ORDER.indexOf(node.id);
      const currentIdx = task.workflow_state ? STATE_ORDER.indexOf(task.workflow_state) : -1;

      if (idx < currentIdx) return { ...node, status: 'completed' as const };
      if (idx === currentIdx) return { ...node, status: 'active' as const };
      return { ...node, status: 'pending' as const };
    }));
    setStatusMsg(`Status: ${task.status} | Agent: ${task.current_agent || '-'}`);
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  };

  const handleNodeClick = (nodeId: string) => {
    const node = workflowState.find(n => n.id === nodeId);
    if (node) setStatusMsg(`${node.label}: ${node.description} (${node.status})`);
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProject || !title || !description) return;
    setCreating(true);
    try {
      const task = await api.createTask({
        project_id: selectedProject,
        title,
        description,
      });
      setTitle('');
      setDescription('');
      await loadTasks(selectedProject);
      handleTaskSelect(task);
      setStatusMsg('Task created! Click Execute to start.');
    } catch (err: any) {
      setStatusMsg(`Error: ${err.message}`);
    } finally {
      setCreating(false);
    }
  };

  const handleExecute = async () => {
    if (!selectedTask) return;
    try {
      await api.executeTask(selectedTask.id);
      setStatusMsg('Task queued for execution...');
      setWorkflowState(prev => prev.map((n, i) => i === 0 ? { ...n, status: 'active' as const } : { ...n, status: 'pending' as const }));
      if (pollRef.current) clearInterval(pollRef.current);
      pollRef.current = setInterval(() => pollTaskStatus(selectedTask.id), 3000);
    } catch (err: any) {
      setStatusMsg(`Error: ${err.message}`);
    }
  };

  const handleCancel = async () => {
    if (!selectedTask) return;
    try {
      await api.cancelTask(selectedTask.id);
      setStatusMsg('Task cancelled');
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
    } catch (err: any) {
      setStatusMsg(`Error: ${err.message}`);
    }
  };

  if (loading) return <div className="min-h-screen bg-gray-950 flex items-center justify-center">
    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
  </div>;

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Workflow Builder</h1>
            <p className="text-sm text-gray-400 mt-1">Visual agent pipeline for task execution</p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={selectedProject}
              onChange={e => handleProjectChange(e.target.value)}
              className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-blue-500"
            >
              <option value="">Select Project...</option>
              {projects.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
        </div>

        {!selectedProject ? (
          <div className="text-center py-20 text-gray-500">
            <div className="text-5xl mb-4">🔧</div>
            <p className="text-lg">Select a project to view its workflow</p>
          </div>
        ) : (
          <>
            <div className="bg-gray-900 rounded-xl p-4 mb-6">
              <WorkflowDiagram nodes={workflowState} onNodeClick={handleNodeClick} />
            </div>

            {statusMsg && (
              <div className="mb-4 px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg text-sm text-gray-300 flex items-center gap-2">
                <span className={`inline-block w-2 h-2 rounded-full ${statusMsg.includes('Error') ? 'bg-red-500' : statusMsg.includes('completed') ? 'bg-green-500' : statusMsg.includes('queued') || statusMsg.includes('Agent') ? 'bg-blue-500 animate-pulse' : 'bg-gray-500'}`} />
                {statusMsg}
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-4">
                <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
                  <h2 className="text-lg font-semibold text-white mb-4">Tasks</h2>
                  {tasks.length === 0 ? (
                    <p className="text-gray-500 text-sm">No tasks yet. Create one below.</p>
                  ) : (
                    <div className="space-y-2">
                      {tasks.map(task => (
                        <div
                          key={task.id}
                          onClick={() => handleTaskSelect(task)}
                          className={`px-4 py-3 rounded-lg cursor-pointer transition-all border ${
                            selectedTask?.id === task.id
                              ? 'bg-blue-900/30 border-blue-500/50'
                              : 'bg-gray-800/50 border-gray-700 hover:border-gray-600'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <span className="font-medium text-sm text-gray-200">{task.title}</span>
                              <span className="text-xs text-gray-500 ml-2">{task.status}</span>
                            </div>
                            <span className="text-xs text-gray-500">${Number(task.current_cost).toFixed(4)}</span>
                          </div>
                          <div className="text-xs text-gray-500 mt-1">{task.description}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {selectedTask && (
                  <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
                    <h2 className="text-lg font-semibold text-white mb-4">Task Actions</h2>
                    <div className="flex gap-3">
                      <button
                        onClick={handleExecute}
                        disabled={selectedTask.status === 'running' || selectedTask.status === 'queued'}
                        className="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg text-sm font-medium transition-all"
                      >
                        {selectedTask.status === 'running' ? 'Running...' : 'Execute Task'}
                      </button>
                      <button
                        onClick={handleCancel}
                        disabled={!(selectedTask.status === 'running' || selectedTask.status === 'queued')}
                        className="px-5 py-2 bg-red-600/20 hover:bg-red-600/30 disabled:bg-gray-800 disabled:text-gray-600 text-red-400 rounded-lg text-sm font-medium transition-all border border-red-800/50 disabled:border-gray-700"
                      >
                        Cancel
                      </button>
                    </div>
                    {selectedTask.status === 'completed' && selectedTask.result_json && (
                      <div className="mt-4">
                        <h3 className="text-sm font-medium text-gray-400 mb-2">Result</h3>
                        <pre className="text-xs text-gray-500 bg-gray-800 rounded-lg p-3 overflow-auto max-h-40">
                          {JSON.stringify(selectedTask.result_json, null, 2)}
                        </pre>
                      </div>
                    )}
                    {selectedTask.error_message && (
                      <div className="mt-4 p-3 bg-red-900/20 border border-red-800/30 rounded-lg">
                        <h3 className="text-sm font-medium text-red-400 mb-1">Error</h3>
                        <p className="text-xs text-red-300">{selectedTask.error_message}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="space-y-4">
                <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
                  <h2 className="text-lg font-semibold text-white mb-4">New Task</h2>
                  <form onSubmit={handleCreateTask} className="space-y-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-400 mb-1">Title</label>
                      <input
                        type="text"
                        value={title}
                        onChange={e => setTitle(e.target.value)}
                        placeholder="e.g. Build login page"
                        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-blue-500"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-400 mb-1">Description</label>
                      <textarea
                        value={description}
                        onChange={e => setDescription(e.target.value)}
                        placeholder="Describe what the agent should build..."
                        rows={3}
                        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-blue-500 resize-none"
                        required
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={creating || !title || !description}
                      className="w-full px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-700 disabled:to-gray-700 disabled:text-gray-500 text-white rounded-lg text-sm font-medium transition-all"
                    >
                      {creating ? 'Creating...' : 'Create Task'}
                    </button>
                  </form>
                </div>

                {selectedTask && (
                  <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
                    <h2 className="text-lg font-semibold text-white mb-3">Task Details</h2>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Status</span>
                        <span className={`font-medium ${
                          selectedTask.status === 'completed' ? 'text-green-400' :
                          selectedTask.status === 'running' ? 'text-blue-400' :
                          selectedTask.status === 'failed' ? 'text-red-400' : 'text-gray-400'
                        }`}>{selectedTask.status}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Cost</span>
                        <span className="text-gray-200">${Number(selectedTask.current_cost).toFixed(4)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Tokens</span>
                        <span className="text-gray-200">{selectedTask.tokens_used}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Agent</span>
                        <span className="text-gray-200">{selectedTask.current_agent || '-'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Created</span>
                        <span className="text-gray-200">{new Date(selectedTask.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
