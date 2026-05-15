import { LogoIcon } from '@/components/logo'
import Link from 'next/link'

const links = [
    {
        title: 'Fonctionnalités',
        href: '#features',
    },
    {
        title: 'Manifesto',
        href: '#manifesto',
    },
    {
        title: 'Contact',
        href: 'mailto:contact@infrench.v2',
    },
]

export default function FooterSection() {
    return (
        <footer className="bg-background border-t py-12">
            <div className="mx-auto max-w-5xl px-6">
                <div className="flex flex-wrap justify-between gap-12">
                    <div className="order-last flex items-center gap-3 md:order-first">
                        <Link
                            href="/"
                            aria-label="go home">
                            <LogoIcon />
                        </Link>
                        <span className="text-muted-foreground block text-center text-sm">© {new Date().getFullYear()} inFrench. Tous droits réservés.</span>
                    </div>

                    <div className="order-first flex flex-wrap gap-x-6 gap-y-4 md:order-last">
                        {links.map((link, index) => (
                            <Link
                                key={index}
                                href={link.href}
                                className="text-muted-foreground hover:text-primary block duration-150">
                                <span>{link.title}</span>
                            </Link>
                        ))}
                    </div>
                </div>
            </div>
        </footer>
    )
}
