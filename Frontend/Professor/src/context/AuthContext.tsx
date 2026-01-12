import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface User {
    id: number;
    email: string; // Professor email
    role: 'professor';
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    login: (token: string, userData: User) => void;
    logout: () => void;
    isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem('aura_prof_token'));

    useEffect(() => {
        if (token) {
            // Here we could validate token or fetch profile if needed.
            // For now, we assume if token exists, we are somewhat auth'd, 
            // but decoding JWT to get user info is better. 
            // For MVP, we'll rely on server 401s to log us out.
            // We can optionally store user in localstorage too.
            const storedUser = localStorage.getItem('aura_prof_user');
            if (storedUser) {
                setUser(JSON.parse(storedUser));
            }
        }
    }, [token]);

    const login = (newToken: string, userData: User) => {
        setToken(newToken);
        setUser(userData);
        localStorage.setItem('aura_prof_token', newToken);
        localStorage.setItem('aura_prof_user', JSON.stringify(userData));
        api.defaults.headers.Authorization = `Bearer ${newToken}`;
    };

    const logout = () => {
        setToken(null);
        setUser(null);
        localStorage.removeItem('aura_prof_token');
        localStorage.removeItem('aura_prof_user');
        delete api.defaults.headers.Authorization;
    };

    return (
        <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!token }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
