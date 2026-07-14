'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Task, TaskStatus } from '@/lib/types';
import { useAuth } from '@/lib/auth-context';
import { useTaskSocket } from '@/lib/use-task-socket';

const WORKFLOW_STATES: Record<string, { label: string; color: string; step: number }> = {
  initialized: { label: 'Initialized', color: 'bg-gray-200', step: 0 },
  queued: { label: 'Queued', color: 'bg-gray-200', step: 0 },
  planning: { label: 'Planning', color: 'bg-blue-500', step: 1 },
  researching: { label: 'Researching', color: 'bg-blue-500', step: 2 },
  writing_tests: { label: 'Writing Tests', color: 'bg-purple-500', step: 3 },
  coding: { label: 'Coding', color: 'bg-yellow-500', step: 4 },
  verifying: { label: 'Verifying', color: 'bg-orange-500', step: 5 },
  debugging: { label: 'Debugging', color: 'bg-red-500', step: 5 },
  reviewing: { label: 'Reviewing', color: 'bg-indigo-500', step: 6 },
  documenting: { label: 'Documenting', color: 'bg-teal-500', step: 7 },
  completed: { label: 'Completed', color: 'bg-green-500', step: 8 },
  failed: { label: 'Failed', color: 'bg-red-500', step: -1 },
  cancelled: { label: 'Cancelled', color: 'bg-gray-400', step: -1 },
};

const STEPS = ['Plan', 'Research', 'Tests', 'Code', 'Verify', 'Review', 'Docs', 'Done'];

export default function TaskDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const taskId = params.id as string;

  const [task, setTask] = useState<Task | null>(null);
  const [status, setStatus] = useState<TaskStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState<Array<{ level: string; message: string; agent?: string; time: string }>>([]);
  const logsEndRef = useRef<HTMLDivElement>(null);

  const handleTaskUpdate = useCallback((data: any) => {
    setStatus(prev => prev ? { ...prev, ...data } : null);
    setTask(prev => prev ? { ...prev, ...data } : null);
  }, []);

  const handleAgentUpdate = useCallback((msg: any) => {
    setStatus(prev => {
      if (!prev) return null;
      const runs = [...prev.runs];
      const existing = runs.findIndex(r => r.agent_type === msg.agent_type);
      if (existing >= 0) {
        runs[existing] = { ...runs[existing], status: msg.status, ...msg.data };
      } else {
        runs.push({ agent_type: msg.agent_type, status: msg.status, cost: 0, ...msg.data });
      }
      return { ...prev, runs };
    });
  }, []);

  const handleLog = useCallback((msg: any) => {
    setLogs(prev => [...prev.slice(-100), {
      level: msg.level,
      message: msg.message,
      agent: msg.agent,
      time: new Date().toLocaleTimeString()
    }]);
  }, []);

  const { connected } = useTaskSocket({
    taskId,
    onTaskUpdate: handleTaskUpdate,
    onAgentUpdate: handleAgentUpdate,
    onLog: handleLog,
    enabled: !!status && ['running', 'queued'].includes(status.status)
  });

  const loadStatus = useCallback(async () => {
    try {
      const taskData = await api.getTask(taskId);
      setTask(taskData);
      const statusData = await api.getTaskStatus(taskId);
      setStatus(statusData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  useEffect(() => {
    if (!isAuthenticated) { router.push('/login'); return; }
    loadStatus();
  }, [isAuthenticated, loadStatus]);

  // Poll for updates when running
  useEffect(() => {
    if (!status || !['running', 'queued'].includes(status.status)) return;
    const interval = setInterval(loadStatus, 3000);
    return () => clearInterval(interval);
  }, [status?.status, loadStatus]);

  if (loading) return <div className="p-8 text-center">Loading...</div>;
  if (!task || !status) return <div className="p-8 text-center">Task not found</div>;

  const stateInfo = WORKFLOW_STATES[status.workflow_state] || WORKFLOW_STATES.initialized;
  const currentStep = stateInfo.step;
  const isRunning = ['running', 'queued'].includes(status.status);

  return (
    <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div className="px-4 py-6 sm:px-0">
        <button onClick={() => router.back()} className="text-sm text-primary-600 hover:text-primary-500 mb-4">
          &larr; Back
        </button>

        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{task.title}</h1>
            <p className="text-gray-600 mt-1">{task.description}</p>
          </div>
          <div className="flex items-center space-x-3">
            <span className={`px-3 py-1 text-sm rounded-full ${stateInfo.color} text-white font-medium`}>
              {stateInfo.label}
            </span>
            {isRunning && (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600" />
            )}
          </div>
        </div>

        {/* Progress Pipeline */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-sm font-medium text-gray-500 mb-4">Workflow Progress</h2>
          <div className="flex items-center justify-between">
            {STEPS.map((step, i) => {
              const isActive = i === currentStep;
              const isComplete = currentStep > i || status.status === 'completed';
              const isFailed = status.status === 'failed' && i === currentStep;
              return (
                <div key={step} className="flex flex-col items-center flex-1">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${
                      isFailed
                        ? 'bg-red-500 text-white'
                        : isComplete
                        ? 'bg-green-500 text-white'
                        : isActive
                        ? 'bg-primary-600 text-white animate-pulse'
                        : 'bg-gray-200 text-gray-500'
                    }`}
                  >
                    {isComplete ? '✓' : i + 1}
                  </div>
                  <span className={`text-xs mt-2 ${isActive ? 'font-medium text-primary-600' : 'text-gray-500'}`}>
                    {step}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">Current Agent</div>
            <div className="text-lg font-semibold text-gray-900">{status.current_agent || 'None'}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">Cost</div>
            <div className="text-lg font-semibold text-gray-900">
              ${status.cost.toFixed(4)} / ${status.budget_limit.toFixed(2)}
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
              <div
                className="bg-primary-600 h-2 rounded-full"
                style={{ width: `${Math.min(100, (status.cost / status.budget_limit) * 100)}%` }}
              />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-500">Tokens Used</div>
              <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-gray-300'}`} title={connected ? 'Connected' : 'Disconnected'} />
            </div>
            <div className="text-lg font-semibold text-gray-900">{status.tokens_used.toLocaleString()}</div>
          </div>
        </div>

        {/* Agent Runs */}
        <div className="bg-white rounded-lg shadow overflow-hidden mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Agent Runs</h2>
          </div>
          {status.runs.length === 0 ? (
            <div className="px-6 py-4 text-sm text-gray-500">No agent runs yet</div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Agent</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cost</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Started</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {status.runs.map((run, i) => (
                  <tr key={i}>
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{run.agent_type}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        run.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {run.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">${run.cost.toFixed(4)}</td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {run.started_at ? new Date(run.started_at).toLocaleTimeString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Live Logs */}
        {logs.length > 0 && (
          <div className="bg-gray-900 rounded-lg shadow overflow-hidden mb-6">
            <div className="px-6 py-3 border-b border-gray-700 flex items-center justify-between">
              <h2 className="text-lg font-medium text-white">Live Logs</h2>
              <button
                onClick={() => setLogs([])}
                className="text-xs text-gray-400 hover:text-white"
              >
                Clear
              </button>
            </div>
            <div className="px-6 py-4 max-h-64 overflow-y-auto font-mono text-sm">
              {logs.map((log, i) => (
                <div key={i} className="py-0.5">
                  <span className="text-gray-500">{log.time}</span>
                  <span className={`mx-2 ${
                    log.level === 'error' ? 'text-red-400' :
                    log.level === 'warning' ? 'text-yellow-400' :
                    'text-green-400'
                  }`}>
                    [{log.level.toUpperCase()}]
                  </span>
                  {log.agent && <span className="text-blue-400">({log.agent})</span>}
                  <span className="text-gray-300">{log.message}</span>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          </div>
        )}

        {/* Error */}
        {task.error_message && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <h3 className="text-sm font-medium text-red-800">Error</h3>
            <p className="mt-1 text-sm text-red-700">{task.error_message}</p>
          </div>
        )}

        {/* Result */}
        {task.result_json && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">Result</h2>
            </div>
            <pre className="px-6 py-4 text-sm text-gray-700 overflow-auto max-h-96">
              {JSON.stringify(task.result_json, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
