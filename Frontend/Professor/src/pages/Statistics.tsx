import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { format } from 'date-fns';

export default function Statistics() {
    const [sessions, setSessions] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const res = await api.get('/professor/attendance/history');
                setSessions(res.data);
            } catch (error) {
                console.error("Failed to fetch history");
            } finally {
                setIsLoading(false);
            }
        };
        fetchHistory();
    }, []);

    if (isLoading) return <div className="p-8">Loading history...</div>;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Attendance History</h1>
                <p className="text-muted-foreground">View past sessions and records.</p>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Recent Sessions</CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Date</TableHead>
                                <TableHead>Course</TableHead>
                                <TableHead>Class Group</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead className="text-right">Students</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {sessions.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={5} className="text-center text-muted-foreground">
                                        No sessions found.
                                    </TableCell>
                                </TableRow>
                            ) : (
                                sessions.map((session) => (
                                    <TableRow key={session.id}>
                                        <TableCell>
                                            <div className="font-medium">
                                                {format(new Date(session.start_time), 'MMM d, yyyy')}
                                            </div>
                                            <div className="text-xs text-muted-foreground">
                                                {format(new Date(session.start_time), 'h:mm a')}
                                            </div>
                                        </TableCell>
                                        <TableCell>{session.assignment?.course?.name || "Unknown Course"}</TableCell>
                                        <TableCell>
                                            <Badge variant="outline">{session.assignment?.class_group?.name || "N/A"}</Badge>
                                        </TableCell>
                                        <TableCell>
                                            {session.is_active ? 
                                                <Badge className="bg-green-500">Active</Badge> : 
                                                <Badge variant="secondary">Completed</Badge>
                                            }
                                        </TableCell>
                                        <TableCell className="text-right font-medium">
                                            {session.student_count || 0}
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}