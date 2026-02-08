"use client";

import { AIInputWithLoading } from "@/components/ui/ai-input-with-loading";

export default function AIDemoPage() {
    const handleSubmit = async (value: string) => {
        console.log("User submitted:", value);
        // Simuler un appel API
        await new Promise((resolve) => setTimeout(resolve, 2000));
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
            <div className="w-full max-w-2xl px-4">
                <div className="text-center mb-8">
                    <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
                        AI Input Demo
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400">
                        Testez le composant AI Input avec animation de chargement
                    </p>
                </div>

                <AIInputWithLoading
                    placeholder="Posez votre question ici..."
                    onSubmit={handleSubmit}
                    loadingDuration={3000}
                    thinkingDuration={1000}
                />

                <div className="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
                    <p>Appuyez sur Entrée ou cliquez sur l'icône pour soumettre</p>
                    <p className="mt-1">Shift + Entrée pour un saut de ligne</p>
                </div>
            </div>
        </div>
    );
}
