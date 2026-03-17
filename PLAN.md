# neon pig — Interactive AI Portfolio Website

## Overview
An AI-powered portfolio site where visitors interact with a trained assistant that knows everything about neon pig — services, case studies, team, philosophy, and more. The assistant responds via text and voice.

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Framework | **Next.js 14 (App Router)** | SSR/SEO, API routes, React Server Components |
| Styling | **Tailwind CSS** | Rapid styling, dark-theme friendly for "neon" aesthetic |
| AI | **Claude API (Anthropic SDK)** | Large context window for company knowledge, nuanced conversation |
| Voice Input | **Web Speech API** (browser-native) | No extra dependencies for speech-to-text |
| Voice Output | **Anthropic TTS or Web Speech Synthesis** | Text-to-speech for assistant responses |
| Knowledge Base | **Static markdown/JSON files** (Phase 1) | Simple, version-controlled content |
| Future CMS | **Sanity** (Phase 2) | Headless CMS, great Next.js integration |
| Deployment | **Vercel** | Zero-config Next.js hosting |
| Database | **None initially** | Stateless chat; add Vercel KV later if conversation history is needed |

---

## Architecture

```
┌─────────────────────────────────────────────┐
│                  Frontend                    │
│  Next.js App Router                         │
│  ┌───────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Chat UI   │  │ Voice    │  │ Media    │ │
│  │ Component │  │ Controls │  │ Renderer │ │
│  └─────┬─────┘  └────┬─────┘  └────┬─────┘ │
│        └──────────────┼─────────────┘       │
│                       ▼                      │
│              Streaming API Route             │
└───────────────────────┬─────────────────────┘
                        ▼
┌───────────────────────────────────────────────┐
│              Backend (API Routes)              │
│  /api/chat         — Claude streaming endpoint │
│  /api/tts          — Text-to-speech endpoint   │
│                                                │
│  ┌──────────────────────────┐                  │
│  │  Knowledge Base Loader   │                  │
│  │  Reads /content/*.md     │                  │
│  │  Builds system prompt    │                  │
│  └──────────────────────────┘                  │
└───────────────────────┬───────────────────────┘
                        ▼
              Claude API (Anthropic)
```

---

## Project Structure

```
neon-pig-site/
├── app/
│   ├── layout.tsx              # Root layout, fonts, metadata
│   ├── page.tsx                # Landing/chat page
│   ├── globals.css             # Tailwind + custom neon theme
│   └── api/
│       ├── chat/
│       │   └── route.ts        # Claude streaming chat endpoint
│       └── tts/
│           └── route.ts        # Text-to-speech endpoint
├── components/
│   ├── Chat/
│   │   ├── ChatWindow.tsx      # Main chat container
│   │   ├── MessageBubble.tsx   # Individual message rendering
│   │   ├── InputBar.tsx        # Text input + send button
│   │   └── VoiceButton.tsx     # Mic toggle for voice input
│   ├── MediaRenderer.tsx       # Renders images/videos inline in chat
│   └── ui/                     # Shared UI primitives (button, etc.)
├── lib/
│   ├── claude.ts               # Claude API client + system prompt builder
│   ├── knowledge.ts            # Loads & indexes content files
│   ├── voice.ts                # Web Speech API helpers
│   └── types.ts                # Shared TypeScript types
├── content/                    # Knowledge base (markdown + metadata)
│   ├── company/
│   │   ├── about.md            # About neon pig
│   │   ├── services.md         # Services offered
│   │   ├── ai-philosophy.md    # Your take on AI
│   │   └── operations.md       # How you operate
│   ├── case-studies/
│   │   ├── _index.json         # Case study metadata (images, videos, links)
│   │   ├── project-alpha.md
│   │   └── project-beta.md
│   ├── team/
│   │   ├── _index.json         # Team member metadata (photo, links, role)
│   │   ├── member-1.md
│   │   └── member-2.md
│   └── links.json              # Contact, social, LinkedIn, portfolios
├── public/
│   ├── images/                 # Team photos, case study images
│   └── videos/                 # Case study videos
├── tailwind.config.ts
├── next.config.js
├── package.json
├── tsconfig.json
└── .env.local                  # ANTHROPIC_API_KEY
```

---

## Implementation Plan (Phases)

### Phase 1: Project Setup & Core Chat (Steps 1–5)

**Step 1 — Scaffold Next.js project**
- Initialize Next.js 14 with App Router, TypeScript, Tailwind
- Configure neon-themed color palette in Tailwind (dark bg, neon accents)
- Set up project structure (folders above)

**Step 2 — Build the Chat UI**
- `ChatWindow` — scrollable message list with auto-scroll
- `MessageBubble` — styled differently for user vs assistant
- `InputBar` — text input with send button, enter-to-send
- Streaming text display (word-by-word rendering)
- Mobile-responsive layout

**Step 3 — Claude API Integration**
- `/api/chat/route.ts` — POST endpoint accepting messages array
- Build system prompt from content files:
  - Load all `/content/**/*.md` files at startup
  - Inject company context, personality, and response guidelines
  - Include structured data (team, links, case studies) as JSON in prompt
- Stream responses using Anthropic SDK's `stream` method
- Handle errors gracefully (rate limits, API errors)

**Step 4 — Knowledge Base Content**
- Create content file templates with frontmatter
- Write sample content for each category (company, services, team, case studies)
- Build `knowledge.ts` loader that reads and structures all content
- System prompt instructions for the assistant:
  - Personality: friendly, knowledgeable, on-brand for neon pig
  - Can reference case studies with images/videos
  - Can provide team member info and contact links
  - Stays on topic (neon pig related)

**Step 5 — Media in Chat**
- `MediaRenderer` component for inline images and video embeds
- Assistant can return structured responses with media references
- Parse assistant responses for media markers and render appropriately

---

### Phase 2: Voice Interaction (Steps 6–7)

**Step 6 — Voice Input (Speech-to-Text)**
- `VoiceButton` component using Web Speech API (`SpeechRecognition`)
- Mic toggle with visual feedback (recording indicator)
- Transcribed text feeds into the same chat flow
- Browser compatibility handling (Chrome/Edge primary, fallback message for others)

**Step 7 — Voice Output (Text-to-Speech)**
- `/api/tts/route.ts` — converts assistant text responses to audio
- Option A: Browser Web Speech Synthesis (free, basic quality)
- Option B: External TTS API (ElevenLabs, etc.) for higher quality
- Play/pause controls on assistant messages
- Auto-play option toggle

---

### Phase 3: Polish & Content Management (Steps 8–9)

**Step 8 — Landing Experience & Branding**
- Animated intro/greeting from the assistant
- neon pig logo and branding
- Suggested starter questions (chips/buttons)
- Loading states and transitions
- SEO metadata, Open Graph tags

**Step 9 — CMS Integration (Sanity)**
- Set up Sanity Studio for content management
- Migrate static content files to Sanity schemas
- Real-time content updates without redeployment
- Image/video asset management through Sanity

---

## System Prompt Strategy

The Claude assistant will receive a carefully crafted system prompt:

```
You are the AI assistant for neon pig, an [industry] company.
You speak on behalf of the company with a friendly, knowledgeable tone.

Your knowledge includes:
- Company background, mission, and values
- Detailed service offerings
- Case studies with results and media
- Team member profiles
- Contact information and links

Guidelines:
- Be conversational but professional
- When discussing case studies, offer to show images/videos
- Provide direct links when relevant (LinkedIn, portfolio, contact)
- If asked something outside your knowledge, say so honestly
- Keep responses concise but thorough
- Match the brand voice of neon pig
```

The actual company data gets injected below this as structured context.

---

## Key Decisions Needed from You

1. **Brand details** — Do you have colors, fonts, logo files to use?
2. **Assistant personality** — How should it sound? Casual? Professional? Witty?
3. **Content** — Can you start providing the markdown files / docs about neon pig?
4. **Voice quality** — Browser-native TTS (free, robotic) vs. paid API (natural)?
5. **Domain/hosting** — Do you have a domain? Vercel account?

---

## What's NOT in MVP

- User authentication / accounts
- Conversation history persistence
- Analytics dashboard
- Multi-language support
- Admin panel

These can all be added in later phases.
