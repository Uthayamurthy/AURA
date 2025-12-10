import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Plus } from 'lucide-react';

interface ClassGroup {
    id: number;
    name: string;
    department: string;
    year: number;
}

interface Student {
    id: number;
    name: string;
    digital_id: number;
    email: string;
    department: string;
    year: number;
    class_group_id: number;
}

export default function Students() {
    const [selectedDept, setSelectedDept] = useState<string>('all');
    const [selectedYear, setSelectedYear] = useState<string>('all');
    const [selectedClassId, setSelectedClassId] = useState<string>('all');

    // Fetch Classes
    const { data: classes = [] } = useQuery<ClassGroup[]>({
        queryKey: ['classes'],
        queryFn: async () => {
            const res = await api.get('/admin/classes');
            return res.data;
        }
    });

    // Derived filters
    const departments = useMemo(() => Array.from(new Set(classes.map(c => c.department))).filter(Boolean), [classes]);
    const years = useMemo(() => Array.from(new Set(classes.map(c => c.year))).filter(Boolean).sort(), [classes]);

    // Filtered Classes for Section dropdown
    const filteredClasses = useMemo(() => {
        return classes.filter(c => {
            if (selectedDept !== 'all' && c.department !== selectedDept) return false;
            if (selectedYear !== 'all' && c.year.toString() !== selectedYear) return false;
            return true;
        });
    }, [classes, selectedDept, selectedYear]);

    // Fetch Students
    // If 'all' classes is selected, we fetch all students? Or force selection?
    // Server supports ?class_group_id=... 
    // If 'all', backend might return all if param omitted.
    const { data: students = [], isLoading } = useQuery<Student[]>({
        queryKey: ['students', selectedClassId],
        queryFn: async () => {
            const params = selectedClassId !== 'all' ? { class_group_id: selectedClassId } : {};
            const res = await api.get('/admin/students', { params });
            return res.data;
        }
    });

    return (
        <div className="flex-1 space-y-4 p-8 pt-6">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">Students Management</h2>
                <Button>
                    <Plus className="mr-2 h-4 w-4" /> Add Student
                </Button>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Filters</CardTitle>
                </CardHeader>
                <CardContent className="flex gap-4">
                    <Select value={selectedDept} onValueChange={setSelectedDept}>
                        <SelectTrigger className="w-[180px]">
                            <SelectValue placeholder="Department" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">All Departments</SelectItem>
                            {departments.map(d => <SelectItem key={d} value={d}>{d}</SelectItem>)}
                        </SelectContent>
                    </Select>

                    <Select value={selectedYear} onValueChange={setSelectedYear}>
                        <SelectTrigger className="w-[180px]">
                            <SelectValue placeholder="Year" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">All Years</SelectItem>
                            {years.map(y => <SelectItem key={y} value={y?.toString()!}>Year {y}</SelectItem>)}
                        </SelectContent>
                    </Select>

                    <Select value={selectedClassId} onValueChange={setSelectedClassId}>
                        <SelectTrigger className="w-[180px]">
                            <SelectValue placeholder="Section / Class" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">All Classes</SelectItem>
                            {filteredClasses.map(c => <SelectItem key={c.id} value={c.id.toString()}>{c.name}</SelectItem>)}
                        </SelectContent>
                    </Select>
                </CardContent>
            </Card>

            <div className="rounded-md border">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>ID</TableHead>
                            <TableHead>Digital ID</TableHead>
                            <TableHead>Name</TableHead>
                            <TableHead>Email</TableHead>
                            <TableHead>Department</TableHead>
                            <TableHead>Year</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {isLoading ? (
                            <TableRow>
                                <TableCell colSpan={6} className="text-center">Loading...</TableCell>
                            </TableRow>
                        ) : students.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={6} className="text-center">No students found.</TableCell>
                            </TableRow>
                        ) : (
                            students.map((student) => (
                                <TableRow key={student.id}>
                                    <TableCell>{student.id}</TableCell>
                                    <TableCell>{student.digital_id}</TableCell>
                                    <TableCell className="font-medium">{student.name}</TableCell>
                                    <TableCell>{student.email}</TableCell>
                                    <TableCell>{student.department}</TableCell>
                                    <TableCell>{student.year}</TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </div>
        </div>
    );
}
