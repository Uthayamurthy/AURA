import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Plus, Trash2, Pencil } from 'lucide-react';

export default function Courses() {
    const queryClient = useQueryClient();
    const [isAddOpen, setIsAddOpen] = useState(false);
    const [isEditOpen, setIsEditOpen] = useState(false);
    
    const [formData, setFormData] = useState({ code: '', name: '', department: '' });
    const [editData, setEditData] = useState<any>({});

    const { data: courses = [], isLoading } = useQuery({
        queryKey: ['courses'],
        queryFn: async () => (await api.get('/admin/courses')).data
    });

    const createMutation = useMutation({
        mutationFn: async (data: any) => await api.post('/admin/courses', data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['courses'] });
            setIsAddOpen(false);
            setFormData({ code: '', name: '', department: '' });
        }
    });

    const updateMutation = useMutation({
        mutationFn: async (data: any) => await api.put(`/admin/courses/${data.id}`, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['courses'] });
            setIsEditOpen(false);
        }
    });

    const deleteMutation = useMutation({
        mutationFn: async (id: number) => await api.delete(`/admin/courses/${id}`),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['courses'] })
    });

    const handleEdit = (course: any) => {
        setEditData(course);
        setIsEditOpen(true);
    };

    return (
        <div className="flex-1 space-y-4 p-8 pt-6">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">Course Catalog</h2>
                <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
                    <DialogTrigger asChild>
                        <Button><Plus className="mr-2 h-4 w-4" /> Add Course</Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader><DialogTitle>Add New Course</DialogTitle></DialogHeader>
                        <div className="space-y-4 py-4">
                            <div className="grid gap-2">
                                <Label>Course Code</Label>
                                <Input value={formData.code} onChange={e => setFormData({ ...formData, code: e.target.value })} placeholder="e.g. UCS1234" />
                            </div>
                            <div className="grid gap-2">
                                <Label>Course Name</Label>
                                <Input value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} placeholder="e.g. Data Structures" />
                            </div>
                            <div className="grid gap-2">
                                <Label>Department</Label>
                                <Input value={formData.department} onChange={e => setFormData({ ...formData, department: e.target.value })} placeholder="e.g. CSE" />
                            </div>
                            <Button onClick={() => createMutation.mutate(formData)} className="w-full">Create Course</Button>
                        </div>
                    </DialogContent>
                </Dialog>
            </div>

            <Card>
                <CardHeader><CardTitle>All Courses</CardTitle></CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Code</TableHead>
                                <TableHead>Name</TableHead>
                                <TableHead>Department</TableHead>
                                <TableHead className="text-right">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {isLoading ? <TableRow><TableCell colSpan={4}>Loading...</TableCell></TableRow> :
                                courses.map((course: any) => (
                                    <TableRow key={course.id}>
                                        <TableCell className="font-medium">{course.code}</TableCell>
                                        <TableCell>{course.name}</TableCell>
                                        <TableCell>{course.department}</TableCell>
                                        <TableCell className="text-right">
                                            <Button variant="ghost" size="icon" onClick={() => handleEdit(course)}><Pencil className="h-4 w-4" /></Button>
                                            <Button variant="ghost" size="icon" className="text-red-500" onClick={() => deleteMutation.mutate(course.id)}><Trash2 className="h-4 w-4" /></Button>
                                        </TableCell>
                                    </TableRow>
                                ))
                            }
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            {/* Edit Dialog */}
            <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
                <DialogContent>
                    <DialogHeader><DialogTitle>Edit Course</DialogTitle></DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="grid gap-2">
                            <Label>Course Code</Label>
                            <Input value={editData.code} onChange={e => setEditData({ ...editData, code: e.target.value })} />
                        </div>
                        <div className="grid gap-2">
                            <Label>Course Name</Label>
                            <Input value={editData.name} onChange={e => setEditData({ ...editData, name: e.target.value })} />
                        </div>
                        <div className="grid gap-2">
                            <Label>Department</Label>
                            <Input value={editData.department} onChange={e => setEditData({ ...editData, department: e.target.value })} />
                        </div>
                        <DialogFooter><Button onClick={() => updateMutation.mutate(editData)}>Update Course</Button></DialogFooter>
                    </div>
                </DialogContent>
            </Dialog>
        </div>
    );
}