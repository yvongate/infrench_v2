"use client";

import { Upload, Video } from "lucide-react";
import { useState, useRef } from "react";
import { cn } from "@/lib/utils";

interface VideoUploaderProps {
    className?: string;
}

export function VideoUploader({ className }: VideoUploaderProps) {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [srtOriginal, setSrtOriginal] = useState<string>("");
    const [srtTranslated, setSrtTranslated] = useState<string>("");
    const [audioUrl, setAudioUrl] = useState<string>("");
    const [error, setError] = useState<string>("");
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file && file.type.startsWith("video/")) {
            setSelectedFile(file);
            setSrtOriginal("");
            setSrtTranslated("");
            setAudioUrl("");
            setError("");
        }
    };

    const handleProcess = async () => {
        if (!selectedFile || isProcessing) return;

        setIsProcessing(true);
        setError("");
        setSrtOriginal("");
        setSrtTranslated("");
        setAudioUrl("");

        try {
            const formData = new FormData();
            formData.append("video", selectedFile);

            const response = await fetch("http://localhost:8000/api/transcribe", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Erreur ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                setSrtOriginal(data.srt_original || "");
                setSrtTranslated(data.srt_translated || "");

                if (data.audio_url) {
                    const fullAudioUrl = `http://localhost:8000${data.audio_url}`;
                    setAudioUrl(fullAudioUrl);

                    // Téléchargement automatique de l'audio MP3
                    try {
                        const audioResponse = await fetch(fullAudioUrl);
                        const audioBlob = await audioResponse.blob();
                        const audioDownloadUrl = URL.createObjectURL(audioBlob);
                        const audioLink = document.createElement("a");
                        audioLink.href = audioDownloadUrl;
                        audioLink.download = `${selectedFile.name}_FR.mp3`;
                        document.body.appendChild(audioLink);
                        audioLink.click();
                        document.body.removeChild(audioLink);
                        URL.revokeObjectURL(audioDownloadUrl);
                    } catch (audioErr) {
                        console.error("Erreur téléchargement audio:", audioErr);
                    }
                }

                // Téléchargement SRT traduit
                if (data.srt_translated) {
                    const blob = new Blob([data.srt_translated], { type: "application/x-subrip" });
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement("a");
                    link.href = url;
                    link.download = `${selectedFile.name}_FR_ADAPT.srt`;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    URL.revokeObjectURL(url);
                }
            } else {
                throw new Error("Le traitement a échoué");
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erreur lors du traitement");
        } finally {
            setIsProcessing(false);
        }
    };

    const handleClick = () => {
        if (!isProcessing) fileInputRef.current?.click();
    };

    const handleReset = () => {
        setSelectedFile(null);
        setSrtOriginal("");
        setSrtTranslated("");
        setAudioUrl("");
        setError("");
        if (fileInputRef.current) fileInputRef.current.value = "";
    };

    return (
        <div className={cn("w-full py-4", className)}>
            <div className="relative max-w-xl w-full mx-auto flex items-center flex-col gap-4">
                {/* Zone de sélection */}
                <div
                    onClick={handleClick}
                    className={cn(
                        "relative w-full rounded-3xl p-8 transition-all duration-300",
                        "border-2 border-dashed",
                        isProcessing
                            ? "border-blue-500 bg-blue-50/50 dark:bg-blue-950/20 cursor-not-allowed"
                            : "border-gray-300 dark:border-gray-600 bg-white/50 dark:bg-black/20 cursor-pointer hover:border-blue-400 hover:bg-blue-50/30 dark:hover:bg-blue-950/10"
                    )}
                >
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="video/*"
                        onChange={handleFileSelect}
                        className="hidden"
                        disabled={isProcessing}
                    />

                    <div className="flex flex-col items-center gap-4">
                        {isProcessing ? (
                            <>
                                <div className="w-16 h-16 bg-blue-500 rounded-sm animate-spin" style={{ animationDuration: "3s" }} />
                                <p className="text-lg font-medium text-gray-700 dark:text-gray-300">Doublage en cours...</p>
                                <p className="text-xs text-blue-500 animate-pulse text-center">
                                    Mistral (Traduction) + Zonos (Voix)
                                </p>
                            </>
                        ) : selectedFile ? (
                            <>
                                <Video className="w-16 h-16 text-blue-500" />
                                <div className="text-center">
                                    <p className="text-lg font-medium text-gray-700 dark:text-gray-300">{selectedFile.name}</p>
                                    <p className="text-sm text-gray-500 dark:text-gray-400">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                                </div>
                            </>
                        ) : (
                            <>
                                <Upload className="w-16 h-16 text-gray-400" />
                                <div className="text-center">
                                    <p className="text-lg font-medium text-gray-700 dark:text-gray-300">Cliquez pour "InFrench" votre vidéo</p>
                                    <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
                                        Transcription, Traduction et Voix Synchronisée
                                    </p>
                                </div>
                            </>
                        )}
                    </div>
                </div>

                {/* Bouton de traitement */}
                {selectedFile && !isProcessing && !audioUrl && (
                    <button
                        onClick={(e) => { e.stopPropagation(); handleProcess(); }}
                        className="w-full max-w-xs px-6 py-3 rounded-full font-medium bg-blue-500 hover:bg-blue-600 text-white shadow-lg transform hover:scale-105 transition-all"
                    >
                        Générer le Doublage Français
                    </button>
                )}

                {/* Résultats */}
                {audioUrl && (
                    <div className="w-full max-w-2xl space-y-6">
                        <div className="p-6 bg-blue-50 dark:bg-blue-900/20 rounded-2xl border border-blue-200 dark:border-blue-800 shadow-sm">
                            <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-300 mb-4 flex items-center gap-2">
                                🔊 Doublage Français (Voix Zonos)
                            </h3>
                            <audio controls className="w-full mb-4">
                                <source src={audioUrl} type="audio/mpeg" />
                                Votre navigateur ne supporte pas l'élément audio.
                            </audio>
                            <a
                                href={audioUrl}
                                download={`${selectedFile?.name}_FR.mp3`}
                                className="text-sm text-blue-600 hover:underline font-medium"
                            >
                                Télécharger l'audio seul
                            </a>
                        </div>

                        <div className="p-6 bg-green-50 dark:bg-green-950/20 rounded-2xl border border-green-200 dark:border-green-800">
                            <h3 className="text-lg font-semibold text-green-800 dark:text-green-300 mb-3">
                                📝 Sous-titres Synchronisés
                            </h3>
                            <div className="max-h-48 overflow-y-auto p-4 bg-black/5 dark:bg-black/40 rounded-lg font-mono text-[10px] leading-tight">
                                <pre className="whitespace-pre-wrap">{srtTranslated}</pre>
                            </div>
                        </div>

                        <details className="group border border-gray-200 dark:border-gray-800 rounded-xl">
                            <summary className="p-3 cursor-pointer text-xs font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 list-none flex items-center justify-between">
                                Voir SRT Original (Anglais)
                                <span className="transition-transform group-open:rotate-180 text-[10px]">▼</span>
                            </summary>
                            <div className="p-4 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-800 font-mono text-[10px]">
                                <pre className="whitespace-pre-wrap">{srtOriginal}</pre>
                            </div>
                        </details>

                        <button onClick={handleReset} className="w-full px-4 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-xl text-sm font-medium transition-colors">
                            Nouvelle vidéo
                        </button>
                    </div>
                )}

                {/* Erreurs */}
                {error && (
                    <div className="w-full max-w-2xl p-4 bg-red-50 dark:bg-red-950/20 rounded-2xl border border-red-200">
                        <p className="text-sm text-red-700">❌ {error}</p>
                    </div>
                )}
            </div>
        </div>
    );
}
