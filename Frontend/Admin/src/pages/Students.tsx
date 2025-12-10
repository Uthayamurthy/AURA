import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Upload, Pencil, Trash2 } from 'lucide-react';

export default function Students() {
    const queryClient = useQueryClient();
    const [selectedClassId, setSelectedClassId] = useState<string>('all');
    
    // Dialog States
    const [isAddOpen, setIsAddOpen] = useState(false);
    const [isEditOpen, setIsEditOpen] = useState(false);
    const [isUploadOpen, setIsUploadOpen] = useState(false);

    // Form Data
    const [formData, setFormData] = useState({ id: '', digital_id: '', name: '', email: '', year: '', department: '', class_group_id: '' });
    const [editData, setEditData] = useState<any>({});
    const [file, setFile] = useState<File | null>(null);

    // Fetch Classes
    const { data: classes = [] } = useQuery({ queryKey: ['classes'], queryFn: async () => (await api.get('/admin/classes')).data });

    // Fetch Students
    const { data: students = [], isLoading } = useQuery({
        queryKey: ['students', selectedClassId],
        queryFn: async () => {
            const params = selectedClassId !== 'all' ? { class_group_id: selectedClassId } : {};
            return (await api.get('/admin/students', { params })).data;
        }
    });

    // --- Mutations ---
    const createMutation = useMutation({
        mutationFn: async (data: any) => await api.post('/admin/students', data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['students'] });
            setIsAddOpen(false);
            setFormData({ id: '', digital_id: '', name: '', email: '', year: '', department: '', class_group_id: '' });
        }
    });

    const updateMutation = useMutation({
        mutationFn: async (data: any) => await api.put(`/admin/students/${data.id}`, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['students'] });
            setIsEditOpen(false);
        }
    });

    const deleteMutation = useMutation({
        mutationFn: async (id: number) => await api.delete(`/admin/students/${id}`),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['students'] })
    });

    const uploadMutation = useMutation({
        mutationFn: async () => {
            if (!file) return;
            const form = new FormData();
            form.append('file', file);
            await api.post('/admin/students/bulk_upload', form, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['students'] });
            setIsUploadOpen(false);
            setFile(null);
            alert("Upload successful");
        }
    });

    const handleEdit = (student: any) => {
        setEditData({ ...student, password: '', device_id: student.device_id || '' });
        setIsEditOpen(true);
    };

    return (
        <div className="flex-1 space-y-4 p-8 pt-6">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">Students Management</h2>
                <div className="flex gap-2">
                    <Select value={selectedClassId} onValueChange={setSelectedClassId}>
                        <SelectTrigger className="w-[180px]"><SelectValue placeholder="Filter by Class" /></SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">All Classes</SelectItem>
                            {classes.map((c: any) => <SelectItem key={c.id} value={c.id.toString()}>{c.name}</SelectItem>)}
                        </SelectContent>
                    </Select>

                    <Dialog open={isUploadOpen} onOpenChange={setIsUploadOpen}>
                        <DialogTrigger asChild><Button variant="outline"><Upload className="mr-2 h-4 w-4" /> Bulk Upload</Button></DialogTrigger>
                        <DialogContent>
                            <DialogHeader><DialogTitle>Upload Students (CSV)</DialogTitle></DialogHeader>
                            <div className="py-4 space-y-2">
                                <p className="text-sm text-gray-500">Cols: ID(13), DigID(7), Name, Email, Year, Dept, ClassName, Pass</p>
                                <Input type="file" accept=".csv" onChange={(e) => setFile(e.target.files?.[0] || null)} />
                            </div>
                            <DialogFooter><Button onClick={() => uploadMutation.mutate()} disabled={!file || uploadMutation.isPending}>Upload</Button></DialogFooter>
                        </DialogContent>
                    </Dialog>

                    <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
                        <DialogTrigger asChild><Button><Plus className="mr-2 h-4 w-4" /> Add Student</Button></DialogTrigger>
                        <DialogContent className="max-h-[80vh] overflow-y-auto">
                            <DialogHeader><DialogTitle>Add Student</DialogTitle></DialogHeader>
                            <div className="grid gap-4 py-4">
                                <Input placeholder="Student ID (13 digit)" value={formData.id} onChange={e => setFormData({...formData, id: e.target.value})} />
                                <Input placeholder="Digital ID (7 digit)" value={formData.digital_id} onChange={e => setFormData({...formData, digital_id: e.target.value})} />
                                <Input placeholder="Name" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
                                <Input placeholder="Email" type="email" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} />
                                <div className="grid grid-cols-2 gap-2">
                                    <Input placeholder="Year" type="number" value={formData.year} onChange={e => setFormData({...formData, year: e.target.value})} />
                                    <Input placeholder="Department" value={formData.department} onChange={e => setFormData({...formData, department: e.target.value})} />
                                </div>
                                <div className="space-y-1">
                                    <Label>Class Group</Label>
                                    <Select value={formData.class_group_id} onValueChange={v => setFormData({...formData, class_group_id: v})}>
                                        <SelectTrigger><SelectValue placeholder="Select Class" /></SelectTrigger>
                                        <SelectContent>
                                            {classes.map((c: any) => <SelectItem key={c.id} value={c.id.toString()}>{c.name}</SelectItem>)}
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>
                            <DialogFooter><Button onClick={() => createMutation.mutate(formData)}>Create</Button></DialogFooter>
                        </DialogContent>
                    </Dialog>
                </div>
            </div>

            <div className="rounded-md border">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>ID</TableHead>
                            <TableHead>Name</TableHead>
                            <TableHead>Email</TableHead>
                            <TableHead>Class</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {isLoading ? <TableRow><TableCell colSpan={5}>Loading...</TableCell></TableRow> :
                            students.map((student: any) => (
                                <TableRow key={student.id}>
                                    <TableCell>{student.id}</TableCell>
                                    <TableCell className="font-medium">{student.name}</TableCell>
                                    <TableCell>{student.email}</TableCell>
                                    <TableCell>{classes.find((c: any) => c.id === student.class_group_id)?.name || '-'}</TableCell>
                                    <TableCell className="text-right">
                                        <Button variant="ghost" size="icon" onClick={() => handleEdit(student)}><Pencil className="h-4 w-4" /></Button>
                                        <Button variant="ghost" size="icon" className="text-red-500" onClick={() => deleteMutation.mutate(student.id)}><Trash2 className="h-4 w-4" /></Button>
                                    </TableCell>
                                </TableRow>
                            ))
                        }
                    </TableBody>
                </Table>
            </div>

            {/* Edit Dialog */}
            <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
                <DialogContent>
                    <DialogHeader><DialogTitle>Edit Student</DialogTitle></DialogHeader>
                    <div className="grid gap-4 py-4">
                        <Input placeholder="Name" value={editData.name} onChange={e => setEditData({...editData, name: e.target.value})} />
                        <Input placeholder="Email" value={editData.email} onChange={e => setEditData({...editData, email: e.target.value})} />
                        
                        <div className="space-y-1">
                            <Label>Class Group</Label>
                            <Select value={editData.class_group_id?.toString()} onValueChange={v => setEditData({...editData, class_group_id: parseInt(v)})}>
                                <SelectTrigger><SelectValue placeholder="Select Class" /></SelectTrigger>
                                <SelectContent>
                                    {classes.map((c: any) => <SelectItem key={c.id} value={c.id.toString()}>{c.name}</SelectItem>)}
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-1">
                            <Label>New Password (Optional)</Label>
                            <Input placeholder="Leave blank to keep current" type="password" value={editData.password} onChange={e => setEditData({...editData, password: e.target.value})} />
                        </div>

                        <div className="space-y-1">
                            <Label>Device ID (UUID)</Label>
                            <div className="flex gap-2">
                                <Input value={editData.device_id || ''} disabled placeholder="Not registered" />
                                <Button variant="outline" size="sm" onClick={() => setEditData({...editData, device_id: ""})}>Reset</Button>
                            </div>
                            <p className="text-xs text-gray-500">Clear this to allow student to register a new phone.</p>
                        </div>
                    </div>
                    <DialogFooter><Button onClick={() => updateMutation.mutate(editData)}>Update</Button></DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}