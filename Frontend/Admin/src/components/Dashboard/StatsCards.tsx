import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, GraduationCap, BookOpen, Layers, Activity, CalendarCheck } from 'lucide-react';

interface Stats {
    total_students: number;
    total_professors: number;
    total_courses: number;
    total_classes: number;
    active_sessions: number;
    todays_attendance_rate: number;
}

export function StatsCards({ stats }: { stats: Stats }) {
    const cards = [
        { label: 'Students', value: stats.total_students, icon: Users, desc: 'Total enrolled' },
        { label: 'Professors', value: stats.total_professors, icon: GraduationCap, desc: 'Total registered' },
        { label: 'Courses', value: stats.total_courses, icon: BookOpen, desc: 'Active courses' },
        { label: 'Classes', value: stats.total_classes, icon: Layers, desc: 'Class groups' },
        { label: 'Active Sessions', value: stats.active_sessions, icon: Activity, desc: 'Currently running' },
        { label: "Today's Attendance", value: `${stats.todays_attendance_rate.toFixed(1)}%`, icon: CalendarCheck, desc: 'Average rate' },
    ];

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {cards.map((card) => (
                <Card key={card.label}>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">
                            {card.label}
                        </CardTitle>
                        <card.icon className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{card.value}</div>
                        <p className="text-xs text-muted-foreground">
                            {card.desc}
                        </p>
                    </CardContent>
                </Card>
            ))}
        </div>
    );
}
