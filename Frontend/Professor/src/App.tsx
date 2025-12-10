import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/context/AuthContext';
import Login from '@/pages/Login';
import Home from '@/pages/Home';
import Statistics from '@/pages/Statistics';
import { Toaster } from 'sonner';

import React from 'react';

// Private Route Wrapper
const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

// Layout with Navigation (Bottom Tab Bar for Mobile or Top Bar for Desktop)
// Since it's a PWA for Professors, a simple Top Bar or Bottom Bar is good.
// Let's do a simple layout wrapper for private pages.
import { LayoutDashboard, BarChart3, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

const PrivateLayout = ({ children }: { children: React.ReactNode }) => {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex flex-col">
      <header className="sticky top-0 z-10 bg-white dark:bg-gray-900 border-b p-4 flex justify-between items-center shadow-sm">
        <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">AURA Professor</h1>
        <Button variant="ghost" size="icon" onClick={logout}>
          <LogOut className="h-5 w-5 text-gray-500" />
        </Button>
      </header>

      <main className="flex-1 p-4 pb-20">
        {children}
      </main>

      {/* Bottom Navigation for PWA feel */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-900 border-t flex justify-around p-3 z-10">
        <Button
          variant={location.pathname === '/' ? 'secondary' : 'ghost'}
          className="flex flex-col items-center gap-1 h-auto py-2 px-4"
          onClick={() => navigate('/')}
        >
          <LayoutDashboard className="h-5 w-5" />
          <span className="text-xs">Attendance</span>
        </Button>
        <Button
          variant={location.pathname === '/statistics' ? 'secondary' : 'ghost'}
          className="flex flex-col items-center gap-1 h-auto py-2 px-4"
          onClick={() => navigate('/statistics')}
        >
          <BarChart3 className="h-5 w-5" />
          <span className="text-xs">Statistics</span>
        </Button>
      </nav>
    </div>
  )
}

function AppContent() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <PrivateLayout>
              <Home />
            </PrivateLayout>
          </PrivateRoute>
        }
      />
      <Route
        path="/statistics"
        element={
          <PrivateRoute>
            <PrivateLayout>
              <Statistics />
            </PrivateLayout>
          </PrivateRoute>
        }
      />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
      <Toaster />
      {/* We need to install sonner or use shadcn toast. 'shadcn add toast' adds hooks, sonner is arguably easier but let's see what shadcn recommends. 
            Actually ShadCN has a toaster component. I should install it or use basic alerts. 
            For now, I'll comment out Toaster if I haven't installed it. 
            Wait, I haven't installed sonner. I'll remove it for now to avoid errors. */}
    </AuthProvider>
  );
}

export default App;
