import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Plus, Upload, Pencil, Trash2 } from 'lucide-react';

interface Professor {
    id: number;
    name: string;
    email: string;
    department: string;
}

export default function Professors() {
    const queryClient = useQueryClient();
    const [isAddOpen, setIsAddOpen] = useState(false);
    const [isEditOpen, setIsEditOpen] = useState(false);
    const [isUploadOpen, setIsUploadOpen] = useState(false);
    
    // Forms
    const [formData, setFormData] = useState({ id: '', name: '', email: '', department: '', password: '' });
    const [editData, setEditData] = useState<any>({});
    const [file, setFile] = useState<File | null>(null);

    // Fetch
    const { data: professors = [], isLoading } = useQuery<Professor[]>({
        queryKey: ['professors'],
        queryFn: async () => (await api.get('/admin/professors')).data
    });

    // Create
    const createMutation = useMutation({
        mutationFn: async (data: any) => await api.post('/admin/professors', data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['professors'] });
            setIsAddOpen(false);
            setFormData({ id: '', name: '', email: '', department: '', password: '' });
        }
    });

    // Update
    const updateMutation = useMutation({
        mutationFn: async (data: any) => await api.put(`/admin/professors/${data.id}`, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['professors'] });
            setIsEditOpen(false);
        }
    });

    // Delete
    const deleteMutation = useMutation({
        mutationFn: async (id: number) => await api.delete(`/admin/professors/${id}`),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['professors'] })
    });

    // Bulk Upload
    const uploadMutation = useMutation({
        mutationFn: async () => {
            if (!file) return;
            const form = new FormData();
            form.append('file', file);
            await api.post('/admin/professors/bulk_upload', form, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['professors'] });
            setIsUploadOpen(false);
            setFile(null);
            alert("Upload successful");
        }
    });

    const handleEdit = (prof: Professor) => {
        setEditData({ ...prof, password: '' }); // Don't show old hash, allow setting new
        setIsEditOpen(true);
    };

    return (
        <div className="flex-1 space-y-4 p-8 pt-6">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">Professors Management</h2>
                <div className="flex gap-2">
                    <Dialog open={isUploadOpen} onOpenChange={setIsUploadOpen}>
                        <DialogTrigger asChild><Button variant="outline"><Upload className="mr-2 h-4 w-4" /> Bulk Upload</Button></DialogTrigger>
                        <DialogContent>
                            <DialogHeader><DialogTitle>Upload Professors (CSV)</DialogTitle></DialogHeader>
                            <div className="py-4 space-y-2">
                                <p className="text-sm text-gray-500">CSV Columns: ID, Name, Email, Dept, Password</p>
                                <Input type="file" accept=".csv" onChange={(e) => setFile(e.target.files?.[0] || null)} />
                            </div>
                            <DialogFooter><Button onClick={() => uploadMutation.mutate()} disabled={!file || uploadMutation.isPending}>Upload</Button></DialogFooter>
                        </DialogContent>
                    </Dialog>

                    <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
                        <DialogTrigger asChild><Button><Plus className="mr-2 h-4 w-4" /> Add Professor</Button></DialogTrigger>
                        <DialogContent>
                            <DialogHeader><DialogTitle>Add Professor</DialogTitle></DialogHeader>
                            <div className="grid gap-4 py-4">
                                <Input placeholder="ID (6 digit)" value={formData.id} onChange={e => setFormData({...formData, id: e.target.value})} />
                                <Input placeholder="Name" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
                                <Input placeholder="Email" type="email" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} />
                                <Input placeholder="Department" value={formData.department} onChange={e => setFormData({...formData, department: e.target.value})} />
                                <Input placeholder="Password" type="password" value={formData.password} onChange={e => setFormData({...formData, password: e.target.value})} />
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
                            <TableHead>Department</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {isLoading ? <TableRow><TableCell colSpan={5}>Loading...</TableCell></TableRow> :
                            professors.map((prof) => (
                                <TableRow key={prof.id}>
                                    <TableCell>{prof.id}</TableCell>
                                    <TableCell className="font-medium">{prof.name}</TableCell>
                                    <TableCell>{prof.email}</TableCell>
                                    <TableCell>{prof.department}</TableCell>
                                    <TableCell className="text-right">
                                        <Button variant="ghost" size="icon" onClick={() => handleEdit(prof)}><Pencil className="h-4 w-4" /></Button>
                                        <Button variant="ghost" size="icon" className="text-red-500" onClick={() => deleteMutation.mutate(prof.id)}><Trash2 className="h-4 w-4" /></Button>
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
                    <DialogHeader><DialogTitle>Edit Professor</DialogTitle></DialogHeader>
                    <div className="grid gap-4 py-4">
                        <Input placeholder="Name" value={editData.name} onChange={e => setEditData({...editData, name: e.target.value})} />
                        <Input placeholder="Email" value={editData.email} onChange={e => setEditData({...editData, email: e.target.value})} />
                        <Input placeholder="Department" value={editData.department} onChange={e => setEditData({...editData, department: e.target.value})} />
                        <div className="space-y-1">
                            <Label>New Password (Optional)</Label>
                            <Input placeholder="Leave blank to keep current" type="password" value={editData.password} onChange={e => setEditData({...editData, password: e.target.value})} />
                        </div>
                    </div>
                    <DialogFooter><Button onClick={() => updateMutation.mutate(editData)}>Update</Button></DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}