"use client";

import { VideoUploader } from "@/components/ui/video-uploader";
import Image from "next/image";

export default function Home() {
  return (
    <div className="relative min-h-screen flex items-center justify-center">
      {/* Image de fond */}
      <Image
        src="/arriere_gradient.jpg"
        alt="Background"
        fill
        className="object-cover"
        priority
      />

      {/* Overlay sombre pour améliorer la lisibilité */}
      <div className="absolute inset-0 bg-black/30" />

      {/* Contenu */}
      <div className="relative z-10 w-full max-w-2xl px-4">
        {/* Conteneur avec effet glassmorphism */}
        <div className="backdrop-blur-xl bg-white/80 dark:bg-black/60 rounded-3xl p-8 shadow-2xl border border-white/20">
          <VideoUploader processingDuration={3000} />
        </div>
      </div>
    </div>
  );
}
