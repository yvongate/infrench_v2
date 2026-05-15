import Image from 'next/image'
import { cn } from '@/lib/utils'

export const Logo = ({ className }: { className?: string }) => {
    return (
        <div className={cn('flex items-center gap-2', className)}>
            <Image
                src="/logo.png"
                alt="InFrench Logo"
                width={32}
                height={32}
                className="h-8 w-auto"
            />
            <span className="text-xl font-bold tracking-tight text-foreground">inFrench</span>
        </div>
    )
}

export const LogoIcon = ({ className }: { className?: string }) => {
    return (
        <Image
            src="/logo.png"
            alt="InFrench LogoIcon"
            width={32}
            height={32}
            className={cn('size-5', className)}
        />
    )
}

export const LogoStroke = ({ className }: { className?: string }) => {
    return (
        <Image
            src="/logo.png"
            alt="InFrench LogoStroke"
            width={32}
            height={32}
            className={cn('size-7 w-7', className)}
        />
    )
}
