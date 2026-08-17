import { useEffect, useRef, useCallback, useState } from 'react';

interface WebSocketMessage {
    type: 'headcount_update' | 'attendance_update';
    session_id: number;
    headcount: number | null;
    attendance_count: number;
    new_record?: {
        id: number;
        student_name: string;
        student_id: number;
        digital_id: number;
        timestamp: string;
        status: string;
    };
}

interface UseSessionWebSocketOptions {
    sessionId: number | null;
    onHeadcountUpdate?: (headcount: number | null, attendanceCount: number) => void;
    onAttendanceUpdate?: (message: WebSocketMessage) => void;
}

export function useSessionWebSocket({ sessionId, onHeadcountUpdate, onAttendanceUpdate }: UseSessionWebSocketOptions) {
    const wsRef = useRef<WebSocket | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
    const reconnectAttempts = useRef(0);
    
    const onHeadcountUpdateRef = useRef(onHeadcountUpdate);
    const onAttendanceUpdateRef = useRef(onAttendanceUpdate);
    
    useEffect(() => {
        onHeadcountUpdateRef.current = onHeadcountUpdate;
        onAttendanceUpdateRef.current = onAttendanceUpdate;
    }, [onHeadcountUpdate, onAttendanceUpdate]);

    const connect = useCallback(() => {
        if (!sessionId) return;
        
        const token = localStorage.getItem('aura_prof_token');
        if (!token) return;

        // Build WebSocket URL from the API base URL
        const serverUrl = localStorage.getItem('aura_server_url') || import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
        const wsBase = serverUrl.replace(/^http/, 'ws');
        const cleanWsBase = wsBase.replace(/\/+$/, '');
        const wsUrl = `${cleanWsBase}/professor/ws/session/${sessionId}?token=${token}`;

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            setIsConnected(true);
            reconnectAttempts.current = 0;
        };

        ws.onmessage = (event) => {
            try {
                const data: WebSocketMessage = JSON.parse(event.data);
                if (data.type === 'headcount_update') {
                    onHeadcountUpdateRef.current?.(data.headcount, data.attendance_count);
                } else if (data.type === 'attendance_update') {
                    onAttendanceUpdateRef.current?.(data);
                }
            } catch (e) {
                console.error('Failed to parse WebSocket message', e);
            }
        };

        ws.onclose = () => {
            setIsConnected(false);
            // Auto-reconnect with exponential backoff
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
            reconnectAttempts.current++;
            reconnectTimeoutRef.current = setTimeout(connect, delay);
        };

        ws.onerror = () => {
            ws.close();
        };
    }, [sessionId]);

    useEffect(() => {
        connect();
        return () => {
            if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
            if (wsRef.current) {
                wsRef.current.onclose = null;
                wsRef.current.close();
                wsRef.current = null;
            }
        };
    }, [connect]);

    return { isConnected };
}
