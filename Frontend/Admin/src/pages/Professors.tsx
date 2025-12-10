import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Plus } from 'lucide-react';

interface Professor {
    id: number;
    name: string;
    email: string;
    department: string;
}

export default function Professors() {
    const { data: professors = [], isLoading } = useQuery<Professor[]>({
        queryKey: ['professors'],
        queryFn: async () => {
            const res = await api.get('/admin/professors');
            return res.data;
        }
    });

    return (
        <div className="flex-1 space-y-4 p-8 pt-6">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">Professors Management</h2>
                <Button>
                    <Plus className="mr-2 h-4 w-4" /> Add Professor
                </Button>
            </div>

            <div className="rounded-md border">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>ID</TableHead>
                            <TableHead>Name</TableHead>
                            <TableHead>Email</TableHead>
                            <TableHead>Department</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {isLoading ? (
                            <TableRow>
                                <TableCell colSpan={4} className="text-center">Loading...</TableCell>
                            </TableRow>
                        ) : professors.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={4} className="text-center">No professors found.</TableCell>
                            </TableRow>
                        ) : (
                            professors.map((prof) => (
                                <TableRow key={prof.id}>
                                    <TableCell>{prof.id}</TableCell>
                                    <TableCell className="font-medium">{prof.name}</TableCell>
                                    <TableCell>{prof.email}</TableCell>
                                    <TableCell>{prof.department}</TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </div>
        </div>
    );
}
