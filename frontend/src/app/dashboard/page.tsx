'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Task, Project } from '@/lib/types';
import { useAuth } from '@/lib/auth-context';

export default function DashboardPage() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusMsg, setStatusMsg] = useState('');

  useEffect(() => {
    if (!isAuthenticated) { router.push('/login'); return; }
    loadData();
  }, [isAuthenticated]);

  const loadData = async () => {
    try {
      const projs = await api.getProjects();
      setProjects(projs);
      const allTasks: Task[] = [];
      for (const proj of projs) {
        try {
          const projTasks = await api.getTasks(proj.id);
          allTasks.push(...projTasks);
        } catch {}
      }
      setTasks(allTasks.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const activeTasks = tasks.filter(t => t.status === 'running' || t.status === 'queued');
  const totalCost = tasks.reduce((sum, t) => sum + Number(t.current_cost), 0);
  const completedTasks = tasks.filter(t => t.status === 'completed');
  const failedTasks = tasks.filter(t => t.status === 'failed');
  const successRate = tasks.length > 0 ? (completedTasks.length / tasks.length) * 100 : 0;

  if (loading) return <div className="min-h-screen bg-gray-950 flex items-center justify-center">
    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
  </div>;

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Dashboard</h1>
            <p className="text-sm text-gray-400 mt-1">Overview of your projects and tasks</p>
          </div>
          <button
            onClick={() => router.push('/workflow')}
            className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg text-sm font-medium transition-all flex items-center gap-2"
          >
            <span>⚡</span> Open Workflow
          </button>
        </div>

        {statusMsg && (
          <div className="mb-4 px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg text-sm text-gray-300">{statusMsg}</div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800 hover:border-gray-700 transition-all">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-blue-900/30 flex items-center justify-center text-lg">📁</div>
              <div>
                <div className="text-xs text-gray-500 font-medium uppercase tracking-wider">Projects</div>
                <div className="text-2xl font-bold text-white">{projects.length}</div>
              </div>
            </div>
            <div className="w-full bg-gray-800 rounded-full h-1.5">
              <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${Math.min(projects.length * 20, 100)}%` }} />
            </div>
          </div>
          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800 hover:border-gray-700 transition-all">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-green-900/30 flex items-center justify-center text-lg">⚡</div>
              <div>
                <div className="text-xs text-gray-500 font-medium uppercase tracking-wider">Active Tasks</div>
                <div className="text-2xl font-bold text-white">{activeTasks.length}</div>
              </div>
            </div>
            <div className="w-full bg-gray-800 rounded-full h-1.5">
              <div className="bg-green-500 h-1.5 rounded-full" style={{ width: `${Math.min(activeTasks.length * 25, 100)}%` }} />
            </div>
          </div>
          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800 hover:border-gray-700 transition-all">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-purple-900/30 flex items-center justify-center text-lg">💰</div>
              <div>
                <div className="text-xs text-gray-500 font-medium uppercase tracking-wider">Total Cost</div>
                <div className="text-2xl font-bold text-white">${totalCost.toFixed(4)}</div>
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-500 mt-2">
              <span>Across {tasks.length} tasks</span>
            </div>
          </div>
          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800 hover:border-gray-700 transition-all">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-amber-900/30 flex items-center justify-center text-lg">📊</div>
              <div>
                <div className="text-xs text-gray-500 font-medium uppercase tracking-wider">Success Rate</div>
                <div className="text-2xl font-bold text-white">{successRate.toFixed(0)}%</div>
              </div>
            </div>
            <div className="w-full bg-gray-800 rounded-full h-1.5">
              <div className={`h-1.5 rounded-full ${successRate >= 80 ? 'bg-green-500' : successRate >= 50 ? 'bg-amber-500' : 'bg-red-500'}`} style={{ width: `${successRate}%` }} />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-2 bg-gray-900 rounded-xl p-5 border border-gray-800">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Task Status Breakdown</h2>
            </div>
            {tasks.length === 0 ? (
              <div className="text-center py-10 text-gray-500">
                <div className="text-4xl mb-3">📋</div>
                <p>No tasks yet</p>
                <button onClick={() => router.push('/workflow')} className="mt-3 text-sm text-blue-400 hover:text-blue-300">
                  Create your first task &rarr;
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {[
                  { label: 'Completed', count: completedTasks.length, color: 'bg-green-500', bg: 'bg-green-900/20' },
                  { label: 'Running', count: activeTasks.length, color: 'bg-blue-500', bg: 'bg-blue-900/20' },
                  { label: 'Failed', count: failedTasks.length, color: 'bg-red-500', bg: 'bg-red-900/20' },
                  { label: 'Pending', count: tasks.length - completedTasks.length - activeTasks.length - failedTasks.length, color: 'bg-gray-500', bg: 'bg-gray-800' },
                ].map(item => (
                  <div key={item.label} className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${item.color}`} />
                    <span className="text-sm text-gray-400 flex-1">{item.label}</span>
                    <div className="flex-1">
                      <div className="w-full bg-gray-800 rounded-full h-2">
                        <div className={`${item.color} h-2 rounded-full transition-all duration-500`} style={{ width: `${tasks.length > 0 ? (item.count / tasks.length) * 100 : 0}%` }} />
                      </div>
                    </div>
                    <span className="text-sm text-gray-300 w-8 text-right font-medium">{item.count}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
            <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <button
                onClick={() => router.push('/workflow')}
                className="w-full px-4 py-3 bg-blue-600/10 hover:bg-blue-600/20 border border-blue-800/30 rounded-lg text-sm text-blue-400 font-medium transition-all flex items-center gap-3"
              >
                <span className="text-lg">⚡</span> Open Workflow Builder
              </button>
              <button
                onClick={() => router.push('/projects')}
                className="w-full px-4 py-3 bg-purple-600/10 hover:bg-purple-600/20 border border-purple-800/30 rounded-lg text-sm text-purple-400 font-medium transition-all flex items-center gap-3"
              >
                <span className="text-lg">📁</span> Manage Projects
              </button>
              <button
                onClick={() => router.push('/settings')}
                className="w-full px-4 py-3 bg-gray-700/30 hover:bg-gray-700/50 border border-gray-700 rounded-lg text-sm text-gray-400 font-medium transition-all flex items-center gap-3"
              >
                <span className="text-lg">⚙️</span> Settings
              </button>
            </div>
          </div>
        </div>

        {tasks.length > 0 && (
          <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-800">
              <h2 className="text-lg font-semibold text-white">Recent Tasks</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-800/50">
                  <tr>
                    {['Task', 'Status', 'Agent', 'Cost', 'Created'].map(h => (
                      <th key={h} className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {tasks.slice(0, 5).map(task => (
                    <tr
                      key={task.id}
                      onClick={() => router.push(`/tasks/${task.id}`)}
                      className="hover:bg-gray-800/30 cursor-pointer transition-colors"
                    >
                      <td className="px-5 py-4">
                        <div className="text-sm font-medium text-gray-200">{task.title}</div>
                      </td>
                      <td className="px-5 py-4">
                        <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${
                          task.status === 'completed' ? 'bg-green-900/30 text-green-400' :
                          task.status === 'running' ? 'bg-blue-900/30 text-blue-400' :
                          task.status === 'failed' ? 'bg-red-900/30 text-red-400' :
                          'bg-gray-800 text-gray-400'
                        }`}>
                          {task.status}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-sm text-gray-500">{task.current_agent || '-'}</td>
                      <td className="px-5 py-4 text-sm text-gray-500">${Number(task.current_cost).toFixed(4)}</td>
                      <td className="px-5 py-4 text-sm text-gray-500">{new Date(task.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
