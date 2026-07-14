'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileNode[];
}

interface FileExplorerProps {
  projectId: string;
  onSelectFile?: (path: string) => void;
  selectedFile?: string;
}

function FileIcon({ name }: { name: string }) {
  const ext = name.split('.').pop()?.toLowerCase();
  const color = {
    py: 'text-blue-500',
    js: 'text-yellow-500',
    ts: 'text-blue-600',
    tsx: 'text-blue-600',
    jsx: 'text-yellow-400',
    json: 'text-green-500',
    md: 'text-gray-500',
    css: 'text-purple-500',
    html: 'text-orange-500',
    yml: 'text-pink-500',
    yaml: 'text-pink-500',
    toml: 'text-gray-500',
    txt: 'text-gray-400',
    gitignore: 'text-gray-400',
  }[ext || ''] || 'text-gray-400';

  return (
    <svg className={`w-4 h-4 ${color}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  );
}

function TreeItem({ node, depth, onSelectFile, selectedFile }: {
  node: FileNode;
  depth: number;
  onSelectFile?: (path: string) => void;
  selectedFile?: string;
}) {
  const [expanded, setExpanded] = useState(depth < 1);

  if (node.type === 'directory') {
    return (
      <div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center w-full px-2 py-1 text-sm hover:bg-gray-100 rounded"
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
        >
          <svg className={`w-3 h-3 mr-1 transition-transform ${expanded ? 'rotate-90' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <svg className="w-4 h-4 text-yellow-500 mr-2" fill="currentColor" viewBox="0 0 24 24">
            <path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" />
          </svg>
          <span>{node.name}</span>
        </button>
        {expanded && node.children && (
          <div>
            {node.children
              .sort((a, b) => {
                if (a.type !== b.type) return a.type === 'directory' ? -1 : 1;
                return a.name.localeCompare(b.name);
              })
              .map((child) => (
                <TreeItem
                  key={child.path}
                  node={child}
                  depth={depth + 1}
                  onSelectFile={onSelectFile}
                  selectedFile={selectedFile}
                />
              ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <button
      onClick={() => onSelectFile?.(node.path)}
      className={`flex items-center w-full px-2 py-1 text-sm rounded ${
        selectedFile === node.path ? 'bg-primary-100 text-primary-700' : 'hover:bg-gray-100'
      }`}
      style={{ paddingLeft: `${depth * 16 + 24}px` }}
    >
      <FileIcon name={node.name} />
      <span className="ml-2">{node.name}</span>
    </button>
  );
}

export function FileExplorer({ projectId, onSelectFile, selectedFile }: FileExplorerProps) {
  const [tree, setTree] = useState<FileNode | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadFiles();
  }, [projectId]);

  const loadFiles = async () => {
    try {
      setLoading(true);
      const files = await api.searchRepository(projectId, '');
      const tree = buildTree(files);
      setTree(tree);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const buildTree = (files: any[]): FileNode => {
    const root: FileNode = { name: '', path: '', type: 'directory', children: [] };
    
    for (const file of files) {
      const path = file.file_path || file.path || '';
      const parts = path.split('/').filter(Boolean);
      let current = root;
      
      for (let i = 0; i < parts.length; i++) {
        if (!current.children) current.children = [];
        
        const existing = current.children.find(c => c.name === parts[i]);
        if (existing) {
          current = existing;
        } else {
          const isFile = i === parts.length - 1;
          const newNode: FileNode = {
            name: parts[i],
            path: parts.slice(0, i + 1).join('/'),
            type: isFile ? 'file' : 'directory',
            children: isFile ? undefined : [],
          };
          current.children.push(newNode);
          current = newNode;
        }
      }
    }
    
    return root;
  };

  if (loading) return <div className="p-4 text-sm text-gray-500">Loading files...</div>;
  if (error) return <div className="p-4 text-sm text-red-500">{error}</div>;
  if (!tree?.children?.length) return <div className="p-4 text-sm text-gray-500">No files indexed</div>;

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="text-sm font-medium text-gray-900">Files</h3>
      </div>
      <div className="max-h-96 overflow-y-auto py-1">
        {tree.children
          .sort((a, b) => {
            if (a.type !== b.type) return a.type === 'directory' ? -1 : 1;
            return a.name.localeCompare(b.name);
          })
          .map((node) => (
            <TreeItem
              key={node.path}
              node={node}
              depth={0}
              onSelectFile={onSelectFile}
              selectedFile={selectedFile}
            />
          ))}
      </div>
    </div>
  );
}
