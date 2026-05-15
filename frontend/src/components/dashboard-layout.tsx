"use client";

import React, { useState } from "react";
import { Sidebar, SidebarBody, SidebarLink } from "@/components/ui/sidebar";
import {
    LayoutDashboard,
    LogOut,

    Home,
} from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Logo } from "@/components/logo";
import { authClient } from "@/lib/auth-client";
import { useRouter } from "next/navigation";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
    const { data: session } = authClient.useSession();
    const router = useRouter();

    const links = [
        {
            label: "Dashboard",
            href: "/dashboard",
            icon: (
                <LayoutDashboard className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />
            ),
        },
    ];
    const [open, setOpen] = useState(false);

    const handleLogout = async () => {
        await authClient.signOut();
        router.push("/");
        router.refresh();
    };

    return (
        <div
            className={cn(
                "rounded-md flex flex-col md:flex-row bg-gray-100 dark:bg-neutral-800 w-full flex-1 max-w-full mx-auto border border-neutral-200 dark:border-neutral-700 overflow-hidden",
                "h-screen"
            )}
        >
            <Sidebar open={open} setOpen={setOpen}>
                <SidebarBody className="justify-between gap-10">
                    <div className="flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
                        {open ? <LogoIcon /> : <LogoIconMini />}
                        <div className="mt-8 flex flex-col gap-2">
                            {links.map((link, idx) => (
                                <SidebarLink key={idx} link={link} />
                            ))}
                        </div>
                    </div>
                    <div>
                        <SidebarLink
                            link={{
                                label: session?.user?.name || "Utilisateur",
                                href: "/dashboard", // Redirection vers dashboard car profile supprimé
                                icon: (
                                    <div className="h-7 w-7 rounded-full bg-primary flex items-center justify-center text-white text-xs font-bold">
                                        {session?.user?.name?.charAt(0) || "U"}
                                    </div>
                                ),
                            }}
                        />
                        <button
                            onClick={handleLogout}
                            className="flex items-center justify-start gap-2 group/sidebar py-2 w-full"
                        >
                            <LogOut className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />
                            {open && (
                                <span className="text-neutral-700 dark:text-neutral-200 text-sm group-hover/sidebar:translate-x-1 transition duration-150">
                                    Déconnexion
                                </span>
                            )}
                        </button>
                    </div>
                </SidebarBody>
            </Sidebar>
            <div className="flex-1 overflow-y-auto bg-white dark:bg-neutral-900">
                <div className="p-4 md:p-10 flex flex-col gap-4">
                    {children}
                </div>
            </div>
        </div>
    );
}

const LogoIcon = () => {
    return (
        <Link
            href="/"
            className="font-normal flex space-x-2 items-center text-sm text-black py-1 relative z-20"
        >
            <Logo className="h-6 w-auto" />
            <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="font-medium text-black dark:text-white whitespace-pre"
            >
                inFrench
            </motion.span>
        </Link>
    );
};
const LogoIconMini = () => {
    return (
        <Link
            href="/"
            className="font-normal flex space-x-2 items-center text-sm text-black py-1 relative z-20"
        >
            <Logo className="h-6 w-6" />
        </Link>
    );
};
