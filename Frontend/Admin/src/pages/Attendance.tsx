import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Download } from 'lucide-react';
import { format } from 'date-fns';

export default function Attendance() {
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [classGroupId, setClassGroupId] = useState('all');

    // Fetch Classes for filter
    const { data: classes } = useQuery({
        queryKey: ['classes'],
        queryFn: async () => {
            const res = await api.get('/admin/classes');
            return res.data;
        }
    });

    // Fetch Attendance Records
    const { data: records, isLoading } = useQuery({
        queryKey: ['attendance', startDate, endDate, classGroupId],
        queryFn: async () => {
            const params: any = {};
            if (startDate) params.start_date = startDate;
            if (endDate) params.end_date = endDate;
            if (classGroupId !== 'all') params.class_group_id = classGroupId;

            const res = await api.get('/admin/attendance/records', { params });
            return res.data;
        }
    });

    const handleExport = async () => {
        try {
            const params: any = {};
            if (startDate) params.start_date = startDate;
            if (endDate) params.end_date = endDate;
            if (classGroupId !== 'all') params.class_group_id = classGroupId;

            const response = await api.get('/admin/attendance/export', {
                params,
                responseType: 'blob'
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `attendance_export_${format(new Date(), 'yyyyMMdd')}.csv`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (error) {
            console.error('Export failed:', error);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold tracking-tight">Attendance Records</h1>
                <Button onClick={handleExport} className="gap-2">
                    <Download className="h-4 w-4" />
                    Export CSV
                </Button>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Filters</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-wrap gap-4">
                    <div className="space-y-2">
                        <label className="text-sm font-medium">Start Date</label>
                        <Input
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            className="w-[200px]"
                        />
                    </div>
                    <div className="space-y-2">
                        <label className="text-sm font-medium">End Date</label>
                        <Input
                            type="date"
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                            className="w-[200px]"
                        />
                    </div>
                    <div className="space-y-2">
                        <label className="text-sm font-medium">Class</label>
                        <Select value={classGroupId} onValueChange={setClassGroupId}>
                            <SelectTrigger className="w-[200px]">
                                <SelectValue placeholder="All Classes" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All Classes</SelectItem>
                                {classes?.map((c: any) => (
                                    <SelectItem key={c.id} value={String(c.id)}>{c.name}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardContent className="p-0">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Date</TableHead>
                                <TableHead>Time</TableHead>
                                <TableHead>Student</TableHead>
                                <TableHead>Digital ID</TableHead>
                                {/* <TableHead>Class</TableHead> We'd need to fetch class name for each record or have it in record, currently record has student which has class_group_id but not name directly unless properly joined/populated in schema. Use student.department or something? Or maybe student.class_group if populated */}
                                <TableHead>Status</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {isLoading ? (
                                <TableRow>
                                    <TableCell colSpan={5} className="text-center py-8">Loading...</TableCell>
                                </TableRow>
                            ) : records?.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={5} className="text-center py-8">No records found</TableCell>
                                </TableRow>
                            ) : (
                                records?.map((record: any) => (
                                    <TableRow key={record.id}>
                                        <TableCell>{format(new Date(record.timestamp), 'MMM dd, yyyy')}</TableCell>
                                        <TableCell>{format(new Date(record.timestamp), 'hh:mm a')}</TableCell>
                                        <TableCell className="font-medium">{record.student?.name || 'Unknown'}</TableCell>
                                        <TableCell>{record.student?.digital_id || '-'}</TableCell>
                                        <TableCell>
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${record.status === 'PRESENT' ? 'bg-green-100 text-green-800' :
                                                record.status === 'LATE' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                                                }`}>
                                                {record.status}
                                            </span>
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}
