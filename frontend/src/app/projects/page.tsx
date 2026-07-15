'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Project } from '@/lib/types';
import { useAuth } from '@/lib/auth-context';

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [repoUrl, setRepoUrl] = useState('');
  const [creating, setCreating] = useState(false);
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) { router.push('/login'); return; }
    loadProjects();
  }, [isAuthenticated]);

  const loadProjects = async () => {
    try {
      const data = await api.getProjects();
      setProjects(data);
    } catch (err) {
      console.error('Failed to load projects', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.createProject({ name, description, repo_url: repoUrl || undefined });
      setShowCreate(false);
      setName(''); setDescription(''); setRepoUrl('');
      loadProjects();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this project?')) return;
    try {
      await api.deleteProject(id);
      loadProjects();
    } catch (err: any) {
      alert(err.message);
    }
  };

  if (loading) return <div className="min-h-screen bg-gray-950 flex items-center justify-center">
    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
  </div>;

  return (
    <div className="px-4 py-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Projects</h1>
            <p className="text-sm text-gray-400 mt-1">Manage your software projects</p>
          </div>
          <button onClick={() => setShowCreate(true)} className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg text-sm font-medium transition-all">
            + New Project
          </button>
        </div>

        {showCreate && (
          <div className="bg-gray-900 rounded-xl p-6 mb-6 border border-gray-800">
            <h2 className="text-lg font-semibold text-white mb-4">Create Project</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Name</label>
                <input type="text" value={name} onChange={e => setName(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-blue-500" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Description</label>
                <textarea value={description} onChange={e => setDescription(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-blue-500 resize-none" rows={3} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Repository URL (optional)</label>
                <input type="url" value={repoUrl} onChange={e => setRepoUrl(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-blue-500"
                  placeholder="https://github.com/user/repo.git" />
              </div>
              <div className="flex gap-3">
                <button type="submit" disabled={creating}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg text-sm font-medium transition-all">
                  {creating ? 'Creating...' : 'Create'}
                </button>
                <button type="button" onClick={() => setShowCreate(false)}
                  className="px-4 py-2 bg-gray-800 border border-gray-700 text-gray-300 rounded-lg hover:bg-gray-700 text-sm font-medium transition-all">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {projects.length === 0 ? (
          <div className="text-center py-20 bg-gray-900 rounded-xl border border-gray-800">
            <div className="text-5xl mb-4">📁</div>
            <p className="text-gray-500">No projects yet. Create one to get started.</p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {projects.map(project => (
              <div key={project.id}
                className="bg-gray-900 rounded-xl p-5 border border-gray-800 hover:border-gray-700 transition-all cursor-pointer"
                onClick={() => router.push(`/projects/${project.id}`)}>
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-900/30 flex items-center justify-center text-lg">📁</div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-base font-semibold text-gray-200 truncate">{project.name}</h3>
                    <p className="text-xs text-gray-500 truncate">{project.description || 'No description'}</p>
                  </div>
                </div>
                <div className="flex justify-between items-center pt-3 border-t border-gray-800">
                  <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                    project.status === 'active' ? 'bg-green-900/30 text-green-400' : 'bg-gray-800 text-gray-400'
                  }`}>{project.status}</span>
                  <button onClick={e => { e.stopPropagation(); handleDelete(project.id); }}
                    className="text-xs text-red-400 hover:text-red-300 transition-colors">Delete</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
