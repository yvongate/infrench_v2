"use client";

import { DashboardLayout } from "@/components/dashboard-layout";
import { authClient } from "@/lib/auth-client";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { VideoUploader } from "@/components/ui/video-uploader";

export default function DashboardPage() {
    const { data: session } = authClient.useSession();

    return (
        <DashboardLayout>
            <div className="space-y-8">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">
                        Bienvenue, {session?.user?.name || "Utilisateur"} !
                    </h2>
                    <p className="text-muted-foreground">
                        Traduisez et doublez vos vidéos en un clic.
                    </p>
                </div>

                <div className="w-full">
                    <Card>
                        <CardHeader>
                            <CardTitle>Nouvelle Traduction</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <VideoUploader />
                        </CardContent>
                    </Card>
                </div>
            </div>
        </DashboardLayout>
    );
}
