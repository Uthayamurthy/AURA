import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface DailyStats {
    date: string;
    attendance_rate: number;
}

export function AttendanceChart({ data }: { data: DailyStats[] }) {
    return (
        <Card className="col-span-4">
            <CardHeader>
                <CardTitle>Attendance Trend (Last 7 Days)</CardTitle>
            </CardHeader>
            <CardContent className="pl-2">
                <ResponsiveContainer width="100%" height={350}>
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis
                            dataKey="date"
                            className="text-xs font-bold"
                            tick={{ fontSize: 12 }}
                            tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { weekday: 'short' })}
                        />
                        <YAxis
                            className="text-xs font-bold"
                            domain={[0, 100]}
                            tickFormatter={(value) => `${value}%`}
                        />
                        <Tooltip
                            contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0' }}
                            formatter={(value: number) => [`${value.toFixed(1)}%`, 'Attendance Rate']}
                            labelFormatter={(label) => new Date(label).toLocaleDateString()}
                        />
                        <Line
                            type="monotone"
                            dataKey="attendance_rate"
                            stroke="#2563eb"
                            strokeWidth={2}
                            dot={false}
                            activeDot={{ r: 6 }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
}
