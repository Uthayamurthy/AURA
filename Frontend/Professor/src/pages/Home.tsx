import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Play, Users, Loader2, MapPin } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

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

interface ActiveSession {
    id: number;
    current_code: string | null;
    start_time: string;
    end_time: string;
    assignment: TeachingAssignment;
}

export default function Home() {
    const navigate = useNavigate();
    const [assignments, setAssignments] = useState<TeachingAssignment[]>([]);
    const [activeSession, setActiveSession] = useState<ActiveSession | null>(null);
    const [selectedAssignmentId, setSelectedAssignmentId] = useState<string>("");
    const [duration, setDuration] = useState("5");
    const [isStartDialogOpen, setIsStartDialogOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    // Initial Load
    useEffect(() => {
        fetchData();
    }, []);

    // POLLING: Refresh active session every 2 seconds to check for CODE
    useEffect(() => {
        let interval: any;
        if (activeSession) {
            interval = setInterval(refreshSessionStatus, 2000);
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
            if (running) setActiveSession(running);
        } catch (error) {
            console.error("Failed to fetch data", error);
        } finally {
            setIsLoading(false);
        }
    };

    const refreshSessionStatus = async () => {
        // Just fetch history silently to update the code
        try {
            const historyRes = await api.get('/professor/attendance/history');
            const running = historyRes.data.find((s: any) => s.is_active);
            if (running) {
                setActiveSession(running); // Updates code if it changed
            } else if (activeSession) {
                setActiveSession(null); // Session ended remotely?
            }
        } catch (e) { console.error(e); }
    };

    const handleStartSession = async () => {
        if (!selectedAssignmentId) return;
        const assignment = assignments.find(a => a.id.toString() === selectedAssignmentId);
        if (!assignment) return;

        const roomToSend = assignment.default_classroom || "49";

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
            alert("Failed to start session");
        }
    };

    const handleStopSession = async () => {
        if (!activeSession) return;
        try {
            await api.post(`/professor/attendance/stop/${activeSession.id}`);
            setActiveSession(null);
        } catch (error) {
            alert("Failed to stop session");
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
                    <Button variant="destructive" onClick={handleStopSession}>Stop Current Session</Button>
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
                                <div className="text-xs text-green-600 mt-1">Beacon Active</div>
                            </div>
                        </div>
                    </CardHeader>
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
                                    <span> Room: LH{assign.default_classroom || "N/A"}</span>
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
        </div>
    );
}