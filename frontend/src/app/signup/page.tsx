"use client";

import { useState } from "react";
import { authClient } from "@/lib/auth-client";
import { useRouter } from "next/navigation";
import { AnimatedAuthForm } from "@/components/animated-auth-form";

export default function SignupPage() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const router = useRouter();

    const handleSignup = async (e: React.FormEvent<HTMLFormElement>, data: any) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        const { data: session, error } = await authClient.signUp.email({
            email: data.email,
            password: data.password,
            name: data.name,
        });

        if (error) {
            setError(error.message || "Erreur lors de l'inscription");
        } else {
            router.push("/");
            router.refresh();
        }
        setLoading(false);
    };

    return (
        <AnimatedAuthForm
            mode="signup"
            onSubmit={handleSignup}
            isLoading={loading}
            error={error}
        />
    );
}
