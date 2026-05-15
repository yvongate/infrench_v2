import { useState, useEffect } from 'react';

const API_URL = process.env.NEXT_PUBLIC_AUTH_URL || 'http://localhost:3001';

// MODE DEV: Authentification desactivee - mettre false pour reactiver
const AUTH_DISABLED = true;

const MOCK_USER = {
    id: 'dev-user',
    name: 'Dev User',
    email: 'dev@infrench.local',
};

export const authClient = {
    useSession: () => {
        const [session, setSession] = useState<{ user: any } | null>(
            AUTH_DISABLED ? { user: MOCK_USER } : null
        );
        const [loading, setLoading] = useState(!AUTH_DISABLED);

        useEffect(() => {
            if (AUTH_DISABLED) return;

            const fetchSession = async () => {
                try {
                    const res = await fetch(`${API_URL}/auth/profile`, {
                        credentials: 'include',
                    });

                    if (res.ok) {
                        const user = await res.json();
                        setSession({ user });
                    } else {
                        setSession(null);
                    }
                } catch (e) {
                    setSession(null);
                } finally {
                    setLoading(false);
                }
            };

            fetchSession();
        }, []);

        return { data: session, isPending: loading };
    },

    signIn: {
        email: async ({ email, password }: any) => {
            if (AUTH_DISABLED) {
                window.location.href = '/dashboard';
                return { data: { user: MOCK_USER } };
            }

            try {
                const res = await fetch(`${API_URL}/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password }),
                    credentials: 'include',
                });

                const data = await res.json();

                if (!res.ok) {
                    return { error: { message: data.message || 'Erreur de connexion' } };
                }

                window.location.href = '/dashboard';
                return { data };
            } catch (err) {
                return { error: { message: 'Erreur reseau' } };
            }
        }
    },

    signUp: {
        email: async ({ email, password, name }: any) => {
            if (AUTH_DISABLED) {
                window.location.href = '/dashboard';
                return { data: { user: MOCK_USER } };
            }

            try {
                const res = await fetch(`${API_URL}/auth/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password, name }),
                    credentials: 'include',
                });

                const data = await res.json();

                if (!res.ok) {
                    return { error: { message: data.message || "Erreur d'inscription" } };
                }

                window.location.href = '/dashboard';
                return { data };
            } catch (err) {
                return { error: { message: 'Erreur reseau' } };
            }
        }
    },

    signOut: async () => {
        if (AUTH_DISABLED) {
            window.location.href = '/dashboard';
            return { success: true };
        }

        document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        window.location.href = '/login';
        return { success: true };
    }
};
