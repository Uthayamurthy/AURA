import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Device {
  type: 'beacon' | 'headcount';
  device_id: string;
  status: 'online' | 'offline';
  last_seen: number;
  headcount: number | null;
}

function formatRelativeTime(epochSeconds: number): string {
  const diff = Math.floor(Date.now() / 1000 - epochSeconds);
  if (diff < 5) return 'just now';
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export default function Devices() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [, setTick] = useState(0);

  // Tick for relative time updates
  useEffect(() => {
    const timer = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const { data: initialDevices, isLoading, error } = useQuery({
    queryKey: ['adminDevices'],
    queryFn: async () => {
      const res = await api.get('/admin/devices');
      return res.data as Device[];
    }
  });

  useEffect(() => {
    if (initialDevices) {
      setDevices(initialDevices);
    }
  }, [initialDevices]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;

    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
    const wsURL = baseURL.replace(/^http/, 'ws') + `/admin/ws/devices?token=${token}`;
    
    const ws = new WebSocket(wsURL);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'device_update' && data.devices) {
          setDevices(data.devices);
        }
      } catch (err) {
        console.error('WebSocket message parsing error:', err);
      }
    };

    return () => {
      ws.onclose = null;
      ws.close();
    };
  }, []);

  if (isLoading && devices.length === 0) {
    return <div className="p-8">Loading devices...</div>;
  }

  if (error && devices.length === 0) {
    return <div className="p-8 text-red-500">Error loading devices</div>;
  }

  const beaconDevices = devices.filter(d => d.type === 'beacon');
  const headcountDevices = devices.filter(d => d.type === 'headcount');

  return (
    <div className="flex-1 space-y-6 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Device Monitor</h2>
          <p className="text-muted-foreground mt-1 text-sm">Real-time status of all connected AURA devices</p>
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold">Beacon Devices</h3>
          <span className="bg-zinc-100 text-zinc-800 text-xs font-semibold px-2.5 py-0.5 rounded-full dark:bg-zinc-800 dark:text-zinc-300">
            {beaconDevices.length}
          </span>
        </div>
        
        {beaconDevices.length === 0 ? (
          <div className="text-sm text-muted-foreground p-8 text-center border rounded-lg border-dashed">
            No devices detected yet. Devices will appear once they send their first heartbeat.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {beaconDevices.map(device => (
              <Card key={device.device_id}>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex justify-between items-center">
                    {device.device_id.split('_').join(' — ')}
                    <div className="flex items-center gap-2 text-sm font-medium">
                      <span className={`w-2.5 h-2.5 rounded-full ${device.status === 'online' ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
                      <span className={device.status === 'online' ? 'text-green-600 dark:text-green-500' : 'text-red-600 dark:text-red-500'}>
                        {device.status === 'online' ? 'Online' : 'Offline'}
                      </span>
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    Last seen: {formatRelativeTime(device.last_seen)}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <div className="space-y-4">
        <div className="flex items-center gap-2 mt-8">
          <h3 className="text-lg font-semibold">Headcount Devices</h3>
          <span className="bg-zinc-100 text-zinc-800 text-xs font-semibold px-2.5 py-0.5 rounded-full dark:bg-zinc-800 dark:text-zinc-300">
            {headcountDevices.length}
          </span>
        </div>
        
        {headcountDevices.length === 0 ? (
          <div className="text-sm text-muted-foreground p-8 text-center border rounded-lg border-dashed">
            No devices detected yet. Devices will appear once they send their first heartbeat.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {headcountDevices.map(device => (
              <Card key={device.device_id}>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex justify-between items-center">
                    {device.device_id}
                    <div className="flex items-center gap-2 text-sm font-medium">
                      <span className={`w-2.5 h-2.5 rounded-full ${device.status === 'online' ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
                      <span className={device.status === 'online' ? 'text-green-600 dark:text-green-500' : 'text-red-600 dark:text-red-500'}>
                        {device.status === 'online' ? 'Online' : 'Offline'}
                      </span>
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col items-center py-6">
                  <div className="text-5xl font-bold tabular-nums text-zinc-900 dark:text-zinc-50">
                    {device.headcount !== null ? device.headcount : '-'}
                  </div>
                  <div className="text-sm font-medium text-muted-foreground mt-2 uppercase tracking-wider">People in room</div>
                  <p className="text-xs text-muted-foreground mt-6 w-full text-center border-t pt-4">
                    Last seen: {formatRelativeTime(device.last_seen)}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
