import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Settings } from 'lucide-react';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

interface BellSlot {
    slot_number: number;
    start_time: string;
    end_time: string;
}

export default function Timetable() {
    const queryClient = useQueryClient();
    const [selectedClass, setSelectedClass] = useState<string>('');
    const [selectedCell, setSelectedCell] = useState<{ day: number, slot: number } | null>(null);
    const [isAssignOpen, setIsAssignOpen] = useState(false);
    const [isBellOpen, setIsBellOpen] = useState(false);

    // --- State for Assignment Dialog ---
    const [assignForm, setAssignForm] = useState({ courseId: '', profId: '' });

    // --- State for Bell Schedule Editing ---
    const [tempSchedule, setTempSchedule] = useState<BellSlot[]>([]);

    // --- Fetch Data ---
    const { data: classes = [] } = useQuery({ queryKey: ['classes'], queryFn: async () => (await api.get('/admin/classes')).data });
    const { data: courses = [] } = useQuery({ queryKey: ['courses'], queryFn: async () => (await api.get('/admin/courses')).data });
    const { data: professors = [] } = useQuery({ queryKey: ['professors'], queryFn: async () => (await api.get('/admin/professors')).data });
    const { data: bellSchedule = [] } = useQuery({ 
        queryKey: ['bellSchedule'], 
        queryFn: async () => (await api.get('/admin/bell-schedule')).data 
    });
    
    // Fetch Timetable Grid for selected class
    const { data: timetableEntries = [] } = useQuery({
        queryKey: ['timetable', selectedClass],
        queryFn: async () => selectedClass ? (await api.get(`/admin/timetable/${selectedClass}`)).data : [],
        enabled: !!selectedClass
    });

    // Sync bell schedule to temp state when dialog opens
    useEffect(() => {
        if (isBellOpen && bellSchedule.length > 0) {
            // Deep copy to avoid mutating cache directly
            setTempSchedule(JSON.parse(JSON.stringify(bellSchedule)));
        }
    }, [isBellOpen, bellSchedule]);

    // --- Mutations ---
    const assignMutation = useMutation({
        mutationFn: async () => {
            // 1. Create/Get Teaching Assignment
            const assignRes = await api.post('/admin/assignments', {
                course_id: parseInt(assignForm.courseId),
                professor_id: parseInt(assignForm.profId),
                class_group_id: parseInt(selectedClass)
            });
            // 2. Assign to Slot
            await api.post('/admin/timetable/slot', {
                assignment_id: assignRes.data.id,
                day_of_week: selectedCell?.day,
                hour_slot: selectedCell?.slot
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['timetable'] });
            setIsAssignOpen(false);
            setAssignForm({ courseId: '', profId: '' });
        }
    });

    const deleteSlotMutation = useMutation({
        mutationFn: async () => {
            if (!selectedCell || !selectedClass) return;
            await api.delete(`/admin/timetable/slot?class_group_id=${selectedClass}&day_of_week=${selectedCell.day}&hour_slot=${selectedCell.slot}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['timetable'] });
            setIsAssignOpen(false);
        }
    });

    const updateBellScheduleMutation = useMutation({
        mutationFn: async () => {
            // Backend expects a list of {slot_number, start_time, end_time}
            // Ensure format corresponds to backend expectations (HH:MM:SS)
            // Input type="time" returns HH:MM, backend Pydantic usually handles adding :00 if needed, but let's be safe.
            const payload = tempSchedule.map(s => ({
                slot_number: s.slot_number,
                start_time: s.start_time.length === 5 ? s.start_time + ":00" : s.start_time,
                end_time: s.end_time.length === 5 ? s.end_time + ":00" : s.end_time
            }));
            await api.put('/admin/bell-schedule', payload);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['bellSchedule'] });
            setIsBellOpen(false);
        }
    });

    // --- Helpers ---
    const handleBellChange = (index: number, field: 'start_time' | 'end_time', value: string) => {
        const newSched = [...tempSchedule];
        newSched[index] = { ...newSched[index], [field]: value };
        setTempSchedule(newSched);
    };

    const getSlotContent = (dayIdx: number, slotNum: number) => {
        const entry = timetableEntries.find((t: any) => t.day_of_week === dayIdx && t.hour_slot === slotNum);
        if (!entry) return null;
        
        return (
            <div className="text-xs">
                <div className="font-bold truncate">{entry.assignment?.course?.name || "Course " + entry.assignment?.course_id}</div>
                <div className="text-gray-500 truncate">{entry.assignment?.professor?.name || "Prof " + entry.assignment?.professor_id}</div>
            </div>
        );
    };

    const handleCellClick = (day: number, slot: number) => {
        if (!selectedClass) return alert("Please select a class first");
        setSelectedCell({ day, slot });
        setIsAssignOpen(true);
    };

    return (
        <div className="flex-1 space-y-4 p-8 pt-6">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">Timetable Management</h2>
                <div className="flex items-center gap-2">
                    <Select value={selectedClass} onValueChange={setSelectedClass}>
                        <SelectTrigger className="w-[200px]">
                            <SelectValue placeholder="Select Class Group" />
                        </SelectTrigger>
                        <SelectContent>
                            {classes.map((c: any) => <SelectItem key={c.id} value={c.id.toString()}>{c.name}</SelectItem>)}
                        </SelectContent>
                    </Select>
                    <Button variant="outline" onClick={() => setIsBellOpen(true)}><Settings className="mr-2 h-4 w-4" /> Bell Schedule</Button>
                </div>
            </div>

            <Card className="overflow-x-auto">
                <CardContent className="p-0">
                    <div className="min-w-[800px]">
                        {/* Header Row (Slots) */}
                        <div className="flex border-b">
                            <div className="w-24 flex-shrink-0 p-4 font-bold bg-muted/50 border-r">Day / Time</div>
                            {bellSchedule.map((slot: any) => (
                                <div key={slot.slot_number} className="flex-1 p-2 text-center border-r last:border-r-0 min-w-[100px]">
                                    <div className="font-semibold">Period {slot.slot_number}</div>
                                    <div className="text-xs text-gray-500">
                                        {slot.start_time?.slice(0, 5)} - {slot.end_time?.slice(0, 5)}
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Grid Rows */}
                        {DAYS.map((day, dayIdx) => (
                            <div key={day} className="flex border-b last:border-b-0">
                                <div className="w-24 flex-shrink-0 p-4 font-medium bg-muted/20 border-r">{day}</div>
                                {bellSchedule.map((slot: any) => (
                                    <div 
                                        key={`${dayIdx}-${slot.slot_number}`} 
                                        className="flex-1 p-2 border-r last:border-r-0 min-w-[100px] h-24 cursor-pointer hover:bg-blue-50 transition-colors flex items-center justify-center text-center border-dashed border-gray-200"
                                        onClick={() => handleCellClick(dayIdx, slot.slot_number)}
                                    >
                                        {getSlotContent(dayIdx, slot.slot_number) || <span className="text-gray-300 text-sm">Empty</span>}
                                    </div>
                                ))}
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Assignment Dialog */}
            <Dialog open={isAssignOpen} onOpenChange={setIsAssignOpen}>
                <DialogContent>
                    <DialogHeader><DialogTitle>Edit Slot: {selectedCell && DAYS[selectedCell.day]} Period {selectedCell?.slot}</DialogTitle></DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>Course</Label>
                            <Select value={assignForm.courseId} onValueChange={v => setAssignForm({ ...assignForm, courseId: v })}>
                                <SelectTrigger><SelectValue placeholder="Select Course" /></SelectTrigger>
                                <SelectContent>
                                    {courses.map((c: any) => <SelectItem key={c.id} value={c.id.toString()}>{c.code}: {c.name}</SelectItem>)}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label>Professor</Label>
                            <Select value={assignForm.profId} onValueChange={v => setAssignForm({ ...assignForm, profId: v })}>
                                <SelectTrigger><SelectValue placeholder="Select Professor" /></SelectTrigger>
                                <SelectContent>
                                    {professors.map((p: any) => <SelectItem key={p.id} value={p.id.toString()}>{p.name}</SelectItem>)}
                                </SelectContent>
                            </Select>
                        </div>
                        <DialogFooter className="gap-2">
                            <Button variant="destructive" onClick={() => deleteSlotMutation.mutate()}>Clear Slot</Button>
                            <Button onClick={() => assignMutation.mutate()}>Save Assignment</Button>
                        </DialogFooter>
                    </div>
                </DialogContent>
            </Dialog>

            {/* Bell Schedule Dialog (Fully Editable) */}
            <Dialog open={isBellOpen} onOpenChange={setIsBellOpen}>
                <DialogContent className="max-w-xl">
                    <DialogHeader><DialogTitle>Bell Schedule Configuration</DialogTitle></DialogHeader>
                    <div className="py-4 space-y-4 max-h-[60vh] overflow-y-auto">
                       <p className="text-sm text-gray-500">Edit standard start/end times for all classes.</p>
                       
                       <div className="space-y-3">
                           {tempSchedule.map((s, idx) => (
                               <div key={s.slot_number} className="grid grid-cols-4 gap-4 items-center">
                                   <span className="font-medium col-span-1">Period {s.slot_number}</span>
                                   <Input 
                                        className="col-span-1"
                                        type="time" 
                                        value={s.start_time?.slice(0, 5)} 
                                        onChange={(e) => handleBellChange(idx, 'start_time', e.target.value)}
                                   />
                                   <span className="text-center">-</span>
                                   <Input 
                                        className="col-span-1"
                                        type="time" 
                                        value={s.end_time?.slice(0, 5)} 
                                        onChange={(e) => handleBellChange(idx, 'end_time', e.target.value)}
                                   />
                               </div>
                           ))}
                       </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setIsBellOpen(false)}>Cancel</Button>
                        <Button onClick={() => updateBellScheduleMutation.mutate()} disabled={updateBellScheduleMutation.isPending}>
                            {updateBellScheduleMutation.isPending ? 'Saving...' : 'Save Schedule'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}