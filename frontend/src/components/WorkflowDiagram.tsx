'use client';

import { useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  Position,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';

export interface AgentNode {
  id: string;
  label: string;
  icon: string;
  description: string;
  status: 'pending' | 'active' | 'completed' | 'error';
}

interface WorkflowDiagramProps {
  nodes: AgentNode[];
  onNodeClick?: (nodeId: string) => void;
}

const NODE_WIDTH = 160;
const NODE_HEIGHT = 60;
const H_SPACING = 60;
const V_POS = 200;

const statusColors = {
  pending: { bg: '#1e293b', border: '#334155', text: '#94a3b8', glow: 'none' },
  active: { bg: '#1e3a5f', border: '#3b82f6', text: '#60a5fa', glow: '0 0 12px #3b82f680' },
  completed: { bg: '#064e3b', border: '#10b981', text: '#34d399', glow: 'none' },
  error: { bg: '#450a0a', border: '#ef4444', text: '#fca5a5', glow: 'none' },
};

export default function WorkflowDiagram({ nodes, onNodeClick }: WorkflowDiagramProps) {
  const flowNodes: Node[] = useMemo(() => {
    const totalWidth = nodes.length * NODE_WIDTH + (nodes.length - 1) * H_SPACING;
    const startX = 0;

    return nodes.map((n, i) => ({
      id: n.id,
      type: 'default',
      position: { x: startX + i * (NODE_WIDTH + H_SPACING), y: V_POS },
      data: { label: n.label, icon: n.icon, status: n.status, description: n.description },
      style: {
        width: NODE_WIDTH,
        padding: '8px 12px',
        borderRadius: '10px',
        border: `2px solid ${statusColors[n.status].border}`,
        background: statusColors[n.status].bg,
        color: statusColors[n.status].text,
        fontSize: '13px',
        fontFamily: 'inherit',
        boxShadow: statusColors[n.status].glow,
        cursor: 'pointer',
        transition: 'all 0.3s ease',
      },
    }));
  }, [nodes]);

  const flowEdges: Edge[] = useMemo(() => {
    return nodes.slice(0, -1).map((_, i) => ({
      id: `e-${i}-${i + 1}`,
      source: nodes[i].id,
      target: nodes[i + 1].id,
      type: 'smoothstep',
      animated: nodes[i + 1].status === 'active',
      style: {
        stroke: nodes[i + 1].status === 'active' ? '#3b82f6' : nodes[i].status === 'completed' ? '#10b981' : '#334155',
        strokeWidth: 2,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: nodes[i + 1].status === 'active' ? '#3b82f6' : nodes[i].status === 'completed' ? '#10b981' : '#334155',
      },
    }));
  }, [nodes]);

  const onNodeClickHandler = useCallback(
    (_: React.MouseEvent, node: Node) => {
      if (onNodeClick) onNodeClick(node.id);
    },
    [onNodeClick]
  );

  return (
    <div className="w-full h-[420px] rounded-xl overflow-hidden border border-gray-700 bg-gray-900">
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        fitView
        minZoom={0.5}
        maxZoom={2}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        onNodeClick={onNodeClickHandler}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#1e293b" gap={20} />
        <Controls showInteractive={false} className="[&>button]:bg-gray-800 [&>button]:border-gray-600 [&>button]:text-white" />
        <MiniMap
          nodeColor={() => '#334155'}
          maskColor="rgba(0,0,0,0.6)"
          style={{ background: '#0f172a' }}
        />
      </ReactFlow>
    </div>
  );
}
