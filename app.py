import streamlit as st
import time
from dotenv import load_dotenv
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MediaMind AI Assistant",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@300;400;500;600&display=swap');

/* ── Root Variables — "Control Room" palette ── */
:root {
    --bg: #0b0d10;
    --bg-2: #0e1114;
    --surface: #14171c;
    --surface-2: #1b1f26;
    --border: #262b33;
    --border-soft: #1e222a;
    --accent: #ff6a39;         /* tally-light amber */
    --accent-dim: #c9501f;
    --accent-2: #4fd6c4;       /* console teal */
    --accent-3: #8f7bff;       /* signal violet, used sparingly */
    --text: #edeef1;
    --text-muted: #828993;
    --text-faint: #52596a;
    --success: #45d19a;
    --warning: #f5b042;
    --danger: #ff5c5c;
}

/* ── Global Reset ── */
html, body, [class*="css"] {
    font-family: 'JetBrains Mono', monospace;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

.stApp { background: var(--bg) !important; }

/* Faint scanline / grid texture, plus a soft radial glow anchored top-left */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-image:
        radial-gradient(circle at 12% 8%, rgba(255,106,57,0.07), transparent 40%),
        radial-gradient(circle at 88% 92%, rgba(79,214,196,0.05), transparent 45%),
        linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
    background-size: auto, auto, 44px 44px, 44px 44px;
    pointer-events: none;
    z-index: 0;
}

section.main > div { position: relative; z-index: 1; }

/* ── Sidebar — "Control Deck" ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--surface) 0%, var(--bg-2) 100%) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebar"] .block-container { padding-top: 1.6rem; }

/* ── Headings ── */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Space Grotesk', sans-serif !important;
    color: var(--text) !important;
}

/* ── Deck brand mark ── */
.deck-brand {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.15rem;
}
.deck-brand-mark {
    width: 34px; height: 34px;
    border-radius: 9px;
    background: linear-gradient(135deg, var(--accent), var(--accent-dim));
    display: flex; align-items: center; justify-content: center;
    font-size: 1.05rem;
    box-shadow: 0 0 18px rgba(255,106,57,0.35);
    flex-shrink: 0;
}
.deck-brand-text {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 1.05rem;
    line-height: 1.15;
    color: var(--text);
}
.deck-brand-sub {
    font-size: 0.62rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--text-faint);
    margin-top: 0.15rem;
}

/* ── Hero ── */
.hero-row {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 1rem;
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(1.9rem, 4vw, 3.1rem);
    font-weight: 700;
    line-height: 1.05;
    margin: 0;
    color: var(--text);
    letter-spacing: -0.01em;
}
.hero-title span { color: var(--accent); }
.hero-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: var(--text-muted);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-top: 0.55rem;
}

/* ── Live status pill ── */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0.85rem;
    border-radius: 999px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-muted);
    white-space: nowrap;
}
.status-pill .dot { width: 7px; height: 7px; border-radius: 50%; }
.status-pill.idle .dot { background: var(--text-faint); }
.status-pill.live .dot { background: var(--accent); box-shadow: 0 0 8px var(--accent); animation: blink 1.1s infinite; }
.status-pill.ready .dot { background: var(--success); box-shadow: 0 0 8px var(--success); }
@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0.25; } }

/* ── Waveform decoration ── */
.waveform { display: flex; align-items: center; gap: 3px; height: 26px; }
.waveform span {
    display: block;
    width: 3px;
    border-radius: 2px;
    background: linear-gradient(180deg, var(--accent), var(--accent-2));
    animation: wave 1.2s ease-in-out infinite;
}
.waveform span:nth-child(1) { height: 40%; animation-delay: 0s; }
.waveform span:nth-child(2) { height: 80%; animation-delay: 0.1s; }
.waveform span:nth-child(3) { height: 55%; animation-delay: 0.2s; }
.waveform span:nth-child(4) { height: 95%; animation-delay: 0.3s; }
.waveform span:nth-child(5) { height: 35%; animation-delay: 0.4s; }
.waveform span:nth-child(6) { height: 70%; animation-delay: 0.5s; }
.waveform span:nth-child(7) { height: 50%; animation-delay: 0.6s; }
@keyframes wave {
    0%, 100% { transform: scaleY(0.4); opacity: 0.6; }
    50% { transform: scaleY(1); opacity: 1; }
}
.waveform.dim span { animation-play-state: paused; opacity: 0.3; }

/* ── Cards ── */
.card {
    background: linear-gradient(180deg, var(--surface) 0%, var(--surface-2) 100%);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.4rem 1.5rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s, transform 0.2s;
}
.card:hover { border-color: var(--border-soft); transform: translateY(-1px); }
.card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 2px;
    background: linear-gradient(90deg, var(--accent-line, var(--accent)), transparent 70%);
}
.card.acc-amber  { --accent-line: var(--accent); }
.card.acc-teal   { --accent-line: var(--accent-2); }
.card.acc-violet { --accent-line: var(--accent-3); }

.card-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.card-content {
    font-size: 0.875rem;
    line-height: 1.75;
    color: var(--text);
}

/* ── Badge ── */
.badge {
    display: inline-block;
    padding: 0.22rem 0.65rem;
    border-radius: 5px;
    font-size: 0.64rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.badge-amber  { background: rgba(255,106,57,0.14); color: var(--accent); border: 1px solid rgba(255,106,57,0.3); }
.badge-teal   { background: rgba(79,214,196,0.12); color: var(--accent-2); border: 1px solid rgba(79,214,196,0.28); }
.badge-violet { background: rgba(143,123,255,0.12); color: var(--accent-3); border: 1px solid rgba(143,123,255,0.28); }
.badge-green  { background: rgba(69,209,154,0.12); color: var(--success); border: 1px solid rgba(69,209,154,0.28); }

/* ── Inputs & Buttons ── */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 9px !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(255,106,57,0.15) !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--accent), var(--accent-dim)) !important;
    color: #14100d !important;
    border: none !important;
    border-radius: 9px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.04em !important;
    padding: 0.65rem 1.5rem !important;
    transition: all 0.2s !important;
    text-transform: uppercase !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 10px 28px rgba(255,106,57,0.35) !important;
}
.stButton > button[kind="secondary"] {
    background: var(--surface-2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
}

/* ── Signal chain (pipeline) ── */
.chain { margin-top: 0.4rem; position: relative; padding-left: 1.2rem; }
.chain-item {
    position: relative;
    padding: 0.55rem 0 0.55rem 0.9rem;
    font-size: 0.76rem;
    color: var(--text-muted);
}
.chain-item::before {
    content: '';
    position: absolute;
    left: -1.2rem; top: 0; bottom: 0;
    width: 1px;
    background: var(--border);
}
.chain-item:first-child::before { top: 50%; }
.chain-item:last-child::before { bottom: 50%; }
.chain-dot {
    position: absolute;
    left: calc(-1.2rem - 3.5px);
    top: 50%;
    transform: translateY(-50%);
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--border);
    z-index: 1;
}
.chain-dot.active { background: var(--accent); box-shadow: 0 0 9px var(--accent); animation: blink 1s infinite; }
.chain-dot.done   { background: var(--success); box-shadow: 0 0 6px var(--success); }
.chain-item.is-done .chain-label { color: var(--text); }
.chain-item.is-active .chain-label { color: var(--accent); font-weight: 600; }

/* ── Chat ── */
.chat-container {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.2rem;
    max-height: 440px;
    overflow-y: auto;
    margin-bottom: 1rem;
}
.chat-msg { margin-bottom: 1.1rem; display: flex; gap: 0.6rem; align-items: flex-start; }
.chat-msg.from-user { flex-direction: row-reverse; }
.chat-avatar {
    width: 26px; height: 26px;
    border-radius: 7px;
    flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.75rem;
}
.chat-avatar.user-avatar { background: rgba(255,106,57,0.15); border: 1px solid rgba(255,106,57,0.3); }
.chat-avatar.bot-avatar  { background: rgba(79,214,196,0.12); border: 1px solid rgba(79,214,196,0.28); }
.chat-col { display: flex; flex-direction: column; gap: 0.2rem; max-width: 78%; }
.chat-msg.from-user .chat-col { align-items: flex-end; }
.chat-label { font-size: 0.6rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; }
.chat-msg.from-user .chat-label { color: var(--accent); }
.chat-msg:not(.from-user) .chat-label { color: var(--accent-2); }
.chat-bubble {
    padding: 0.65rem 1rem;
    border-radius: 12px;
    font-size: 0.85rem;
    line-height: 1.6;
}
.user-bubble { background: rgba(255,106,57,0.1); border: 1px solid rgba(255,106,57,0.22); border-top-right-radius: 3px; }
.bot-bubble  { background: rgba(79,214,196,0.08); border: 1px solid rgba(79,214,196,0.2); border-top-left-radius: 3px; }

/* ── Divider ── */
hr { border: none !important; border-top: 1px solid var(--border) !important; margin: 1.6rem 0 !important; }

/* ── Transcript box ── */
.transcript-box {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.25rem;
    font-size: 0.82rem;
    line-height: 1.85;
    max-height: 320px;
    overflow-y: auto;
    color: var(--text-muted);
    white-space: pre-wrap;
    word-break: break-word;
}

/* ── Empty state ── */
.empty-wrap {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    padding: 4.5rem 2rem; text-align: center;
    border: 1px dashed var(--border);
    border-radius: 18px;
    background: radial-gradient(circle at 50% 0%, rgba(255,106,57,0.05), transparent 60%);
}
.empty-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.5rem; font-weight: 700; color: var(--text);
    margin: 1.2rem 0 0.5rem;
}
.empty-copy { color: var(--text-muted); font-size: 0.85rem; max-width: 400px; line-height: 1.75; }

/* ── Stale Streamlit elements ── */
.stProgress > div > div > div { background: var(--accent) !important; }
.stSpinner > div { border-top-color: var(--accent) !important; }
[data-testid="stMarkdownContainer"] p { color: var(--text) !important; }
label { color: var(--text-muted) !important; font-size: 0.8rem !important; }

/* scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ──────────────────────────────────────────────────────────
for key, default in {
    "result": None,
    "chat_history": [],
    "processing": False,
    "pipeline_done": False,
    "pipeline_steps": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── Helpers ────────────────────────────────────────────────────────────────────
def step_status(steps: dict, key: str) -> str:
    s = steps.get(key, "pending")
    if s == "active":  return "active"
    if s == "done":    return "done"
    return "pending"

def render_chain():
    items = [
        ("audio",      "Audio Processing"),
        ("transcript", "Transcription"),
        ("title",      "Title Generation"),
        ("summary",    "Summarisation"),
        ("extract",    "Extraction"),
        ("rag",        "RAG Engine"),
    ]
    html = '<div class="chain">'
    for key, label in items:
        s = step_status(st.session_state.pipeline_steps, key)
        dot_cls = {"active": "active", "done": "done", "pending": ""}[s]
        item_cls = {"active": "is-active", "done": "is-done", "pending": ""}[s]
        html += f"""
        <div class="chain-item {item_cls}">
            <div class="chain-dot {dot_cls}"></div>
            <span class="chain-label">{label}</span>
        </div>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def waveform_html(dim=False):
    cls = "waveform dim" if dim else "waveform"
    bars = "".join(["<span></span>" for _ in range(7)])
    return f'<div class="{cls}">{bars}</div>'

# ─── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="deck-brand">
        <div class="deck-brand-mark">📡</div>
        <div>
            <div class="deck-brand-text">AI Video<br>Assistant</div>
            <div class="deck-brand-sub">Control Deck</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<span class="badge badge-amber">Input Source</span>', unsafe_allow_html=True)
    source = st.text_input(
        "YouTube URL or File Path",
        placeholder="https://youtube.com/watch?v=... or /path/to/file.mp4",
        label_visibility="collapsed",
    )

    st.markdown('<div style="height:0.6rem"></div>', unsafe_allow_html=True)
    language = st.selectbox("Language", ["english", "hinglish"], index=0)

    st.markdown('<div style="height:0.4rem"></div>', unsafe_allow_html=True)
    run_btn = st.button("⚡  Analyse", use_container_width=True)

    st.markdown("---")
    st.markdown('<span class="badge badge-teal">Signal Chain</span>', unsafe_allow_html=True)
    render_chain()

# ─── Main Area — Header ─────────────────────────────────────────────────────────
if st.session_state.processing:
    pill = '<span class="status-pill live"><span class="dot"></span>Processing</span>'
elif st.session_state.pipeline_done:
    pill = '<span class="status-pill ready"><span class="dot"></span>Ready</span>'
else:
    pill = '<span class="status-pill idle"><span class="dot"></span>Idle</span>'

st.markdown(f"""
<div class="hero-row">
    <div>
        <div class="hero-title">MediaMind AI <span>Assistant</span></div>
        <div class="hero-sub">Transcribe · Summarise · Chat with your meetings</div>
    </div>
    <div style="display:flex;align-items:center;gap:1rem">
        {waveform_html(dim=not st.session_state.processing)}
        {pill}
    </div>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ── Run Pipeline ────────────────────────────────────────────────────────────────
if run_btn:
    if not source.strip():
        st.error("Please enter a YouTube URL or file path.")
    else:
        st.session_state.pipeline_done = False
        st.session_state.processing = True
        st.session_state.result = None
        st.session_state.chat_history = []
        st.session_state.pipeline_steps = {}

        progress_placeholder = st.empty()

        def update_step(key, state):
            st.session_state.pipeline_steps[key] = state

        try:
            with progress_placeholder.container():
                st.info("⚙️ Pipeline running — see the Signal Chain in the sidebar for live status…")

            update_step("audio", "active")
            chunks = process_input(source)
            update_step("audio", "done")

            update_step("transcript", "active")
            transcript = transcribe_all(chunks, language)
            update_step("transcript", "done")

            update_step("title", "active")
            title = generate_title(transcript)
            update_step("title", "done")

            update_step("summary", "active")
            summary = summarize(transcript)
            update_step("summary", "done")

            update_step("extract", "active")
            action_items  = extract_action_items(transcript)
            decisions     = extract_key_decisions(transcript)
            questions     = extract_questions(transcript)
            update_step("extract", "done")

            update_step("rag", "active")
            rag_chain = build_rag_chain(transcript)
            update_step("rag", "done")

            st.session_state.result = {
                "title": title,
                "transcript": transcript,
                "summary": summary,
                "action_items": action_items,
                "key_decisions": decisions,
                "open_questions": questions,
                "rag_chain": rag_chain,
            }
            st.session_state.pipeline_done = True
            st.session_state.processing = False
            progress_placeholder.success("✅ Analysis complete!")
            time.sleep(0.5)
            progress_placeholder.empty()
            st.rerun()

        except Exception as e:
            st.session_state.processing = False
            for k in ["audio","transcript","title","summary","extract","rag"]:
                if st.session_state.pipeline_steps.get(k) == "active":
                    st.session_state.pipeline_steps[k] = "pending"
            progress_placeholder.error(f"❌ Error: {e}")

# ── Results ──────────────────────────────────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result

    # Title banner
    st.markdown(f"""
    <div class="card acc-amber">
        <div class="card-title">📌 Session Title</div>
        <div style="font-family:'Space Grotesk',sans-serif;font-size:1.5rem;font-weight:700;color:var(--text)">
            {r['title']}
        </div>
    </div>""", unsafe_allow_html=True)

    # Top row: summary + transcript
    col1, col2 = st.columns([3, 2], gap="medium")

    with col1:
        st.markdown(f"""
        <div class="card acc-teal">
            <div class="card-title">📋 Summary</div>
            <div class="card-content">{r['summary']}</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        with st.expander("📝 Full Transcript", expanded=False):
            st.markdown(f'<div class="transcript-box">{r["transcript"]}</div>', unsafe_allow_html=True)

    # Second row: action items | decisions | questions
    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        st.markdown(f"""
        <div class="card acc-amber">
            <div class="card-title">✅ Action Items</div>
            <div class="card-content">{r['action_items']}</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="card acc-violet">
            <div class="card-title">🔑 Key Decisions</div>
            <div class="card-content">{r['key_decisions']}</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="card acc-teal">
            <div class="card-title">❓ Open Questions</div>
            <div class="card-content">{r['open_questions']}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── RAG Chat ──────────────────────────────────────────────────────────────
    st.markdown('<div style="font-family:\'Space Grotesk\',sans-serif;font-size:1.2rem;font-weight:700;margin-bottom:1rem">💬 Chat with your Meeting</div>', unsafe_allow_html=True)

    # Chat history display
    if st.session_state.chat_history:
        chat_html = '<div class="chat-container">'
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                chat_html += f"""
                <div class="chat-msg from-user">
                    <div class="chat-avatar user-avatar">🧑</div>
                    <div class="chat-col">
                        <span class="chat-label">You</span>
                        <div class="chat-bubble user-bubble">{msg['content']}</div>
                    </div>
                </div>"""
            else:
                chat_html += f"""
                <div class="chat-msg">
                    <div class="chat-avatar bot-avatar">🤖</div>
                    <div class="chat-col">
                        <span class="chat-label">Assistant</span>
                        <div class="chat-bubble bot-bubble">{msg['content']}</div>
                    </div>
                </div>"""
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="card" style="text-align:center;padding:2rem">
            <div style="font-size:2rem;margin-bottom:0.5rem">💬</div>
            <div style="color:var(--text-muted);font-size:0.85rem">Ask anything about your meeting transcript</div>
        </div>""", unsafe_allow_html=True)

    # Chat input
    chat_col1, chat_col2 = st.columns([5, 1], gap="small")
    with chat_col1:
        user_input = st.text_input("Your question", placeholder="What were the main decisions made?", label_visibility="collapsed")
    with chat_col2:
        send_btn = st.button("Send →", use_container_width=True)

    if send_btn and user_input.strip():
        with st.spinner("Thinking…"):
            answer = ask_question(r["rag_chain"], user_input.strip())
        st.session_state.chat_history.append({"role": "user",      "content": user_input.strip()})
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()

else:
    # Empty state
    st.markdown(f"""
    <div class="empty-wrap">
        {waveform_html(dim=True)}
        <div class="empty-title">Ready to Analyse</div>
        <div class="empty-copy">
            Paste a YouTube URL or local file path in the Control Deck, choose your language, and hit <strong>Analyse</strong> to get started.
        </div>
        <div style="margin-top:2rem;display:flex;gap:0.6rem;flex-wrap:wrap;justify-content:center">
            <span class="badge badge-amber">Transcription</span>
            <span class="badge badge-teal">Summarisation</span>
            <span class="badge badge-violet">RAG Chat</span>
        </div>
    </div>""", unsafe_allow_html=True)
