'use client';

import { useEffect, useRef, useCallback, useState } from 'react';

interface WebSocketMessage {
  type: 'task_update' | 'agent_update' | 'log' | 'pong';
  task_id: string;
  [key: string]: any;
}

interface UseTaskSocketOptions {
  taskId: string;
  onTaskUpdate?: (data: any) => void;
  onAgentUpdate?: (data: any) => void;
  onLog?: (data: any) => void;
  enabled?: boolean;
}

export function useTaskSocket({
  taskId,
  onTaskUpdate,
  onAgentUpdate,
  onLog,
  enabled = true,
}: UseTaskSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectCountRef = useRef(0);

  const connect = useCallback(() => {
    if (!enabled || !taskId) return;

    const apiBase = process.env.NEXT_PUBLIC_API_URL || '';
    let wsUrl: string;
    
    if (apiBase) {
      // Use configured API URL (convert http -> ws, https -> wss)
      wsUrl = apiBase.replace(/^http/, 'ws') + `/ws/tasks/${taskId}`;
    } else {
      // Fallback: use current browser host
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      wsUrl = `${protocol}//${window.location.host}/ws/tasks/${taskId}`;
    }

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        reconnectCountRef.current = 0;
        
        // Send periodic pings
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          } else {
            clearInterval(pingInterval);
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);

          switch (message.type) {
            case 'task_update':
              onTaskUpdate?.(message.data);
              break;
            case 'agent_update':
              onAgentUpdate?.(message);
              break;
            case 'log':
              onLog?.(message);
              break;
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        wsRef.current = null;
        
        // Reconnect with exponential backoff
        if (enabled && reconnectCountRef.current < 5) {
          const delay = Math.min(1000 * Math.pow(2, reconnectCountRef.current), 30000);
          reconnectCountRef.current++;
          reconnectTimeoutRef.current = setTimeout(connect, delay);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch (e) {
      console.error('WebSocket connection error:', e);
    }
  }, [taskId, enabled, onTaskUpdate, onAgentUpdate, onLog]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { connected, lastMessage };
}
