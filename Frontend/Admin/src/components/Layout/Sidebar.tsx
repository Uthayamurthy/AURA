import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { LayoutDashboard, Users, GraduationCap, LogOut, BookOpen, CalendarRange } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function Sidebar() {
    const location = useLocation();

    const handleLogout = () => {
        localStorage.removeItem('token');
        window.location.href = '/login';
    };

    const navItems = [
        { name: 'Dashboard', path: '/', icon: LayoutDashboard },
        { name: 'Students', path: '/students', icon: Users },
        { name: 'Professors', path: '/professors', icon: GraduationCap },
        { name: 'Courses', path: '/courses', icon: BookOpen },
        { name: 'Timetable', path: '/timetable', icon: CalendarRange },
    ];

    return (
        <div className="flex flex-col h-screen w-64 bg-zinc-900 text-white border-r">
            <div className="p-6">
                <h1 className="text-2xl font-bold">AURA Admin</h1>
            </div>
            <nav className="flex-1 px-4 space-y-2">
                {navItems.map((item) => (
                    <Link
                        key={item.path}
                        to={item.path}
                        className={cn(
                            "flex items-center gap-3 px-4 py-3 rounded-lg transition-colors",
                            location.pathname === item.path
                                ? "bg-primary text-primary-foreground"
                                : "hover:bg-zinc-800"
                        )}
                    >
                        <item.icon className="h-5 w-5" />
                        {item.name}
                    </Link>
                ))}
            </nav>
            <div className="p-4 border-t border-zinc-800">
                <Button
                    variant="ghost"
                    className="w-full justify-start gap-3 hover:bg-red-900/20 hover:text-red-500"
                    onClick={handleLogout}
                >
                    <LogOut className="h-5 w-5" />
                    Logout
                </Button>
            </div>
        </div>
    );
}