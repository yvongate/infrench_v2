"use client";

import { DashboardLayout } from "@/components/dashboard-layout";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Video, Trash2, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";

export default function VideosPage() {
    const [videos, setVideos] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [page, setPage] = useState(1);
    const [pagination, setPagination] = useState({
        total: 0,
        page: 1,
        limit: 9,
        totalPages: 0,
    });
    const AUTH_URL = process.env.NEXT_PUBLIC_AUTH_URL || "http://localhost:3001";
    const AUTH_DISABLED = true; // Mettre false quand backend_principal tourne

    useEffect(() => {
        if (AUTH_DISABLED) { setLoading(false); return; }
        const timeoutId = setTimeout(() => { fetchVideos(); }, 300);
        return () => clearTimeout(timeoutId);
    }, [search, page]);

    const fetchVideos = async () => {
        if (AUTH_DISABLED) { setLoading(false); return; }
        setLoading(true);
        try {
            const params = new URLSearchParams({
                page: page.toString(),
                limit: '9',
                ...(search && { search }),
            });

            const response = await fetch(`${AUTH_URL}/videos?${params}`, {
                credentials: "include",
            });
            if (response.ok) {
                const data = await response.json();
                setVideos(data.videos || []);
                setPagination(data.pagination || { total: 0, page: 1, limit: 9, totalPages: 0 });
            }
        } catch (err) {
            console.error("Failed to fetch videos:", err);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (confirm("Supprimer cette vidéo ?")) {
            try {
                const response = await fetch(`${AUTH_URL}/videos/${id}`, {
                    method: "DELETE",
                    credentials: "include",
                });
                if (response.ok) {
                    fetchVideos(); // Refresh list after delete
                }
            } catch (err) {
                console.error("Failed to delete video:", err);
            }
        }
    };

    const handleDeleteAll = async () => {
        if (confirm("Voulez-vous vraiment TOUT supprimer ? Cette action est irréversible.")) {
            try {
                const response = await fetch(`${AUTH_URL}/videos`, {
                    method: "DELETE",
                    credentials: "include",
                });
                if (response.ok) {
                    setVideos([]);
                    setPagination({ total: 0, page: 1, limit: 9, totalPages: 0 });
                }
            } catch (err) {
                console.error("Failed to delete all videos:", err);
            }
        }
    };

    const handleDownload = (url: string, title: string) => {
        if (url) {
            const link = document.createElement("a");
            link.href = url;
            link.download = title;
            link.click();
        } else {
            alert("URL de téléchargement non disponible");
        }
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight">Mes Vidéos</h2>
                        <p className="text-muted-foreground">
                            {search
                                ? `${pagination.total} vidéo${pagination.total > 1 ? 's' : ''} trouvée${pagination.total > 1 ? 's' : ''}`
                                : 'Gérez vos vidéos traduites.'
                            }
                        </p>
                    </div>
                    <div>
                        {videos.length > 0 && (
                            <Button
                                variant="destructive"
                                onClick={handleDeleteAll}
                                className="flex items-center gap-2"
                            >
                                <Trash2 className="h-4 w-4" />
                                Tout Supprimer
                            </Button>
                        )}
                    </div>
                </div>

                {/* Search Bar */}
                <div className="flex gap-2">
                    <input
                        type="text"
                        placeholder="Rechercher une vidéo..."
                        value={search}
                        onChange={(e) => {
                            setSearch(e.target.value);
                            setPage(1);
                        }}
                        className="flex-1 px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                </div>

                {loading ? (
                    <div className="text-center py-20 text-muted-foreground">
                        Chargement...
                    </div>
                ) : videos.length === 0 ? (
                    <div className="text-center py-20 text-muted-foreground">
                        Aucune vidéo pour le moment.
                    </div>
                ) : (
                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                        {videos.map((video) => (
                            <Card key={video.id} className="overflow-hidden group hover:border-primary transition-all">
                                <div className="aspect-video bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center relative">
                                    <Video className="h-10 w-10 text-neutral-300 group-hover:text-primary transition-colors" />
                                    <div className="absolute bottom-2 right-2 px-1.5 py-0.5 rounded bg-black/60 text-white text-[10px]">
                                        {video.duration || "00:00"}
                                    </div>
                                </div>
                                <CardHeader className="p-4">
                                    <CardTitle className="text-base truncate">{video.title}</CardTitle>
                                    <div className="text-xs text-muted-foreground">
                                        {new Date(video.createdAt).toLocaleDateString('fr-FR', {
                                            day: 'numeric',
                                            month: 'long',
                                            year: 'numeric'
                                        })}
                                    </div>
                                </CardHeader>
                                <CardContent className="p-4 pt-0 flex gap-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="flex-1 gap-1"
                                        onClick={() => handleDownload(video.translatedUrl, video.title)}
                                    >
                                        <Download className="h-3 w-3" />
                                        Télécharger
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="text-red-500 hover:text-red-700 hover:bg-red-50"
                                        onClick={() => handleDelete(video.id)}
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}

                {/* Pagination */}
                {!loading && pagination.totalPages > 1 && (
                    <div className="flex justify-center items-center gap-2 mt-6">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setPage(page - 1)}
                            disabled={page === 1}
                        >
                            Précédent
                        </Button>
                        <span className="text-sm text-muted-foreground">
                            Page {page} sur {pagination.totalPages}
                        </span>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setPage(page + 1)}
                            disabled={page === pagination.totalPages}
                        >
                            Suivant
                        </Button>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}
