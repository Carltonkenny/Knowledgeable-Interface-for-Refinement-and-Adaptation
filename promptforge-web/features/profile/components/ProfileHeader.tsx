'use client'

import { useState } from 'react'
import { MapPin, Link as LinkIcon, Edit2, Check, X, Github, Twitter, Linkedin, Camera } from 'lucide-react'
import { motion } from 'framer-motion'
import AvatarPicker from '@/components/AvatarPicker'

interface ProfileHeaderProps {
  email: string
  username?: string | null
  bio?: string | null
  location?: string | null
  website?: string | null
  github?: string | null
  twitter?: string | null
  linkedin?: string | null
  avatar_url?: string | null
  job_title?: string | null
  company?: string | null
  tier: string
  trustLevel: number
  isEditing?: boolean
  onSave?: (data: Partial<ProfileHeaderProps>) => Promise<void>
}

const tierColors: Record<string, string> = {
  Bronze: 'from-orange-500 to-orange-400 shadow-[0_0_15px_rgba(249,115,22,0.6)]',
  Silver: 'from-slate-300 to-slate-200 shadow-[0_0_15px_rgba(203,213,225,0.6)]',
  Gold: 'from-yellow-400 to-yellow-300 shadow-[0_0_15px_rgba(250,204,21,0.6)]',
  Kira: 'from-kira to-kira-dim shadow-[0_0_20px_rgba(var(--color-kira),0.8)]'
}

export default function ProfileHeader({
  email,
  username,
  bio,
  location,
  website,
  github,
  twitter,
  linkedin,
  avatar_url,
  job_title,
  company,
  tier = 'Bronze',
  trustLevel,
  isEditing = false,
  onSave
}: ProfileHeaderProps) {
  const [editMode, setEditMode] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [showAvatarPicker, setShowAvatarPicker] = useState(false)
  const [editData, setEditData] = useState({
    username: username || '',
    bio: bio || '',
    location: location || '',
    website: website || '',
    github: github || '',
    twitter: twitter || '',
    linkedin: linkedin || '',
    job_title: job_title || ''
  })

  const handleSave = async () => {
    if (onSave) {
      setIsSaving(true)
      try {
        // Convert empty strings to null so backend ignores them
        const cleaned = Object.fromEntries(
          Object.entries(editData).map(([k, v]) => [k, v === '' ? null : v])
        )
        await onSave(cleaned)
        setEditMode(false)
      } finally {
        setIsSaving(false)
      }
    }
  }

  const handleCancel = () => {
    setEditData({
      username: username || '',
      bio: bio || '',
      location: location || '',
      website: website || '',
      github: github || '',
      twitter: twitter || '',
      linkedin: linkedin || '',
      job_title: job_title || ''
    })
    setEditMode(false)
  }

  const trustLabels = ['Onboarding', 'Active', 'Synced']
  const trustColors = ['bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.6)]', 'bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.6)]', 'bg-kira shadow-[0_0_15px_rgba(var(--color-kira),1)]']

  return (
    <div className="bg-layer2/40 backdrop-blur-xl rounded-3xl border border-border-default/50 overflow-hidden relative shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
      {/* Cover Image - Holographic Sweep */}
      <div className="h-36 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-kira/30 via-layer1/20 to-transparent relative animate-[pulse_4s_ease-in-out_infinite]">
        <div className="absolute inset-0 opacity-10 mix-blend-screen" style={{ backgroundImage: 'linear-gradient(to right, rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.1) 1px, transparent 1px)', backgroundSize: '30px 30px' }} />
        <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-layer2/40 to-transparent" />
      </div>

      {/* Profile Info */}
      <div className="px-6 pb-6 relative">
        {/* Avatar & Basic Info */}
        <div className="flex items-end gap-4 -mt-16 mb-4">
          <div className="relative z-10 group">
            <div className="w-28 h-28 rounded-2xl border border-border-default/50 bg-layer1/60 backdrop-blur-md flex items-center justify-center text-4xl font-bold text-text-bright shadow-[0_0_30px_rgba(0,0,0,0.8)] overflow-hidden cursor-pointer hover:border-kira/50 transition-all"
              onClick={() => setShowAvatarPicker(true)}
            >
              {avatar_url ? (
                <img src={avatar_url} alt={username || 'User'} className="w-full h-full object-cover rounded-2xl" />
              ) : (
                <span className="bg-gradient-to-br from-text-bright to-text-dim bg-clip-text text-transparent">{(username || email || 'U')[0].toUpperCase()}</span>
              )}
              {/* Camera Overlay */}
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
                <Camera size={24} className="text-white" />
              </div>
            </div>
            <div className={`absolute -bottom-2 -right-2 w-8 h-8 rounded-full bg-gradient-to-br ${tierColors[tier]} border border-layer1 flex items-center justify-center`} />
          </div>

          <div className="flex-1 pb-3">
            <div className="flex items-center gap-2 mb-1">
              <h1 className="text-2xl font-bold text-text-bright">
                {username || email?.split('@')[0] || 'User'}
              </h1>
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold text-white bg-gradient-to-br ${tierColors[tier]}`}>
                {tier.toUpperCase()}
              </span>
            </div>
            <p className="text-sm text-text-dim">
              {job_title || 'Prompt Engineer'} {company && `at ${company}`}
            </p>
          </div>

          {!editMode && onSave && (
            <button
              onClick={() => setEditMode(true)}
              className="flex items-center gap-2 px-4 py-2 rounded-xl border-2 border-kira/40 bg-kira/10 text-kira font-bold text-sm hover:bg-kira/20 hover:border-kira/60 hover:shadow-[0_0_15px_rgba(var(--color-kira),0.3)] transition-all uppercase tracking-wider"
              title="Edit profile"
            >
              <Edit2 size={14} />
              EDIT
            </button>
          )}
        </div>

        {/* Identity & Bio Section */}
        {editMode ? (
          <div className="space-y-4 mb-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] uppercase tracking-widest text-kira font-bold">Username</label>
              <input
                value={editData.username}
                onChange={(e) => setEditData({ ...editData, username: e.target.value })}
                className="w-full bg-layer1/50 border border-kira/30 rounded-xl px-4 py-3 text-sm text-text-bright font-mono focus:outline-none focus:border-kira focus:ring-1 focus:ring-kira/50 backdrop-blur-sm transition-all shadow-[inset_0_0_15px_rgba(0,0,0,0.5)]"
                placeholder="Enter username..."
              />
            </div>
            
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] uppercase tracking-widest text-kira font-bold">About & Bio</label>
              <textarea
                value={editData.bio}
                onChange={(e) => setEditData({ ...editData, bio: e.target.value })}
                className="w-full h-24 bg-layer1/50 border border-kira/30 rounded-xl p-3 text-sm text-kira font-mono shadow-[inset_0_0_15px_rgba(0,0,0,0.5)] resize-none focus:outline-none focus:border-kira focus:ring-1 focus:ring-kira/50 backdrop-blur-sm transition-all placeholder:text-kira/30"
                placeholder="Tell the community about your expertise and style..."
                maxLength={500}
              />
            </div>
          </div>
        ) : (
          <p className="text-sm text-text-muted mb-4">
            {bio || 'No bio yet. Click edit to add one.'}
          </p>
        )}

        {/* Meta Info */}
        <div className="flex flex-wrap gap-4 text-xs text-text-dim mb-4">
          {editMode ? (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-4">
              <input
                value={editData.location}
                onChange={(e) => setEditData({ ...editData, location: e.target.value })}
                className="bg-layer1/50 border border-kira/30 rounded-md px-3 py-1.5 text-xs text-kira font-mono shadow-[inset_0_0_10px_rgba(0,0,0,0.5)] focus:outline-none focus:border-kira focus:ring-1 focus:ring-kira/50 w-32 placeholder:text-kira/30"
                placeholder="City, Country"
              />
              <input
                value={editData.job_title}
                onChange={(e) => setEditData({ ...editData, job_title: e.target.value })}
                className="bg-layer1/50 border border-kira/30 rounded-md px-3 py-1.5 text-xs text-kira font-mono shadow-[inset_0_0_10px_rgba(0,0,0,0.5)] focus:outline-none focus:border-kira focus:ring-1 focus:ring-kira/50 w-40 placeholder:text-kira/30"
                placeholder="e.g. Software Engineer"
              />
            </motion.div>
          ) : (
            <>
              {location && (
                <div className="flex items-center gap-1">
                  <MapPin size={12} />
                  <span>{location}</span>
                </div>
              )}
              {website && (
                <a href={website} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 hover:text-kira transition-colors">
                  <LinkIcon size={12} />
                  <span>{website.replace(/^https?:\/\//, '')}</span>
                </a>
              )}
            </>
          )}
        </div>

        {/* Social Links */}
        <div className="flex items-center gap-3 mb-4">
          {editMode ? (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-wrap gap-3">
              <input
                value={editData.github}
                onChange={(e) => setEditData({ ...editData, github: e.target.value })}
                className="bg-layer1/50 border border-kira/30 rounded-md px-3 py-1.5 text-xs text-kira font-mono shadow-[inset_0_0_10px_rgba(0,0,0,0.5)] focus:outline-none focus:border-kira focus:ring-1 focus:ring-kira/50 w-40 placeholder:text-kira/30"
                placeholder="github-username"
              />
              <input
                value={editData.twitter}
                onChange={(e) => setEditData({ ...editData, twitter: e.target.value })}
                className="bg-layer1/50 border border-kira/30 rounded-md px-3 py-1.5 text-xs text-kira font-mono shadow-[inset_0_0_10px_rgba(0,0,0,0.5)] focus:outline-none focus:border-kira focus:ring-1 focus:ring-kira/50 w-40 placeholder:text-kira/30"
                placeholder="@handle"
              />
              <input
                value={editData.linkedin}
                onChange={(e) => setEditData({ ...editData, linkedin: e.target.value })}
                className="bg-layer1/50 border border-kira/30 rounded-md px-3 py-1.5 text-xs text-kira font-mono shadow-[inset_0_0_10px_rgba(0,0,0,0.5)] focus:outline-none focus:border-kira focus:ring-1 focus:ring-kira/50 w-40 placeholder:text-kira/30"
                placeholder="linkedin.com/in/yourname"
              />
            </motion.div>
          ) : (
            <>
              {github && (
                <a href={`https://github.com/${github}`} target="_blank" rel="noopener noreferrer" className="p-2 rounded-lg hover:bg-layer3 text-text-dim hover:text-text-bright transition-colors">
                  <Github size={16} />
                </a>
              )}
              {twitter && (
                <a href={`https://twitter.com/${twitter}`} target="_blank" rel="noopener noreferrer" className="p-2 rounded-lg hover:bg-layer3 text-text-dim hover:text-text-bright transition-colors">
                  <Twitter size={16} />
                </a>
              )}
              {linkedin && (
                <a href={linkedin} target="_blank" rel="noopener noreferrer" className="p-2 rounded-lg hover:bg-layer3 text-text-dim hover:text-text-bright transition-colors">
                  <Linkedin size={16} />
                </a>
              )}
            </>
          )}
        </div>

        {/* Trust Level & Email */}
        <div className="flex items-center justify-between pt-4 border-t border-border-subtle">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1">
              <div className={`w-2 h-2 rounded-full ${trustColors[trustLevel]} ${trustLevel === 2 ? 'animate-pulse' : ''}`} />
              <span className={`text-[10px] font-mono font-bold ${trustLevel === 2 ? 'text-kira' : 'text-text-dim'}`}>
                {trustLabels[trustLevel]}
              </span>
            </div>
            <span className="text-[10px] text-text-dim">•</span>
            <span className="text-[10px] text-text-dim">{email}</span>
          </div>

          {editMode && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="flex items-center gap-3">
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-kira/20 border border-kira text-kira text-xs font-bold hover:bg-kira hover:text-white hover:shadow-[0_0_15px_rgba(var(--color-kira),0.8)] transition-all uppercase tracking-wider disabled:opacity-50 disabled:cursor-not-allowed"
              >
                    SAVING
                  </>
                ) : (
                  <>
                    <Check size={14} />
                    SAVE
                  </>
                )}
              </button>
              <button
                onClick={handleCancel}
                disabled={isSaving}
                className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-layer3/50 text-text-dim text-xs font-bold hover:bg-layer3 hover:text-text-bright transition-all uppercase tracking-wider disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <X size={14} />
                CANCEL
              </button>
            </motion.div>
          )}
        </div>
      </div>

      {/* Avatar Picker Modal */}
      {showAvatarPicker && (
        <AvatarPicker
          currentAvatar={avatar_url}
          onSelect={(url) => {
            if (onSave) {
              onSave({ avatar_url: url })
            }
            setShowAvatarPicker(false)
          }}
          onClose={() => setShowAvatarPicker(false)}
        />
      )}
    </div>
  )
}
