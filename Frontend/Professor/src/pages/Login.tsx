import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { useNavigate } from 'react-router-dom';
import { Settings } from 'lucide-react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"

export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const { login } = useAuth();
    const navigate = useNavigate();

    // Settings for IP/Server URL
    const [serverUrl, setServerUrl] = useState(localStorage.getItem('aura_server_url') || '');
    const [dialogOpen, setDialogOpen] = useState(false);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const formData = new FormData();
            formData.append('username', email); // OAuth2 expects 'username'
            formData.append('password', password);

            const response = await api.post('/login/access-token', formData);
            const { access_token } = response.data;

            // We need to parse user info or fetch "me". 
            // For now, let's just construct a user object since the token is valid.
            // Ideally we call /me endpoint. The backend doesn't have /me for prof yet?
            // Wait, let's check backend. 'deps.get_current_active_professor' works.
            // But we don't have a direct /me endpoint. We can use /my-courses to verify or just assume login worked.

            const user = { id: 0, email, role: 'professor' as const }; // Placeholder ID

            login(access_token, user);
            navigate('/');
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Login failed. Check server URL or credentials.');
        } finally {
            setLoading(false);
        }
    };

    const saveSettings = () => {
        localStorage.setItem('aura_server_url', serverUrl);
        // Force reload to apply API base URL change
        window.location.reload();
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900 p-4">
            <Card className="w-full max-w-md">
                <CardHeader className="space-y-1">
                    <div className="flex justify-between items-center">
                        <CardTitle className="text-2xl font-bold">AURA Professor</CardTitle>
                        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                            <DialogTrigger asChild>
                                <Button variant="ghost" size="icon">
                                    <Settings className="h-5 w-5" />
                                </Button>
                            </DialogTrigger>
                            <DialogContent>
                                <DialogHeader>
                                    <DialogTitle>Server Settings</DialogTitle>
                                    <DialogDescription>
                                        Configure the Backend Server URL (e.g., http://192.168.1.100:8000)
                                    </DialogDescription>
                                </DialogHeader>
                                <div className="grid gap-4 py-4">
                                    <div className="grid grid-cols-4 items-center gap-4">
                                        <Label htmlFor="url" className="text-right">URL</Label>
                                        <Input id="url" value={serverUrl} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setServerUrl(e.target.value)} className="col-span-3" placeholder="/api" />
                                    </div>
                                </div>
                                <Button onClick={saveSettings}>Save & Reload</Button>
                            </DialogContent>
                        </Dialog>
                    </div>
                    <CardDescription>Enter your credentials to access the portal</CardDescription>
                </CardHeader>
                <form onSubmit={handleLogin}>
                    <CardContent className="space-y-4">
                        {error && <div className="text-red-500 text-sm">{error}</div>}
                        <div className="space-y-2">
                            <Label htmlFor="email">Email</Label>
                            <Input id="email" type="email" placeholder="prof@aura.com" required value={email} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)} />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="password">Password</Label>
                            <Input id="password" type="password" required value={password} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)} />
                        </div>
                    </CardContent>
                    <CardFooter>
                        <Button type="submit" className="w-full" disabled={loading}>
                            {loading ? 'Logging in...' : 'Login'}
                        </Button>
                    </CardFooter>
                </form>
            </Card>
        </div>
    );
}
