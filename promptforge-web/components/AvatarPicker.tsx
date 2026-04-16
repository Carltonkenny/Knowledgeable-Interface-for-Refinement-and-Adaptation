// components/AvatarPicker.tsx
// Kira-themed avatar selection - 10 professional yet playful options

'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Check, X, Sparkles } from 'lucide-react'

interface AvatarPickerProps {
  currentAvatar?: string | null
  onSelect: (avatarUrl: string) => void
  onClose: () => void
}

// 10 Kira-themed avatars - professional but with personality
// Using DiceBear "bottts" style for consistent robot/AI aesthetic
const AVATARS = [
  { 
    id: 'kira-core', 
    name: 'Kira Core', 
    desc: 'The original',
    url: 'https://api.dicebear.com/9.x/bottts/svg?seed=kira-core&backgroundColor=0d8abc&eyes=bulging&mouth=smile02&texture=carbon' 
  },
  { 
    id: 'neural-net', 
    name: 'Neural Net', 
    desc: 'Deep learning mode',
    url: 'https://api.dicebear.com/9.x/bottts/svg?seed=neural-net&backgroundColor=6b4c9a&eyes=eva&mouth=grill01&texture=electro' 
  },
  { 
    id: 'prompt-forge', 
    name: 'Prompt Forge', 
    desc: 'Master crafter',
    url: 'https://api.dicebear.com/9.x/bottts/svg?seed=prompt-forge&backgroundColor=c2410c&eyes=diamond&mouth=smile01&texture=shiny' 
  },
  { 
    id: 'data-wizard', 
    name: 'Data Wizard', 
    desc: 'Analytics guru',
    url: 'https://api.dicebear.com/9.x/bottts/svg?seed=data-wizard&backgroundColor=0f766e&eyes=frame01&mouth=smile02&texture=gradient' 
  },
  { 
    id: 'code-ninja', 
    name: 'Code Ninja', 
    desc: 'Silent but deadly',
    url: 'https://api.dicebear.com/9.x/bottts/svg?seed=code-ninja&backgroundColor=1e293b&eyes=glow&mouth=grill02&texture=dark' 
  },
  { 
    id: 'quantum-leap', 
    name: 'Quantum Leap', 
    desc: 'Beyond classical',
    url: 'https://api.dicebear.com/9.x/bottts/svg?seed=quantum-leap&backgroundColor=7c3aed&eyes=round&mouth=smile01&texture=holographic' 
  },
  { 
    id: 'cyber-punk', 
    name: 'Cyber Punk', 
    desc: 'Neon rebel',
    url: 'https://api.dicebear.com/9.x/bottts/svg?seed=cyber-punk&backgroundColor=db2777&eyes=cyber&mouth=grill01&texture=neon' 
  },
  { 
    id: 'space-cadet', 
    name: 'Space Cadet', 
    desc: 'Out of this world',
    url: 'https://api.dicebear.com/9.x/bottts/svg?seed=space-cadet&backgroundColor=0369a1&eyes=astro&mouth=smile02&texture=stars' 
  },
  { 
    id: 'pixel-punk', 
    name: 'Pixel Punk', 
    desc: 'Retro future',
    url: 'https://api.dicebear.com/9.x/bottts/svg?seed=pixel-punk&backgroundColor=ea580c&eyes=pixel&mouth=grill02&texture=retro' 
  },
  { 
    id: 'ghost-shell', 
    name: 'Ghost Shell', 
    desc: 'Stealth mode',
    url: 'https://api.dicebear.com/9.x/bottts/svg?seed=ghost-shell&backgroundColor=475569&eyes=ghost&mouth=smile01&texture=matte' 
  },
]

export default function AvatarPicker({ currentAvatar, onSelect, onClose }: AvatarPickerProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [hoveredId, setHoveredId] = useState<string | null>(null)

  const handleSelect = (avatar: typeof AVATARS[0]) => {
    setSelectedId(avatar.id)
    onSelect(avatar.url)
  }

  const isCurrentOrSelected = (avatar: typeof AVATARS[0]) => {
    return selectedId === avatar.id || currentAvatar === avatar.url
  }

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        transition={{ type: "spring", stiffness: 300, damping: 25 }}
        className="bg-layer2 border border-border-subtle rounded-2xl max-w-2xl w-full shadow-2xl overflow-hidden"
      >
        {/* Header with gradient */}
        <div className="relative bg-gradient-to-r from-kira/20 via-purple-500/20 to-kira/20 border-b border-border-subtle p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Sparkles size={18} className="text-kira" />
                <h2 className="text-lg font-bold text-text-bright">Choose Your Neural Identity</h2>
              </div>
              <p className="text-xs text-text-dim">Select an avatar to represent your AI persona</p>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-layer3 text-text-dim hover:text-text-bright transition-colors"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Avatar Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 p-6">
          {AVATARS.map((avatar) => {
            const isSelected = isCurrentOrSelected(avatar)
            const isHovered = hoveredId === avatar.id
            
            return (
              <motion.button
                key={avatar.id}
                onClick={() => handleSelect(avatar)}
                onMouseEnter={() => setHoveredId(avatar.id)}
                onMouseLeave={() => setHoveredId(null)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.98 }}
                className={`relative group flex flex-col items-center gap-2 p-3 rounded-xl border-2 transition-all duration-200
                  ${isSelected 
                    ? 'border-kira bg-kira/10 shadow-[0_0_20px_rgba(var(--color-kira),0.4)]' 
                    : 'border-border-subtle bg-layer1 hover:border-kira/50 hover:bg-kira/5'
                  }`}
              >
                {/* Avatar Image */}
                <div className="w-20 h-20 rounded-full overflow-hidden bg-layer3 relative">
                  <img 
                    src={avatar.url} 
                    alt={avatar.name}
                    className="w-full h-full object-cover"
                  />
                  {/* Glow effect on hover */}
                  {isHovered && !isSelected && (
                    <div className="absolute inset-0 bg-kira/20 rounded-full animate-pulse" />
                  )}
                  {/* Selected checkmark */}
                  {isSelected && (
                    <motion.div 
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-kira flex items-center justify-center shadow-lg"
                    >
                      <Check size={14} className="text-white" />
                    </motion.div>
                  )}
                </div>
                
                {/* Avatar Info */}
                <div className="text-center">
                  <span className={`text-xs font-bold block ${isSelected ? 'text-kira' : 'text-text-bright group-hover:text-kira'} transition-colors`}>
                    {avatar.name}
                  </span>
                  <span className="text-[9px] text-text-dim block mt-0.5">
                    {avatar.desc}
                  </span>
                </div>
              </motion.button>
            )
          })}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-border-subtle bg-layer1/50">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-kira animate-pulse" />
            <p className="text-[10px] text-text-dim font-mono">
              Avatars powered by DiceBear API • Kira Theme Pack v2.0
            </p>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-layer3 text-text-dim text-xs font-bold hover:bg-layer3/80 hover:text-text-bright transition-all uppercase tracking-wider"
          >
            ABORT
          </button>
        </div>
      </motion.div>
    </div>
  )
}
