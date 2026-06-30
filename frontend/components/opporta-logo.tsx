import Image from 'next/image'
import { cn } from '@/lib/utils'

interface OpportaLogoProps {
  /** Size of the logo mark icon */
  iconSize?: 'sm' | 'md' | 'lg' | 'xl'
  /** Whether to show the OPPORTA wordmark next to the icon */
  showWordmark?: boolean
  /** Extra class names on the wrapper */
  className?: string
  /** Extra class names on the wordmark text */
  wordmarkClassName?: string
}

const sizeMap = {
  sm: { img: 28, text: 'text-base' },
  md: { img: 36, text: 'text-lg' },
  lg: { img: 48, text: 'text-2xl' },
  xl: { img: 64, text: 'text-3xl' },
}

export function OpportaLogo({
  iconSize = 'md',
  showWordmark = true,
  className,
  wordmarkClassName,
}: OpportaLogoProps) {
  const { img, text } = sizeMap[iconSize]

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <Image
        src="/opporta-logo.png"
        alt="OPPORTA logo mark"
        width={img}
        height={img}
        className="flex-shrink-0 object-contain"
        priority
      />
      {showWordmark && (
        <span
          className={cn('opporta-wordmark', text, wordmarkClassName)}
          aria-label="OPPORTA"
        >
          OPPORTA
        </span>
      )}
    </div>
  )
}
