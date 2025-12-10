import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { StatsCards } from '@/components/Dashboard/StatsCards';
import { AttendanceChart } from '@/components/Dashboard/AttendanceChart';

export default function Dashboard() {
    const { data, isLoading, error } = useQuery({
        queryKey: ['adminStats'],
        queryFn: async () => {
            // Return type matches DashboardStats schema
            const res = await api.get('/admin/stats');
            return res.data;
        }
    });

    if (isLoading) return <div className="p-8">Loading stats...</div>;
    if (error) return <div className="p-8 text-red-500">Error loading stats: {(error as any).message}</div>;

    return (
        <div className="flex-1 space-y-4 p-8 pt-6">
            <div className="flex items-center justify-between space-y-2">
                <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
            </div>

            <StatsCards stats={data} />

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                <div className="col-span-7">
                    <AttendanceChart data={data.weekly_trend} />
                </div>
            </div>
        </div>
    );
}
