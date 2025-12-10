import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"


export default function Statistics() {
    const [history, setHistory] = useState<any[]>([]);
    const [selectedSession, setSelectedSession] = useState<any>(null);
    const [detailsOpen, setDetailsOpen] = useState(false);
    const [loadingDetails, setLoadingDetails] = useState(false);

    useEffect(() => {
        api.get('/professor/attendance/history')
            .then(res => setHistory(res.data))
            .catch(console.error);
    }, []);

    const handleRowClick = async (session: any) => {
        setSelectedSession(session); // Set basic info first
        setDetailsOpen(true);
        setLoadingDetails(true);
        try {
            const res = await api.get(`/professor/attendance/session/${session.id}`);
            setSelectedSession(res.data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoadingDetails(false);
        }
    };

    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold px-1">Attendance History</h2>

            {/* Chart Placeholder */}
            {/* We could use Recharts here if requested, but for MVP a list is good */}

            <Card>
                <CardHeader>
                    <CardTitle>Recent Sessions</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Date</TableHead>
                                <TableHead>Course</TableHead>
                                <TableHead className="text-right">Students</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {history.map((session) => (
                                <TableRow key={session.id} onClick={() => handleRowClick(session)} className="cursor-pointer hover:bg-gray-50">
                                    <TableCell className="font-medium">
                                        {new Date(session.start_time).toLocaleDateString()}
                                        <div className="text-xs text-gray-500">
                                            {new Date(session.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        Course #{session.course_id}
                                        {/* Ideally we map ID to name if available or available in history obj */}
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <Badge variant="secondary">{session.student_count || 0}</Badge>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            <Dialog open={detailsOpen} onOpenChange={setDetailsOpen}>
                <DialogContent className="max-h-[80vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>Session Details</DialogTitle>
                    </DialogHeader>
                    {selectedSession && (
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-2 text-sm">
                                <div><strong>Date:</strong> {new Date(selectedSession.start_time).toLocaleString()}</div>
                                <div><strong>Total:</strong> {selectedSession.student_count || 0}</div>
                            </div>

                            <h4 className="font-semibold mt-4">Attendees</h4>
                            {loadingDetails ? <div className="text-sm text-gray-500">Loading list...</div> : (
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead>Student ID</TableHead>
                                            <TableHead>Status</TableHead>
                                            <TableHead>Time</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {selectedSession.attendees?.map((rec: any) => (
                                            <TableRow key={rec.id}>
                                                <TableCell>{rec.student_id}</TableCell>
                                                <TableCell><Badge variant="outline" className="text-green-600 border-green-200 bg-green-50">{rec.status}</Badge></TableCell>
                                                <TableCell className="text-xs text-gray-500">{new Date(rec.timestamp).toLocaleTimeString()}</TableCell>
                                            </TableRow>
                                        ))}
                                        {(!selectedSession.attendees || selectedSession.attendees.length === 0) && (
                                            <TableRow>
                                                <TableCell colSpan={3} className="text-center text-gray-500">No attendees recorded.</TableCell>
                                            </TableRow>
                                        )}
                                    </TableBody>
                                </Table>
                            )}
                        </div>
                    )}
                </DialogContent>
            </Dialog>
        </div>
    );
}
