# neon pig — Interactive AI Portfolio Website

## Overview
A voice-first, full-screen conversational portfolio for neon pig. There is no traditional website navigation — the AI assistant IS the interface. Visitors talk to it (text or voice), and it responds with rich content: text, image grids, case study cards, team profiles, and links. The entire experience is black & white, monospace, and minimal.

---

## Design Language (from screens)

| Element | Style |
|---------|-------|
| Background | Pure black `#000000` |
| Text | White `#FFFFFF`, all **uppercase**, **monospace**, **wide letter-spacing** (tracking) |
| Logo | Small wireframe pig head + "neon pig" in script font, top-left on all screens |
| AI messages | Left-aligned, no bubbles, just typed text on black |
| User messages | Right-aligned, same monospace style |
| Buttons | Hand-drawn/rough white border (brushstroke aesthetic) |
| Voice circle | Enso (zen brushstroke circle) with mic icon, center screen |
| Media cards | Full-bleed images in a row, with label + bold title below |
| Loading | Full-screen logo animation + "LOADING" text |
| Accent style | No color — only black, white, and the glow/neon effect on the logo |

### Typography Rules
- ALL body text: monospace, uppercase, wide letter-spacing (~0.2-0.3em)
- Logo "neon pig": handwritten/script font
- Case study titles: monospace, bold, larger size
- No sentence case anywhere — everything is uppercase

### Screen States
1. **Splash/Loading** — Full-screen neon pig logo (geometric wireframe pig with glow) + "LOADING"
2. **Welcome** — AI greeting with intro text + topic suggestion links (THE COMPANY, CASE STUDIES, THE TEAM BEHIND, THE TECHNOLOGY, ETHICAL TAKE)
3. **Voice Listening** — Full-screen enso circle with mic icon + "TELL ME, HOW CAN I HELP YOU TODAY?"
4. **Conversation** — Messages flowing top-to-bottom, AI renders rich content (image grids, cards) inline
5. **Case Study Detail** — AI presents project with hero image, title, description

### Persistent Elements (all screens except splash)
- **Top-left**: Small logo watermark
- **Bottom-right**: `SAY "HELLO, PIG" OR` + `[ PRESS TO TALK ]` button (rough border)

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Framework | **Next.js 14 (App Router)** | SSR/SEO, API routes, streaming |
| Styling | **Tailwind CSS** | Utility-first, easy to enforce the strict B&W monospace system |
| Fonts | **Custom monospace** (e.g., Space Mono / IBM Plex Mono) + **script font** for logo | Match the design |
| AI | **Claude API (Anthropic SDK)** | Large context, nuanced conversation, structured output |
| Voice Input | **Web Speech API** (browser-native) | Speech-to-text, zero dependencies |
| Voice Output | **TTS API** (TBD: browser-native or ElevenLabs) | Text-to-speech for responses |
| Wake Word | **"HELLO, PIG"** via continuous speech recognition | Voice activation |
| Knowledge Base | **Static markdown/JSON** (Phase 1) → **Sanity CMS** (Phase 2) | Version-controlled then manageable |
| Animation | **Framer Motion** | Smooth transitions between screen states, typewriter effects |
| Deployment | **Vercel** | Zero-config Next.js |

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    Frontend (Single Page)              │
│                                                        │
│  ┌─────────┐  ┌───────────┐  ┌──────────┐            │
│  │ Screen   │  │ Message   │  │ Voice    │            │
│  │ Manager  │  │ Renderer  │  │ Engine   │            │
│  │ (states) │  │ (rich)    │  │ (STT+TTS)│            │
│  └────┬─────┘  └─────┬─────┘  └────┬─────┘            │
│       └───────────────┼─────────────┘                  │
│                       ▼                                │
│            Conversation Controller                     │
│     (manages messages, screen state, AI calls)         │
└───────────────────────┬──────────────────────────────┘
                        ▼
┌──────────────────────────────────────────────────────┐
│                Backend (API Routes)                    │
│                                                        │
│  POST /api/chat    → Claude streaming + knowledge base │
│  POST /api/tts     → Text-to-speech (optional)         │
│                                                        │
│  Knowledge Base Loader:                                │
│    Reads /content/**/*.md + JSON metadata              │
│    Builds system prompt with company data              │
│    Instructs Claude to return structured responses     │
│    (text + media markers for frontend rendering)       │
└───────────────────────┬──────────────────────────────┘
                        ▼
                 Claude API (Anthropic)
```

### Structured Response Format

Claude returns JSON-structured responses so the frontend can render rich content:

```json
{
  "type": "message",
  "content": [
    { "type": "text", "value": "THATS GREAT, HERE ARE THE 3 AVAILABLE CASE STUDIES..." },
    {
      "type": "case_study_grid",
      "items": [
        { "id": "kia-ev3", "title": "KIA EV3", "label": "FULL AI CAMPAIGN FOR", "image": "/images/cases/kia-ev3.jpg" },
        { "id": "hyundai-tucson", "title": "HYUNDAI TUCSON", "label": "HYBRID FILM/AI FOR", "image": "/images/cases/hyundai.jpg" },
        { "id": "jeep", "title": "JEEP", "label": "FULL AI CAMPAIGN FOR", "image": "/images/cases/jeep.jpg" }
      ]
    }
  ]
}
```

The frontend parses this and renders the appropriate components (text blocks, image grids, team cards, etc.).

---

## Project Structure

```
neon-pig-site/
├── app/
│   ├── layout.tsx                # Root layout, fonts, metadata, black bg
│   ├── page.tsx                  # Single-page app entry
│   ├── globals.css               # Tailwind + monospace uppercase system
│   └── api/
│       ├── chat/
│       │   └── route.ts          # Claude streaming endpoint
│       └── tts/
│           └── route.ts          # Text-to-speech endpoint
├── components/
│   ├── SplashScreen.tsx          # Full-screen loading animation (logo + glow)
│   ├── Conversation.tsx          # Main conversation view (message list)
│   ├── MessageRenderer.tsx       # Renders a single AI/user message
│   ├── RichContent/
│   │   ├── CaseStudyGrid.tsx     # 3-column image card grid (screen 4)
│   │   ├── CaseStudyDetail.tsx   # Single case study view (screen 5)
│   │   ├── TopicLinks.tsx        # Clickable topic suggestions (screen 2)
│   │   ├── TeamGrid.tsx          # Team member cards
│   │   └── ImageBlock.tsx        # Single image renderer
│   ├── VoiceOverlay.tsx          # Full-screen voice mode (enso circle + mic)
│   ├── VoiceButton.tsx           # Persistent "PRESS TO TALK" button (bottom-right)
│   ├── Logo.tsx                  # Persistent top-left logo watermark
│   └── TypewriterText.tsx        # Animated text typing effect
├── lib/
│   ├── claude.ts                 # Claude client, system prompt builder, response parser
│   ├── knowledge.ts              # Loads content files into structured data
│   ├── voice.ts                  # Web Speech API: recognition + synthesis + wake word
│   ├── conversation.ts           # Conversation state machine (splash → welcome → chat → voice)
│   └── types.ts                  # TypeScript types (Message, RichContent, ScreenState, etc.)
├── content/
│   ├── company/
│   │   ├── about.md              # "AI production company focused on leveraging human creativity..."
│   │   ├── services.md
│   │   ├── ai-philosophy.md      # Your take on AI
│   │   └── operations.md
│   ├── case-studies/
│   │   ├── _index.json           # { id, title, label, image, video, description }
│   │   ├── kia-ev3.md
│   │   ├── hyundai-tucson.md
│   │   └── jeep.md
│   ├── team/
│   │   ├── _index.json           # { name, role, photo, linkedin, portfolio, email }
│   │   └── [member].md
│   ├── technology.md             # THE TECHNOLOGY topic
│   ├── ethics.md                 # ETHICAL TAKE topic
│   └── links.json                # All contact/social/LinkedIn/portfolio links
├── public/
│   ├── logo.svg                  # Wireframe pig head (small watermark version)
│   ├── logo-full.svg             # Full geometric pig + "neon pig" text (splash screen)
│   ├── enso-circle.svg           # Brushstroke circle for voice mode
│   ├── images/
│   │   ├── cases/                # Case study photos
│   │   └── team/                 # Team member photos
│   └── fonts/                    # Custom monospace + script fonts
├── tailwind.config.ts
├── next.config.js
├── package.json
├── tsconfig.json
└── .env.local                    # ANTHROPIC_API_KEY
```

---

## Implementation Plan

### Phase 1: Foundation & Splash (Steps 1-3)

**Step 1 — Project Scaffold & Design System**
- Initialize Next.js 14 with App Router, TypeScript, Tailwind, Framer Motion
- Set up the strict design system in Tailwind config:
  - Colors: only `black` (#000) and `white` (#FFF)
  - Font family: monospace (Space Mono or IBM Plex Mono) + script for logo
  - Letter-spacing utilities for the wide-tracked uppercase text
  - Base styles: all text uppercase, tracked, monospace by default
- Create `Logo` component (SVG placeholder until real assets provided)
- Create `TypewriterText` component for animated text rendering
- Set up project folder structure

**Step 2 — Splash Screen**
- Full-screen black background
- Centered geometric pig logo with subtle white glow/neon animation (CSS glow + fade-in)
- "neon pig" in script font below the logo
- "LOADING" text at bottom with letter-spacing animation
- Auto-transition to welcome screen after 2-3 seconds (or when assets loaded)
- Framer Motion exit animation (fade out)

**Step 3 — Welcome Screen (Static)**
- Logo watermark top-left
- AI greeting text, typed out with typewriter animation:
  > "HI, WE ARE NEON PIG. AN AI PRODUCTION COMPANY FOCUSED ON LEVERAGING HUMAN CREATIVITY AND CRAFT THROUGH AI AND INNOVATIVE TECHNOLOGY SOLUTIONS."
  > "TELL ME, HOW CAN I HELP YOU TODAY? YOU WANT TO KNOW MORE ABOUT:"
- Topic links below (clickable, underlined):
  - THE COMPANY
  - CASE STUDIES
  - THE TEAM BEHIND
  - THE TECHNOLOGY
  - ETHICAL TAKE
- Bottom-right: `SAY "HELLO, PIG" OR [ PRESS TO TALK ]` (static button, not functional yet)
- Clicking a topic link sends it as a user message → transitions to conversation

---

### Phase 2: AI Chat & Rich Content (Steps 4-6)

**Step 4 — Claude API Integration**
- `/api/chat/route.ts`:
  - Accepts conversation history (messages array)
  - Loads knowledge base via `knowledge.ts`
  - Builds system prompt with all company data + response format instructions
  - Streams response from Claude API
  - Claude instructed to return structured JSON for rich content (grids, images, links)
- `conversation.ts` state machine managing screen transitions
- Parse Claude's structured responses into renderable components

**Step 5 — Conversation UI**
- Full-screen conversation view (replaces welcome screen after first interaction)
- AI messages: left-aligned, typewriter animation, white monospace uppercase
- User messages: right-aligned, same style
- No chat bubbles, no borders — just text on black
- Auto-scroll to latest message
- `MessageRenderer` parses structured content and renders appropriate `RichContent` components
- Smooth Framer Motion transitions for new messages appearing

**Step 6 — Rich Content Components**
- `TopicLinks` — the initial suggested topics (underlined, clickable, send as message)
- `CaseStudyGrid` — 3-column image cards (as seen in screen 4):
  - Large thumbnail image
  - Small label text: "FULL AI CAMPAIGN FOR" / "HYBRID FILM/AI FOR"
  - Bold title: "KIA EV3" etc.
  - Clickable → sends selection as user message (e.g., "OPTION 1")
- `CaseStudyDetail` — single case study with hero image, title, description
- `TeamGrid` — team member cards with photos, names, roles
- `ImageBlock` — single image with optional caption
- All components follow the B&W monospace design system

---

### Phase 3: Voice Interaction (Steps 7-8)

**Step 7 — Voice Input & Listening Mode**
- `VoiceButton` (persistent bottom-right):
  - Hand-drawn/rough white border (CSS or SVG brushstroke)
  - Clicking opens full-screen voice overlay
- `VoiceOverlay` (screen 3):
  - Full-screen black with centered enso/brushstroke circle SVG
  - Mic icon with sound wave indicators inside the circle
  - "TELL ME, HOW CAN I HELP YOU TODAY?" text at bottom
  - Pulsing animation while listening
  - Web Speech API `SpeechRecognition` captures speech → converts to text
  - On speech end: close overlay, inject transcribed text as user message
- Wake word detection: continuous low-power speech recognition listening for "HELLO, PIG"
  - When detected → open voice overlay automatically
- Browser compatibility: Chrome/Edge primary, graceful fallback message for others

**Step 8 — Voice Output (TTS)**
- AI responses spoken aloud when in voice mode
- Option A (MVP): Browser Web Speech Synthesis API
- Option B (upgrade): ElevenLabs or similar for natural voice
- Audio plays while typewriter text animates (synchronized)
- User can interrupt by speaking or clicking

---

### Phase 4: Polish & CMS (Steps 9-10)

**Step 9 — Animations, Transitions & Mobile**
- Smooth screen state transitions (splash → welcome → conversation → voice)
- Typewriter text speed tuning
- Image loading states (fade-in)
- Mobile responsive:
  - Stack case study cards vertically on mobile
  - Voice button repositioned for thumb reach
  - Touch-friendly topic links
- SEO: metadata, Open Graph tags, structured data
- Performance: image optimization, lazy loading, font preloading

**Step 10 — CMS Integration (Sanity)**
- Set up Sanity Studio with schemas matching content structure
- Schemas: Company Info, Case Study, Team Member, Technology, Ethics
- Migrate static markdown/JSON to Sanity documents
- Update `knowledge.ts` to fetch from Sanity API instead of filesystem
- Image/video assets managed through Sanity CDN
- Content editable without redeployment

---

## System Prompt Strategy

```
You are the AI assistant for neon pig, an AI production company focused on
leveraging human creativity and craft through AI and innovative technology solutions.

PERSONALITY:
- Speak in first person plural ("we") as neon pig
- Confident, knowledgeable, slightly informal but professional
- Direct and concise — match the minimal aesthetic of the brand

RESPONSE FORMAT:
- Return structured JSON responses so the frontend can render rich content
- Available content types: text, topic_links, case_study_grid, case_study_detail,
  team_grid, image, link_list
- Always start with a text block, then add rich content as needed
- When listing case studies, use case_study_grid with images
- When showing a single case study, use case_study_detail
- When discussing team, use team_grid with photos and links

TEXT STYLE:
- Keep text concise — the UI is minimal, long paragraphs won't fit the aesthetic
- Suggest next actions ("select the one you want to see", "or just say 1, 2 or 3")
- Offer to show related content when relevant

BOUNDARIES:
- Only discuss neon pig, its work, team, philosophy, and technology
- If asked about unrelated topics, redirect politely
- If you don't know something, say so honestly

KNOWLEDGE BASE:
[Injected company data, case studies, team info, links, etc.]
```

---

## Assets Needed from You

1. **Logo files** — The geometric wireframe pig SVG (both full splash version and small watermark)
2. **Font choice** — Or I'll use Space Mono (monospace) + a script font for the logo
3. **Case study images** — The actual photos for KIA EV3, Hyundai Tucson, Jeep (and any others)
4. **Team member photos** — Headshots for team grid
5. **Content documents** — Company info, case study details, team bios, philosophy, ethics
6. **Voice preference** — Browser TTS (free, robotic) vs ElevenLabs (natural, paid)
7. **The enso circle** — Do you have the brushstroke SVG, or should I create/source one?

---

## What's NOT in MVP

- User accounts / auth
- Conversation history persistence
- Analytics
- Multi-language
- Admin panel
- Traditional page-based navigation (by design — the AI IS the navigation)
