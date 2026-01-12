import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { format } from 'date-fns';
import { Eye, Download, Users, Loader2 } from 'lucide-react';

interface Student {
    id: number;
    name: string;
    digital_id: number;
    email: string;
}

interface AttendanceRecord {
    id: number;
    status: string;
    timestamp: string;
    student: Student;
}

interface Session {
    id: number;
    start_time: string;
    end_time: string;
    is_active: boolean;
    student_count: number;
    assignment?: {
        course?: { name: string; code: string };
        class_group?: { name: string };
    };
}

interface SessionDetails extends Session {
    records: AttendanceRecord[];
}

export default function Statistics() {
    const [sessions, setSessions] = useState<Session[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedSession, setSelectedSession] = useState<SessionDetails | null>(null);
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [isLoadingDetails, setIsLoadingDetails] = useState(false);

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

    const handleViewDetails = async (sessionId: number) => {
        setIsDialogOpen(true);
        setIsLoadingDetails(true);
        try {
            const res = await api.get(`/professor/attendance/session/${sessionId}`);
            setSelectedSession(res.data);
        } catch (error) {
            console.error("Failed to fetch session details");
        } finally {
            setIsLoadingDetails(false);
        }
    };

    const handleDownloadCSV = () => {
        if (!selectedSession || !selectedSession.records) return;

        const courseName = selectedSession.assignment?.course?.name || 'Unknown';
        const className = selectedSession.assignment?.class_group?.name || 'Unknown';
        const dateStr = format(new Date(selectedSession.start_time), 'yyyy-MM-dd');

        // Create CSV content
        const headers = ['S.No', 'Student Name', 'Student ID', 'Email', 'Status', 'Timestamp'];
        const rows = selectedSession.records.map((record, index) => [
            index + 1,
            record.student?.name || 'Unknown',
            record.student?.digital_id || 'N/A',
            record.student?.email || 'N/A',
            record.status,
            format(new Date(record.timestamp), 'yyyy-MM-dd HH:mm:ss')
        ]);

        const csvContent = [
            headers.join(','),
            ...rows.map(row => row.join(','))
        ].join('\n');

        // Download file
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `Attendance_${courseName}_${className}_${dateStr}.csv`;
        link.click();
        URL.revokeObjectURL(link.href);
    };

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
                                <TableHead className="text-center">Students</TableHead>
                                <TableHead className="text-right">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {sessions.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={6} className="text-center text-muted-foreground">
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
                                        <TableCell className="text-center">
                                            <div className="flex items-center justify-center gap-1">
                                                <Users className="h-4 w-4 text-muted-foreground" />
                                                <span className="font-medium">{session.student_count || 0}</span>
                                            </div>
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => handleViewDetails(session.id)}
                                            >
                                                <Eye className="h-4 w-4 mr-1" />
                                                View Details
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            {/* Session Details Dialog */}
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                <DialogContent className="max-w-3xl max-h-[80vh] flex flex-col">
                    <DialogHeader>
                        <DialogTitle>
                            {selectedSession ? (
                                <>
                                    {selectedSession.assignment?.course?.name || 'Session Details'}
                                    <span className="text-muted-foreground font-normal ml-2">
                                        ({selectedSession.assignment?.class_group?.name})
                                    </span>
                                </>
                            ) : 'Session Details'}
                        </DialogTitle>
                        <DialogDescription>
                            {selectedSession && format(new Date(selectedSession.start_time), 'MMMM d, yyyy • h:mm a')}
                        </DialogDescription>
                    </DialogHeader>

                    {isLoadingDetails ? (
                        <div className="flex items-center justify-center py-12">
                            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                        </div>
                    ) : selectedSession?.records && selectedSession.records.length > 0 ? (
                        <>
                            <div className="flex-1 overflow-auto border rounded-md">
                                <Table>
                                    <TableHeader className="sticky top-0 bg-background">
                                        <TableRow>
                                            <TableHead className="w-12">S.No</TableHead>
                                            <TableHead>Student Name</TableHead>
                                            <TableHead>Student ID</TableHead>
                                            <TableHead>Status</TableHead>
                                            <TableHead className="text-right">Time</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {selectedSession.records.map((record, index) => (
                                            <TableRow key={record.id}>
                                                <TableCell className="font-medium">{index + 1}</TableCell>
                                                <TableCell className="font-medium">{record.student?.name || 'Unknown'}</TableCell>
                                                <TableCell className="text-muted-foreground">{record.student?.digital_id}</TableCell>
                                                <TableCell>
                                                    <Badge variant={record.status === 'PRESENT' ? 'default' : 'secondary'}>
                                                        {record.status}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell className="text-right text-muted-foreground">
                                                    {format(new Date(record.timestamp), 'h:mm:ss a')}
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </div>
                            <div className="flex justify-between items-center pt-4 border-t">
                                <div className="text-sm text-muted-foreground">
                                    Total: <span className="font-medium text-foreground">{selectedSession.records.length}</span> students
                                </div>
                                <Button onClick={handleDownloadCSV}>
                                    <Download className="h-4 w-4 mr-2" />
                                    Download CSV
                                </Button>
                            </div>
                        </>
                    ) : (
                        <div className="text-center py-12 text-muted-foreground">
                            No attendance records for this session.
                        </div>
                    )}
                </DialogContent>
            </Dialog>
        </div>
    );
}