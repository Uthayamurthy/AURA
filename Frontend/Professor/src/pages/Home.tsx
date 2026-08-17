import { useState, useEffect } from 'react';
// import { useNavigate } from 'react-router-dom'; // Unused
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Play, Users, Loader2, ShieldCheck, AlertTriangle, CheckCircle, Radio, UserMinus, RefreshCw, Save } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { useSessionWebSocket } from '@/hooks/useSessionWebSocket';

// Interfaces
interface Course {
    id: number;
    code: string;
    name: string;
}

interface ClassGroup {
    id: number;
    name: string;
}

interface TeachingAssignment {
    id: number;
    course_id: number;
    class_group_id: number;
    default_classroom?: string;
    course: Course;
    class_group: ClassGroup;
}

interface Student {
    id: number;
    name: string;
    digital_id: number;
}

interface AttendanceRecord {
    id: number;
    status: string;
    timestamp: string;
    student: Student;
}

interface ActiveSession {
    id: number;
    current_code: string | null;
    start_time: string;
    end_time: string;
    assignment: TeachingAssignment;
    records?: AttendanceRecord[];
    headcount?: number | null;
    room_number?: string;
    is_verified?: boolean;
    verification_status?: string;
}

interface VerifyResponse {
    session_id: number;
    headcount: number | null;
    headcount_students: number | null;
    attendance_count: number;
    is_match: boolean;
    difference: number;
    records: AttendanceRecord[];
}

export default function Home() {
    // const navigate = useNavigate(); // Unused
    const [assignments, setAssignments] = useState<TeachingAssignment[]>([]);
    const [activeSession, setActiveSession] = useState<ActiveSession | null>(null);
    const [selectedAssignmentId, setSelectedAssignmentId] = useState<string>("");
    const [duration, setDuration] = useState("5");
    const [isStartDialogOpen, setIsStartDialogOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    const [headcount, setHeadcount] = useState<number | null>(null);
    const [attendanceCount, setAttendanceCount] = useState<number>(0);
    const [isVerifyDialogOpen, setIsVerifyDialogOpen] = useState(false);
    const [verifyResult, setVerifyResult] = useState<VerifyResponse | null>(null);
    const [isVerifying, setIsVerifying] = useState(false);
    const [isRemoveDialogOpen, setIsRemoveDialogOpen] = useState(false);
    const [selectedRecordId, setSelectedRecordId] = useState<number | null>(null);
    const [isRetaking, setIsRetaking] = useState(false);

    const { isConnected } = useSessionWebSocket({
        sessionId: activeSession?.id ?? null,
        onHeadcountUpdate: (hc, ac) => {
            setHeadcount(hc);
            setAttendanceCount(ac);
            if (hc !== null) {
                const students = hc - 1;
                if (students !== ac) {
                    toast.warning(`Headcount mismatch: ${students} in room, ${ac} registered`);
                }
            }
        },
        onAttendanceUpdate: (msg) => {
            setAttendanceCount(msg.attendance_count);
            if (msg.headcount !== null && msg.headcount !== undefined) {
                setHeadcount(msg.headcount);
            }
            if (msg.new_record && activeSession) {
                setActiveSession(prev => {
                    if (!prev) return prev;
                    if (prev.records?.some(r => r.id === msg.new_record!.id)) return prev;
                    const newRecord: AttendanceRecord = {
                        id: msg.new_record!.id,
                        status: msg.new_record!.status,
                        timestamp: msg.new_record!.timestamp,
                        student: {
                            id: msg.new_record!.student_id,
                            name: msg.new_record!.student_name,
                            digital_id: msg.new_record!.digital_id,
                        }
                    };
                    return {
                        ...prev,
                        records: [...(prev.records || []), newRecord]
                    };
                });
            }
        }
    });

    // Initial Load
    useEffect(() => {
        fetchData();
    }, []);

    // POLLING: Refresh active session every 5 seconds to check for CODE
    useEffect(() => {
        let interval: any;
        if (activeSession) {
            interval = setInterval(refreshSessionStatus, 5000);
        }
        return () => clearInterval(interval);
    }, [activeSession]);

    const fetchData = async () => {
        try {
            const [coursesRes, historyRes] = await Promise.all([
                api.get('/professor/my-courses'),
                api.get('/professor/attendance/history')
            ]);
            setAssignments(coursesRes.data);

            const running = historyRes.data.find((s: any) => s.is_active);
            if (running) {
                const sessionRes = await api.get(`/professor/attendance/session/${running.id}`);
                setActiveSession({ ...sessionRes.data, assignment: running.assignment });
                setHeadcount(sessionRes.data.headcount ?? null);
                setAttendanceCount(sessionRes.data.records?.length ?? 0);
            }
        } catch (error) {
            console.error("Failed to fetch data", error);
        } finally {
            setIsLoading(false);
        }
    };

    const refreshSessionStatus = async () => {
        // Just fetch history silently to update the code
        try {
            // Changed to fetch specific session details including attendees
            const sessionRes = await api.get(`/professor/attendance/session/${activeSession?.id}`);
            setActiveSession(sessionRes.data);
        } catch (e) {
            console.error("Failed to refresh session", e);
            // If 404, session might be gone
            // setActiveSession(null); 
        }
    };

    const handleVerify = async () => {
        if (!activeSession) return;
        setIsVerifying(true);
        try {
            const res = await api.post(`/professor/attendance/verify/${activeSession.id}`);
            setVerifyResult(res.data);
            setIsVerifyDialogOpen(true);
        } catch (error) {
            toast.error('Failed to verify headcount');
        } finally {
            setIsVerifying(false);
        }
    };

    const handleRetake = async () => {
        if (!activeSession) return;
        setIsRetaking(true);
        try {
            const res = await api.post(`/professor/attendance/retake/${activeSession.id}`);
            const assignment = activeSession.assignment;
            setActiveSession({ ...res.data, assignment });
            setVerifyResult(null);
            setIsVerifyDialogOpen(false);
            setHeadcount(null);
            setAttendanceCount(0);
            toast.success('Attendance retake started');
        } catch (error) {
            toast.error('Failed to retake attendance');
        } finally {
            setIsRetaking(false);
        }
    };

    const handleRemoveStudent = async () => {
        if (!selectedRecordId) return;
        try {
            await api.delete(`/professor/attendance/record/${selectedRecordId}`);
            setActiveSession(prev => {
                if (!prev) return prev;
                return {
                    ...prev,
                    records: prev.records?.filter(r => r.id !== selectedRecordId) || []
                };
            });
            setVerifyResult(prev => {
                if (!prev) return prev;
                const newCount = prev.attendance_count - 1;
                const newRecords = prev.records.filter(r => r.id !== selectedRecordId);
                const isMatch = prev.headcount_students === newCount;
                return {
                    ...prev,
                    records: newRecords,
                    attendance_count: newCount,
                    is_match: isMatch,
                    difference: (prev.headcount_students ?? 0) - newCount
                };
            });
            setSelectedRecordId(null);
            setIsRemoveDialogOpen(false);
            toast.success('Student record removed');
        } catch (error) {
            toast.error('Failed to remove record');
        }
    };

    const handleSaveAnyway = async () => {
        if (!activeSession) return;
        try {
            await api.post(`/professor/attendance/verify/${activeSession.id}/save`);
            setIsVerifyDialogOpen(false);
            setVerifyResult(null);
            toast.success('Records saved despite mismatch');
        } catch (error) {
            toast.error('Failed to save');
        }
    };

    const handleStartSession = async () => {
        if (!selectedAssignmentId) return;
        const assignment = assignments.find(a => a.id.toString() === selectedAssignmentId);
        if (!assignment) return;

        const roomToSend = assignment.default_classroom || "LH49";

        try {
            const res = await api.post('/professor/attendance/start', {
                course_id: assignment.course_id,
                class_group_id: assignment.class_group_id,
                duration_minutes: parseInt(duration),
                room_number: roomToSend
            });
            // Optimistic update (Code will be null initially, Polling will fix it)
            setActiveSession({ ...res.data, assignment: assignment });
            setIsStartDialogOpen(false);
        } catch (error) {
            toast.error("Failed to start session");
        }
    };

    const handleStopSession = async () => {
        if (!activeSession) return;
        try {
            await api.post(`/professor/attendance/stop/${activeSession.id}`);
            setActiveSession(null);
        } catch (error) {
            toast.error("Failed to stop session");
        }
    };

    if (isLoading) return <div className="p-8">Loading dashboard...</div>;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
                    <p className="text-muted-foreground">Manage your classes and attendance.</p>
                </div>
                {activeSession ? (
                    <div className="flex items-center gap-2">
                        <Button variant="outline" onClick={handleVerify} disabled={isVerifying || headcount === null}>
                            {isVerifying ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <ShieldCheck className="mr-2 h-4 w-4" />}
                            Verify Headcount
                        </Button>
                        <Button variant="destructive" onClick={handleStopSession}>Stop Current Session</Button>
                    </div>
                ) : (
                    <Button onClick={() => setIsStartDialogOpen(true)}>
                        <Play className="mr-2 h-4 w-4" /> Start Attendance
                    </Button>
                )}
            </div>

            {/* Active Session Card */}
            {activeSession && (
                <Card className="border-green-500/50 bg-green-500/10">
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle className="text-green-700">Session in Progress</CardTitle>
                                <CardDescription>
                                    {/* These will now appear correctly thanks to the schema fix */}
                                    {activeSession.assignment?.course?.name} ({activeSession.assignment?.class_group?.name})
                                </CardDescription>
                            </div>
                            <div className="text-right">
                                {activeSession.current_code ? (
                                    <div className="text-4xl font-mono font-bold text-green-800 tracking-wider">
                                        {activeSession.current_code}
                                    </div>
                                ) : (
                                    <div className="flex items-center gap-2 text-green-800">
                                        <Loader2 className="animate-spin h-5 w-5" />
                                        <span className="font-mono font-bold">WAITING...</span>
                                    </div>
                                )}
                                <div className="flex items-center justify-end gap-1 text-xs text-green-600 mt-1">
                                    <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-400'}`} />
                                    Beacon Active
                                </div>
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent>
                        {/* Live Headcount Stats */}
                        <div className="grid grid-cols-2 gap-3 mb-4">
                            <div className="bg-white rounded-lg border p-3 flex flex-col items-center">
                                <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground mb-1">
                                    <Radio className="h-3.5 w-3.5" />
                                    Physical Headcount
                                </div>
                                <div className="text-2xl font-bold tabular-nums">
                                    {headcount !== null ? headcount - 1 : '—'}
                                </div>
                                <div className="text-[10px] text-muted-foreground">students (excl. professor)</div>
                            </div>
                            <div className="bg-white rounded-lg border p-3 flex flex-col items-center">
                                <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground mb-1">
                                    <Users className="h-3.5 w-3.5" />
                                    Registered
                                </div>
                                <div className="text-2xl font-bold tabular-nums">
                                    {activeSession.records?.length ?? attendanceCount}
                                </div>
                                <div className="text-[10px] text-muted-foreground">students checked in</div>
                            </div>
                        </div>

                        {/* Mismatch warning banner */}
                        {headcount !== null && (headcount - 1) !== (activeSession.records?.length ?? attendanceCount) && (
                            <div className="flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-4 text-sm text-amber-800">
                                <AlertTriangle className="h-4 w-4 shrink-0" />
                                <span>Headcount mismatch detected. Verify when ready.</span>
                            </div>
                        )}

                        {activeSession.records && activeSession.records.length > 0 ? (
                            <div className="mt-4 border rounded-md overflow-hidden">
                                <table className="w-full text-sm">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-4 py-2 text-left">Student</th>
                                            <th className="px-4 py-2 text-left">ID</th>
                                            <th className="px-4 py-2 text-right">Time</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y">
                                        {activeSession.records.map((record) => (
                                            <tr key={record.id} className="bg-white">
                                                <td className="px-4 py-2 font-medium">{record.student?.name}</td>
                                                <td className="px-4 py-2 text-gray-500">{record.student?.digital_id}</td>
                                                <td className="px-4 py-2 text-right text-gray-500">
                                                    {new Date(record.timestamp).toLocaleTimeString()}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className="mt-4 text-center text-sm text-muted-foreground p-4 bg-white/50 rounded-md border border-dashed">
                                No students have checked in yet.
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {assignments.map((assign) => (
                    <Card key={assign.id}>
                        <CardHeader>
                            <div className="flex justify-between items-start">
                                <div>
                                    <CardTitle>{assign.course.name}</CardTitle>
                                    <CardDescription>{assign.course.code}</CardDescription>
                                </div>
                                <Badge variant="outline">{assign.class_group.name}</Badge>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
                                <div className="flex items-center gap-1">
                                    <Users className="h-4 w-4" />
                                    <span>Class Group: {assign.class_group.name}</span>
                                </div>
                                <div className="flex items-center gap-2 text-blue-600 font-medium">
                                    <span> Room: {assign.default_classroom || "N/A"}</span>
                                </div>
                            </div>
                            <Button
                                className="w-full"
                                variant="secondary"
                                onClick={() => { setSelectedAssignmentId(assign.id.toString()); setIsStartDialogOpen(true); }}
                                disabled={!!activeSession}
                            >
                                Start Class
                            </Button>
                        </CardContent>
                    </Card>
                ))}
            </div>

            <Dialog open={isStartDialogOpen} onOpenChange={setIsStartDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Start Attendance Session</DialogTitle>
                        <DialogDescription>Select duration for {assignments.find(a => a.id.toString() === selectedAssignmentId)?.course.name}</DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Duration</label>
                            <Select value={duration} onValueChange={setDuration}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="5">5 Minutes</SelectItem>
                                    <SelectItem value="10">10 Minutes</SelectItem>
                                    <SelectItem value="15">15 Minutes</SelectItem>
                                    <SelectItem value="60">1 Hour</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setIsStartDialogOpen(false)}>Cancel</Button>
                        <Button onClick={handleStartSession}>Start Broadcast</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            <Dialog open={isVerifyDialogOpen} onOpenChange={setIsVerifyDialogOpen}>
                <DialogContent className="max-w-md">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            {verifyResult?.is_match ? (
                                <><CheckCircle className="h-5 w-5 text-green-600" /> Headcount Verified</>
                            ) : (
                                <><AlertTriangle className="h-5 w-5 text-amber-600" /> Headcount Mismatch</>
                            )}
                        </DialogTitle>
                        <DialogDescription>
                            {verifyResult?.is_match
                                ? 'Physical headcount matches registered attendance.'
                                : `Physical headcount shows ${verifyResult?.headcount_students ?? '?'} students, but ${verifyResult?.attendance_count ?? 0} have registered.`
                            }
                        </DialogDescription>
                    </DialogHeader>

                    {!verifyResult?.is_match && (
                        <div className="space-y-2 pt-2">
                            <p className="text-sm font-medium text-muted-foreground">Choose an action:</p>
                            <Button variant="outline" className="w-full justify-start" onClick={handleRetake} disabled={isRetaking}>
                                {isRetaking ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
                                Retake Attendance
                            </Button>
                            <Button variant="outline" className="w-full justify-start" onClick={() => setIsRemoveDialogOpen(true)}>
                                <UserMinus className="mr-2 h-4 w-4" /> Remove a Student
                            </Button>
                            <Button variant="outline" className="w-full justify-start" onClick={handleSaveAnyway}>
                                <Save className="mr-2 h-4 w-4" /> Save Records Anyway
                            </Button>
                        </div>
                    )}

                    {verifyResult?.is_match && (
                        <DialogFooter>
                            <Button onClick={() => setIsVerifyDialogOpen(false)}>Done</Button>
                        </DialogFooter>
                    )}
                </DialogContent>
            </Dialog>

            <Dialog open={isRemoveDialogOpen} onOpenChange={setIsRemoveDialogOpen}>
                <DialogContent className="max-w-md">
                    <DialogHeader>
                        <DialogTitle>Remove a Student</DialogTitle>
                        <DialogDescription>Select the student whose attendance record should be removed.</DialogDescription>
                    </DialogHeader>
                    <div className="max-h-60 overflow-y-auto space-y-1">
                        {verifyResult?.records.map((record) => (
                            <div
                                key={record.id}
                                className={`flex items-center gap-3 p-2 rounded-md cursor-pointer transition-colors ${
                                    selectedRecordId === record.id ? 'bg-red-50 border border-red-200' : 'hover:bg-gray-50 border border-transparent'
                                }`}
                                onClick={() => setSelectedRecordId(record.id)}
                            >
                                <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                                    selectedRecordId === record.id ? 'border-red-500' : 'border-gray-300'
                                }`}>
                                    {selectedRecordId === record.id && <div className="w-2 h-2 rounded-full bg-red-500" />}
                                </div>
                                <div>
                                    <div className="text-sm font-medium">{record.student?.name}</div>
                                    <div className="text-xs text-muted-foreground">ID: {record.student?.digital_id}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                    <DialogFooter className="gap-2">
                        <Button variant="outline" onClick={() => { setIsRemoveDialogOpen(false); setSelectedRecordId(null); }}>Cancel</Button>
                        <Button variant="destructive" onClick={handleRemoveStudent} disabled={!selectedRecordId}>Remove</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div >
    );
}