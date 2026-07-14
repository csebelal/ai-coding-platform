'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';

const PROVIDERS = [
  { value: 'deepseek', label: 'DeepSeek', models: ['deepseek/deepseek-chat', 'deepseek/deepseek-coder'] },
  { value: 'gemini', label: 'Google Gemini', models: ['google/gemini-flash'] },
  { value: 'openai', label: 'OpenAI', models: ['openai/gpt-4o'] },
];

export default function SettingsPage() {
  const { isAuthenticated, user } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [prefs, setPrefs] = useState({
    preferred_provider: 'deepseek',
    preferred_model: 'deepseek/deepseek-chat',
    temperature: 0.2,
    max_tokens: 4096,
    default_budget_limit: 0.10,
    daily_budget_limit: 1.00,
    theme: 'light',
    editor_font_size: 14,
    show_token_counts: true,
    email_notifications: false,
    task_completion_notifications: true,
  });

  useEffect(() => {
    if (!isAuthenticated) { router.push('/login'); return; }
    loadPreferences();
  }, [isAuthenticated]);

  const loadPreferences = async () => {
    try {
      const data = await api.getPreferences();
      setPrefs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      await api.updatePreferences(prefs);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setSaving(false);
    }
  };

  const selectedProvider = PROVIDERS.find(p => p.value === prefs.preferred_provider);

  if (loading) return <div className="p-8 text-center">Loading...</div>;

  return (
    <div className="max-w-3xl mx-auto py-6 sm:px-6 lg:px-8">
      <div className="px-4 py-6 sm:px-0">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

        {/* AI Provider */}
        <section className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">AI Provider</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">Provider</label>
              <select
                value={prefs.preferred_provider}
                onChange={(e) => {
                  const provider = PROVIDERS.find(p => p.value === e.target.value);
                  setPrefs({
                    ...prefs,
                    preferred_provider: e.target.value,
                    preferred_model: provider?.models[0] || '',
                  });
                }}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              >
                {PROVIDERS.map(p => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Model</label>
              <select
                value={prefs.preferred_model}
                onChange={(e) => setPrefs({ ...prefs, preferred_model: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              >
                {selectedProvider?.models.map(m => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Temperature</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="2"
                value={prefs.temperature}
                onChange={(e) => setPrefs({ ...prefs, temperature: parseFloat(e.target.value) })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Max Tokens</label>
              <input
                type="number"
                step="256"
                min="256"
                max="32768"
                value={prefs.max_tokens}
                onChange={(e) => setPrefs({ ...prefs, max_tokens: parseInt(e.target.value) })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>
        </section>

        {/* Budget */}
        <section className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Budget Limits</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">Default Task Budget ($)</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={prefs.default_budget_limit}
                onChange={(e) => setPrefs({ ...prefs, default_budget_limit: parseFloat(e.target.value) })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Daily Budget Limit ($)</label>
              <input
                type="number"
                step="0.10"
                min="0.10"
                value={prefs.daily_budget_limit}
                onChange={(e) => setPrefs({ ...prefs, daily_budget_limit: parseFloat(e.target.value) })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>
        </section>

        {/* Appearance */}
        <section className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Appearance</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-gray-900">Show Token Counts</div>
                <div className="text-sm text-gray-500">Display token usage in task views</div>
              </div>
              <button
                onClick={() => setPrefs({ ...prefs, show_token_counts: !prefs.show_token_counts })}
                className={`relative inline-flex h-6 w-11 items-center rounded-full ${
                  prefs.show_token_counts ? 'bg-primary-600' : 'bg-gray-200'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                  prefs.show_token_counts ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Editor Font Size</label>
              <input
                type="number"
                min="10"
                max="24"
                value={prefs.editor_font_size}
                onChange={(e) => setPrefs({ ...prefs, editor_font_size: parseInt(e.target.value) })}
                className="mt-1 block w-32 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>
        </section>

        {/* Notifications */}
        <section className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Notifications</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-gray-900">Task Completion</div>
                <div className="text-sm text-gray-500">Get notified when tasks finish</div>
              </div>
              <button
                onClick={() => setPrefs({ ...prefs, task_completion_notifications: !prefs.task_completion_notifications })}
                className={`relative inline-flex h-6 w-11 items-center rounded-full ${
                  prefs.task_completion_notifications ? 'bg-primary-600' : 'bg-gray-200'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                  prefs.task_completion_notifications ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>
          </div>
        </section>

        {/* Save */}
        <div className="flex items-center justify-end space-x-3">
          {saved && <span className="text-sm text-green-600">Saved!</span>}
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 text-sm font-medium disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
}
