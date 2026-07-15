'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Project, Task } from '@/lib/types';
import { useAuth } from '@/lib/auth-context';

const WORKFLOW_STATES: Record<string, { label: string; color: string }> = {
  initialized: { label: 'Initialized', color: 'bg-gray-100 text-gray-800' },
  queued: { label: 'Queued', color: 'bg-gray-100 text-gray-800' },
  planning: { label: 'Planning', color: 'bg-blue-100 text-blue-800' },
  researching: { label: 'Researching', color: 'bg-blue-100 text-blue-800' },
  writing_tests: { label: 'Writing Tests', color: 'bg-purple-100 text-purple-800' },
  coding: { label: 'Coding', color: 'bg-yellow-100 text-yellow-800' },
  verifying: { label: 'Verifying', color: 'bg-orange-100 text-orange-800' },
  debugging: { label: 'Debugging', color: 'bg-red-100 text-red-800' },
  reviewing: { label: 'Reviewing', color: 'bg-indigo-100 text-indigo-800' },
  documenting: { label: 'Documenting', color: 'bg-teal-100 text-teal-800' },
  completed: { label: 'Completed', color: 'bg-green-100 text-green-800' },
  failed: { label: 'Failed', color: 'bg-red-100 text-red-800' },
  cancelled: { label: 'Cancelled', color: 'bg-gray-100 text-gray-800' },
};

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateTask, setShowCreateTask] = useState(false);
  const [taskTitle, setTaskTitle] = useState('');
  const [taskDesc, setTaskDesc] = useState('');
  const [taskBudget, setTaskBudget] = useState('0.10');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) { router.push('/login'); return; }
    loadData();
  }, [isAuthenticated, projectId]);

  const loadData = async () => {
    try {
      const [proj, taskList] = await Promise.all([
        api.getProject(projectId),
        api.getTasks(projectId),
      ]);
      setProject(proj);
      setTasks(taskList);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.createTask({
        project_id: projectId,
        title: taskTitle,
        description: taskDesc,
        budget_limit: parseFloat(taskBudget),
      });
      setShowCreateTask(false);
      setTaskTitle('');
      setTaskDesc('');
      setTaskBudget('0.10');
      loadData();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setCreating(false);
    }
  };

  const handleExecute = async (taskId: string) => {
    try {
      await api.executeTask(taskId);
      loadData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleCancel = async (taskId: string) => {
    try {
      await api.cancelTask(taskId);
      loadData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  if (loading) return <div className="p-8 text-center">Loading...</div>;
  if (!project) return <div className="p-8 text-center">Project not found</div>;

  return (
    <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div className="px-4 py-6 sm:px-0">
        <div className="mb-6">
          <button onClick={() => router.push('/projects')} className="text-sm text-primary-600 hover:text-primary-500 mb-2">
            &larr; Back to Projects
          </button>
          <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
          <p className="text-gray-600 mt-1">{project.description}</p>
          {project.repository_url && (
            <p className="text-sm text-gray-500 mt-1">Repo: {project.repository_url}</p>
          )}
        </div>

        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-medium text-gray-900">Tasks</h2>
          <button
            onClick={() => setShowCreateTask(true)}
            className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 text-sm font-medium"
          >
            New Task
          </button>
        </div>

        {showCreateTask && (
          <div className="bg-white shadow rounded-lg p-6 mb-6">
            <h3 className="text-lg font-medium mb-4">Create Task</h3>
            <form onSubmit={handleCreateTask} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Title</label>
                <input
                  type="text"
                  value={taskTitle}
                  onChange={(e) => setTaskTitle(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  value={taskDesc}
                  onChange={(e) => setTaskDesc(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  rows={4}
                  required
                  placeholder="Describe what you want the AI to implement..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Budget Limit (USD)</label>
                <input
                  type="number"
                  step="0.01"
                  value={taskBudget}
                  onChange={(e) => setTaskBudget(e.target.value)}
                  className="mt-1 block w-32 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div className="flex space-x-3">
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 text-sm font-medium disabled:opacity-50"
                >
                  {creating ? 'Creating...' : 'Create Task'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateTask(false)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 text-sm font-medium"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {tasks.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-500">No tasks yet. Create one to get started.</p>
          </div>
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Title</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">State</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cost</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {tasks.map((task) => {
                  const stateInfo = WORKFLOW_STATES[task.workflow_state] || WORKFLOW_STATES.initialized;
                  return (
                    <tr key={task.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900">{task.title}</div>
                        <div className="text-sm text-gray-500 line-clamp-1">{task.description}</div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 text-xs rounded-full ${stateInfo.color}`}>
                          {stateInfo.label}
                        </span>
                        {task.current_agent && (
                          <div className="text-xs text-gray-500 mt-1">Agent: {task.current_agent}</div>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">{task.status}</td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        ${Number(task.current_cost).toFixed(4)} / ${Number(task.budget_limit).toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-sm space-x-2">
                        {task.status === 'pending' && (
                          <button
                            onClick={() => handleExecute(task.id)}
                            className="text-primary-600 hover:text-primary-800 font-medium"
                          >
                            Execute
                          </button>
                        )}
                        {task.status === 'running' && (
                          <button
                            onClick={() => handleCancel(task.id)}
                            className="text-red-600 hover:text-red-800 font-medium"
                          >
                            Cancel
                          </button>
                        )}
                        <button
                          onClick={() => router.push(`/tasks/${task.id}`)}
                          className="text-gray-600 hover:text-gray-800"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
