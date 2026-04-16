# 🎙️ Kira Voice System - Configuration Guide

## Current Setup (Ready to Use!)

✅ **Voice Input:** Pollinations Whisper Large V3 ($0.00004/sec)  
✅ **Voice Output:** Pollinations TTS (FREE, 6 voices)  
✅ **API Key:** Already configured in backend `.env`  
✅ **Cost:** ~$1.20/month for 1000 voice messages (transcription) + FREE TTS

---

## 🔧 How to Switch TTS Providers

### In `.env.local` (frontend):

```bash
# Change this line to switch providers:
TTS_PROVIDER=pollinations  # Options: "pollinations" | "elevenlabs" | "browser"
```

---

## 🎨 Pollinations TTS - Tweaking Guide

### Available Voices (6 options)

Each voice has a different character:

| Voice | Character | Best For |
|-------|-----------|----------|
| **alloy** | Neutral, balanced | General purpose, default voice |
| **echo** | Warm, friendly | Conversational responses |
| **fable** | Storytelling, expressive | Narratives, creative content |
| **onyx** | Deep, authoritative | Serious topics, technical explanations |
| **nova** | Bright, energetic | Enthusiastic responses, motivation |
| **shimmer** | Soft, gentle | Supportive tone, empathetic responses |

**Change voice:** Edit `.env.local`
```bash
POLLINATIONS_VOICE=echo  # Try different voices!
```

### Speech Speed

```bash
POLLINATIONS_SPEED=1.0  # Range: 0.25 (very slow) to 4.0 (very fast)
```

**Examples:**
- `0.75` - Slower, easier to follow
- `1.0` - Normal speed (default)
- `1.25` - Slightly faster
- `1.5` - Quick, efficient

### Language Support

```bash
POLLINATIONS_LANG=en  # Supports 100+ languages
```

**Popular language codes:**
- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `it` - Italian
- `pt` - Portuguese
- `ru` - Russian
- `zh` - Chinese
- `ja` - Japanese
- `ko` - Korean
- `ar` - Arabic
- `hi` - Hindi

### Per-Message Override

You can override voice, language, and speed for individual messages through the API:

```typescript
// In your code:
await apiTTS("Hello!", {
  token: userToken,
  voiceId: "echo",  // Override voice
  model: "es",      // Override language (speak in Spanish!)
  speed: 1.2        // Override speed
})
```

---

## 🌟 ElevenLabs TTS (Premium Quality)

### Setup

1. Get API key: https://elevenlabs.io → Account → API Keys
2. Update `.env.local`:

```bash
TTS_PROVIDER=elevenlabs
ELEVENLABS_API_KEY=your_actual_key_here
ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB  # Adam voice
ELEVENLABS_MODEL=eleven_multilingual_v2
```

### Voice Quality Comparison

| Feature | Pollinations | ElevenLabs |
|---------|-------------|------------|
| Quality | ⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Best |
| Cost | FREE | ~$5-22/month |
| Realism | Standard | Neural, human-like |
| Voice Cloning | ❌ No | ✅ Yes |
| Emotion Control | ❌ No | ✅ Yes |
| Setup | Instant | Requires API key |

### When to Use ElevenLabs
- Professional presentations
- Customer-facing applications
- Voice cloning needs
- Maximum realism required

---

## 🎛️ Advanced Tweaking

### Backend Environment Variables

In your backend `.env` file (same as frontend):

```bash
# Provider selection
TTS_PROVIDER=pollinations

# Pollinations settings
POLLINATIONS_VOICE=alloy
POLLINATIONS_SPEED=1.0
POLLINATIONS_LANG=en

# ElevenLabs settings (if using that provider)
ELEVENLABS_API_KEY=your_key
ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB
ELEVENLABS_MODEL=eleven_multilingual_v2
```

**⚠️ Important:** After changing backend `.env`, restart your backend server!

### Frontend Environment Variables

In `.env.local`:

```bash
TTS_PROVIDER=pollinations
POLLINATIONS_VOICE=alloy
POLLINATIONS_SPEED=1.0
POLLINATIONS_LANG=en
ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB
```

**⚠️ Important:** After changing `.env.local`, restart your Next.js dev server!

---

## 🎯 What to Expect

### With Pollinations (Current Setup)

**Pros:**
✅ Completely free - no billing, no limits
✅ No API key needed - works immediately
✅ Good quality voices for most use cases
✅ 100+ language support
✅ Fast response times (~1-3 seconds)

**Cons:**
⚠️ Less realistic than ElevenLabs (sounds more "robotic")
⚠️ No voice cloning
⚠️ Limited emotion/tone control
⚠️ 6 voice options only

### Audio Quality

You should expect:
- **Clear, understandable speech** - not perfect, but very usable
- **Natural pacing** - especially at 1.0 speed
- **Decent intonation** - good for information delivery
- **Not quite human-level** - will sound like a good TTS system, not a real person

---

## 🚀 Testing Your Setup

### 1. Check Backend is Running

```bash
# Your backend should be running on http://localhost:8000
```

### 2. Test TTS Endpoint

You can test directly in your browser console:

```javascript
// Get your auth token first (check localStorage or your auth system)
const token = "your_jwt_token_here";

// Test the TTS endpoint
fetch("http://localhost:8000/tts", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
  },
  body: JSON.stringify({
    text: "Hello! I'm Kira, your AI assistant.",
    voice_id: "alloy",
    speed: 1.0
  })
})
.then(res => res.blob())
.then(blob => {
  const audio = new Audio(URL.createObjectURL(blob));
  audio.play();
})
```

### 3. Test in UI

1. Start your frontend: `npm run dev`
2. Chat with Kira
3. Click the 🔊 speaker icon on any Kira message
4. You should hear the response read aloud!

---

## 🎨 Creative Use Cases

### 1. Multilingual Kira

Switch languages on the fly:

```typescript
// Speak in Spanish
await apiTTS("¡Hola! ¿Cómo estás?", {
  token,
  voiceId: "echo",
  model: "es"  // Spanish
})

// Speak in French
await apiTTS("Bonjour! Comment allez-vous?", {
  token,
  voiceId: "fable",
  model: "fr"  // French
})
```

### 2. Mood-Based Voice Selection

```typescript
const getVoiceForMood = (mood: string) => {
  switch(mood) {
    case 'serious': return 'onyx';
    case 'happy': return 'nova';
    case 'empathetic': return 'shimmer';
    case 'creative': return 'fable';
    default: return 'alloy';
  }
}
```

### 3. Speed for Content Type

```typescript
const getSpeedForContent = (type: string) => {
  switch(type) {
    case 'technical': return 0.8;   // Slower for complex info
    case 'casual': return 1.0;      // Normal speed
    case 'summary': return 1.3;     // Faster for quick updates
    case 'story': return 0.9;       // Slightly slower for narratives
    default: return 1.0;
  }
}
```

---

## 🐛 Troubleshooting

### "TTS failed" Error

**Check:**
1. Backend server is running (`http://localhost:8000`)
2. `TTS_PROVIDER` is set correctly in backend `.env`
3. For ElevenLabs: API key is valid and has credits

### No Sound Playing

**Check:**
1. Browser volume is up
2. Check browser console for errors
3. Verify audio blob is being received (Network tab)

### Voice Sounds Wrong

**Fix:**
- Change `POLLINATIONS_VOICE` to try different voices
- Check if language code matches your text
- Adjust speed if too fast/slow

### Changes Not Taking Effect

**Remember:**
- Backend `.env` changes → Restart backend server
- Frontend `.env.local` changes → Restart Next.js dev server
- Browser cache → Hard refresh (Ctrl+Shift+R)

---

## 📊 Performance Comparison

### Response Times (Approximate)

| Provider | Short Text (<50 chars) | Medium (100-200) | Long (500+) |
|----------|----------------------|------------------|-------------|
| Pollinations | ~1-2 seconds | ~2-4 seconds | ~4-8 seconds |
| ElevenLabs | ~0.5-1 second | ~1-2 seconds | ~2-4 seconds |
| Browser TTS | Instant | Instant | Instant |

### Cost Estimation

| Provider | Cost per 1K chars | Monthly Cost (1000 messages) |
|----------|------------------|------------------------------|
| Pollinations | FREE | $0 |
| ElevenLabs | ~$0.30 | ~$30 |
| Browser | FREE | $0 |

---

## 🎓 Summary

**You're all set with Pollinations!**

- ✅ No API key needed
- ✅ Works immediately
- ✅ 6 voices to choose from
- ✅ 100+ languages
- ✅ Adjustable speed (0.25x to 4.0x)

**To tweak:**
1. Edit `.env.local` for frontend preferences
2. Edit backend `.env` for server settings
3. Restart servers after changes
4. Test by clicking speaker icon on Kira messages

**Want better quality?**
- Switch to ElevenLabs by changing `TTS_PROVIDER=elevenlabs`
- Add your API key
- Restart backend

Enjoy your voice-enabled Kira! 🎙️✨
