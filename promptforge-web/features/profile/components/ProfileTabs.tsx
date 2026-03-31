'use client'

import { useState } from 'react'
import { User, Activity, Settings, Shield } from 'lucide-react'
import { motion } from 'framer-motion'

type TabId = 'overview' | 'activity' | 'settings' | 'security'

interface ProfileTabsProps {
  activeTab?: TabId
  onTabChange?: (tab: TabId) => void
}

const tabs: { id: TabId; label: string; icon: any }[] = [
  { id: 'overview', label: 'Overview', icon: User },
  { id: 'activity', label: 'Activity', icon: Activity },
  { id: 'settings', label: 'Settings', icon: Settings },
  { id: 'security', label: 'Security', icon: Shield },
]

export default function ProfileTabs({ activeTab = 'overview', onTabChange }: ProfileTabsProps) {
  const [currentTab, setCurrentTab] = useState<TabId>(activeTab)

  const handleTabClick = (tabId: TabId) => {
    setCurrentTab(tabId)
    onTabChange?.(tabId)
  }

  return (
    <div className="bg-layer2/40 backdrop-blur-md rounded-2xl border border-border-default/50 p-2 mb-6 shadow-xl">
      <div className="flex flex-wrap items-center gap-2">
        {tabs.map((tab) => {
          const Icon = tab.icon
          const isActive = currentTab === tab.id
          
          return (
            <button
              key={tab.id}
              onClick={() => handleTabClick(tab.id)}
              className={`relative flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-colors z-10 ${
                isActive ? 'text-kira' : 'text-text-dim hover:text-text-bright hover:bg-layer3/50'
              }`}
            >
              {isActive && (
                <motion.div
                  layoutId="activeProfileTab"
                  className="absolute inset-0 bg-kira/10 border border-kira/30 rounded-xl -z-10 shadow-[0_0_15px_rgba(var(--color-kira),0.15)]"
                  transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                />
              )}
              <Icon size={16} className={isActive ? "animate-pulse" : ""} />
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
