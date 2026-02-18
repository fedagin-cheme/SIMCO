import { Construction } from 'lucide-react'

interface ComingSoonProps {
  title: string
  phase: string
  description: string
}

export function ComingSoonPage({ title, phase, description }: ComingSoonProps) {
  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="text-center space-y-4 max-w-sm">
        <div className="p-4 bg-surface-700 rounded-full w-16 h-16 flex items-center justify-center mx-auto">
          <Construction size={28} className="text-primary-500" />
        </div>
        <div>
          <p className="text-primary-500 text-xs font-semibold uppercase tracking-widest mb-1">{phase}</p>
          <h2 className="text-slate-100 font-semibold text-lg">{title}</h2>
          <p className="text-slate-500 text-sm mt-2">{description}</p>
        </div>
      </div>
    </div>
  )
}
