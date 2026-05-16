"use client";

import { Upload, Video } from "lucide-react";
import { useState, useRef, useEffect } from "react";
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
    const [videoUrl, setVideoUrl] = useState<string>("");
    const [error, setError] = useState<string>("");
    const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
    const fileInputRef = useRef<HTMLInputElement>(null);

    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    // Vérifier la connexion au backend au chargement
    useEffect(() => {
        const checkHealth = async () => {
            try {
                const res = await fetch(`${API_URL}/health`);
                if (res.ok) setBackendStatus("online");
                else setBackendStatus("offline");
            } catch (err) {
                setBackendStatus("offline");
            }
        };
        checkHealth();
    }, [API_URL]);

    const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file && file.type.startsWith("video/")) {
            setSelectedFile(file);
            setSrtOriginal("");
            setSrtTranslated("");
            setAudioUrl("");
            setVideoUrl("");
            setError("");
        }
    };

    const downloadAudio = async (fullAudioUrl: string) => {
        try {
            const audioResponse = await fetch(fullAudioUrl);
            const audioBlob = await audioResponse.blob();
            const audioDownloadUrl = URL.createObjectURL(audioBlob);
            const audioLink = document.createElement("a");
            audioLink.href = audioDownloadUrl;
            audioLink.download = `${selectedFile?.name}_FR.mp3`;
            document.body.appendChild(audioLink);
            audioLink.click();
            document.body.removeChild(audioLink);
            URL.revokeObjectURL(audioDownloadUrl);
        } catch (audioErr) {
            console.error("Erreur téléchargement audio:", audioErr);
        }
    };

    const pollAudioStatus = async (jobId: string) => {
        const maxAttempts = 150; // 5 minutes max (150 * 2s)
        let attempts = 0;

        const poll = async (): Promise<void> => {
            try {
                const response = await fetch(`${API_URL}/api/audio-status/${jobId}`);
                if (!response.ok) {
                    console.error("Erreur lors du polling:", response.status);
                    return;
                }

                const status = await response.json();
                console.log(`Job ${jobId}: ${status.status} - ${status.progress}%`);

                if (status.status === "completed" && (status.video_url || status.audio_url)) {
                    // Video doublee disponible
                    if (status.video_url) {
                        const fullVideoUrl = `${API_URL}${status.video_url}`;
                        setVideoUrl(fullVideoUrl);
                        // Telecharger la video automatiquement
                        const videoLink = document.createElement("a");
                        videoLink.href = fullVideoUrl;
                        videoLink.download = `${selectedFile?.name?.replace(/\.[^/.]+$/, "")}_FR.mp4`;
                        document.body.appendChild(videoLink);
                        videoLink.click();
                        document.body.removeChild(videoLink);
                    }
                    // Audio aussi disponible
                    if (status.audio_url) {
                        const fullAudioUrl = `${API_URL}${status.audio_url}`;
                        setAudioUrl(fullAudioUrl);
                    }

                    // Save video to backend (DISABLED - auth off)
                    // TODO: Reactiver quand backend_principal tourne
                    setIsProcessing(false);
                    return;
                } else if (status.status === "failed") {
                    setError(`Génération audio échouée: ${status.error || "Erreur inconnue"}`);
                    setIsProcessing(false);
                    return;
                } else if (attempts < maxAttempts) {
                    attempts++;
                    setTimeout(poll, 2000); // Poll toutes les 2 secondes
                } else {
                    setError("Timeout: La génération audio prend trop de temps");
                    setIsProcessing(false);
                }
            } catch (err) {
                console.error("Erreur polling:", err);
                setError("Erreur lors de la vérification du statut audio");
                setIsProcessing(false);
            }
        };

        await poll();
    };

    const handleProcess = async () => {
        if (!selectedFile || isProcessing) return;

        setIsProcessing(true);
        setError("");
        setSrtOriginal("");
        setSrtTranslated("");
        setAudioUrl("");
        setVideoUrl("");

        try {
            const formData = new FormData();
            formData.append("video", selectedFile);

            // Timeout de 5 minutes pour permettre au TTS de se terminer
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5 * 60 * 1000);

            const response = await fetch(`${API_URL}/api/transcribe`, {
                method: "POST",
                body: formData,
                signal: controller.signal,
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Erreur ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                setSrtOriginal(data.srt_original || "");
                setSrtTranslated(data.srt_translated || "");

                // Si un job_id est retourné, démarrer le polling pour l'audio
                // Le spinner continue jusqu'à ce que la vidéo soit prête
                if (data.job_id) {
                    console.log(`Job TTS créé: ${data.job_id}`);
                    await pollAudioStatus(data.job_id);
                } else if (data.audio_url) {
                    // Cas où l'audio est déjà disponible (backward compatibility)
                    const fullAudioUrl = `${API_URL}${data.audio_url}`;
                    setAudioUrl(fullAudioUrl);
                    setIsProcessing(false);
                } else {
                    // Pas de job, pas d'audio - arrêter le spinner
                    setIsProcessing(false);
                }
            } else {
                throw new Error("Le traitement a échoué");
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erreur lors du traitement");
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
        setVideoUrl("");
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
                        {/* Indicateur de statut backend */}
                        <div className="absolute top-4 right-4 flex items-center gap-2">
                            <div className={cn(
                                "w-2 h-2 rounded-full",
                                backendStatus === "online" ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" :
                                    backendStatus === "offline" ? "bg-red-500" : "bg-gray-400 animate-pulse"
                            )} />
                            <span className="text-[10px] font-medium text-gray-400 uppercase tracking-wider">
                                {backendStatus === "online" ? "Server Online" :
                                    backendStatus === "offline" ? "Server Offline" : "Checking..."}
                            </span>
                        </div>

                        {isProcessing ? (
                            <>
                                <div className="w-16 h-16 bg-blue-500 rounded-sm animate-spin" style={{ animationDuration: "3s" }} />
                                <p className="text-lg font-medium text-gray-700 dark:text-gray-300">Doublage en cours...</p>
                                <p className="text-xs text-blue-500 animate-pulse text-center">
                                    Mistral (Traduction) + Qwen3-TTS (Voix)
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
                {(videoUrl || audioUrl) && (
                    <div className="w-full max-w-2xl space-y-6">
                        {/* Video doublee */}
                        {videoUrl && (
                            <div className="p-6 bg-purple-50 dark:bg-purple-900/20 rounded-2xl border border-purple-200 dark:border-purple-800 shadow-sm">
                                <h3 className="text-lg font-semibold text-purple-800 dark:text-purple-300 mb-4 flex items-center gap-2">
                                    🎬 Video Doublee en Francais
                                </h3>
                                <video controls className="w-full mb-4 rounded-lg">
                                    <source src={videoUrl} type="video/mp4" />
                                    Votre navigateur ne supporte pas la video.
                                </video>
                                <a
                                    href={videoUrl}
                                    download={`${selectedFile?.name?.replace(/\.[^/.]+$/, "")}_FR.mp4`}
                                    className="text-sm text-purple-600 hover:underline font-medium"
                                >
                                    Telecharger la video doublee
                                </a>
                            </div>
                        )}

                        {/* Audio seul */}
                        {audioUrl && (
                            <div className="p-6 bg-blue-50 dark:bg-blue-900/20 rounded-2xl border border-blue-200 dark:border-blue-800 shadow-sm">
                                <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-300 mb-4 flex items-center gap-2">
                                    🔊 Audio Francais (Qwen3-TTS)
                                </h3>
                                <audio controls className="w-full mb-4">
                                    <source src={audioUrl} type="audio/mpeg" />
                                </audio>
                                <a
                                    href={audioUrl}
                                    download={`${selectedFile?.name}_FR.mp3`}
                                    className="text-sm text-blue-600 hover:underline font-medium"
                                >
                                    Telecharger l'audio seul
                                </a>
                            </div>
                        )}

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
