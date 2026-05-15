"use client";

import { useState } from "react";
import { authClient } from "@/lib/auth-client";
import { useRouter } from "next/navigation";
import { AnimatedAuthForm } from "@/components/animated-auth-form";

export default function LoginPage() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const router = useRouter();

    const handleLogin = async (e: React.FormEvent<HTMLFormElement>, data: any) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        const { data: session, error } = await authClient.signIn.email({
            email: data.email,
            password: data.password,
        });

        if (error) {
            setError(error.message || "Erreur lors de la connexion");
        } else {
            router.push("/");
            router.refresh();
        }
        setLoading(false);
    };

    return (
        <AnimatedAuthForm
            mode="login"
            onSubmit={handleLogin}
            isLoading={loading}
            error={error}
        />
    );
}
