import React from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { HeroHeader } from './header'
import { ChevronRight } from 'lucide-react'
import Image from 'next/image'

export default function HeroSection() {
    return (
        <>
            <HeroHeader />
            <main className="overflow-hidden">
                <section className="bg-linear-to-b to-muted from-background">
                    <div className="relative py-36">
                        <div className="relative z-10 mx-auto w-full max-w-5xl px-6">
                            <div className="md:w-1/2">
                                <div>
                                    <h1 className="max-w-md text-balance text-5xl font-medium md:text-6xl text-foreground">Traduisez vos vidéos en français</h1>
                                    <p className="text-muted-foreground my-8 max-w-2xl text-balance text-xl">Doublez vos contenus avec une voix naturelle grâce à l'IA. Simple, rapide et gratuit.</p>

                                    <div className="flex items-center gap-3">
                                        <Button
                                            asChild
                                            size="lg"
                                            className="pr-4.5">
                                            <Link href="/dashboard">
                                                <span className="text-nowrap">Commencer</span>
                                                <ChevronRight className="opacity-50" />
                                            </Link>
                                        </Button>
                                        
                                    </div>
                                </div>

                                <div className="mt-10">
                                    <p className="text-muted-foreground">Trusted by teams at :</p>
                                    <div className="mt-6 grid max-w-sm grid-cols-3 gap-6">
                                        <div className="flex">
                                            <img
                                                className="h-14 w-fit"
                                                src="/iua.png"
                                                alt="IUA Logo"
                                                height="32"
                                                width="auto"
                                            />
                                        </div>
                                        <div className="flex">
                                            <img
                                                className="h-14 w-fit"
                                                src="/iugb.png"
                                                alt="IUGB Logo"
                                                height="32"
                                                width="auto"
                                            />
                                        </div>
                                        <div className="flex">
                                            <img
                                                className="h-14 w-fit"
                                                src="/umeci.png"
                                                alt="UMECI Logo"
                                                height="32"
                                                width="auto"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="hidden md:block perspective-near md:absolute md:-right-6 md:bottom-16 md:left-1/2 md:top-40">
                            <div className="before:border-foreground/5 before:bg-foreground/5 relative h-full before:absolute before:-inset-x-4 before:bottom-7 before:top-0 before:skew-x-6 before:rounded-[calc(var(--radius)+1rem)] before:border">
                                <div className="bg-background rounded-(--radius) shadow-foreground/10 ring-foreground/5 relative h-full -translate-y-12 skew-x-6 overflow-hidden border border-transparent shadow-md ring-1">
                                    <Image
                                        src="/hero.png"
                                        alt="infrench_v2 app screen"
                                        width={2880}
                                        height={1842}
                                        className="object-top-left size-full object-cover"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            </main>
        </>
    )
}
