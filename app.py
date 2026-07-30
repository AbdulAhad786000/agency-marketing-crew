"""
app.py
------
Streamlit web interface for the Agency Marketing Crew.

Runs the same two-agent pipeline as agency_marketing_crew.py but inside
a browser UI — with live activity logging, agent status cards, and a
formatted output panel.

USAGE
-----
  streamlit run app.py

NOTES
-----
- The crew runs synchronously in Streamlit's main thread (no background
  threading). This is intentional — it keeps the code simple and lets
  CrewAI callbacks update the UI in real time.
- API keys are loaded from .env by default but can be overridden in the
  sidebar, so teammates can run it without touching the .env file.
"""

import streamlit as st
import os
import time
from dotenv import load_dotenv

# Page config must come before any other Streamlit call
st.set_page_config(
    page_title="Agency Marketing Crew",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_dotenv()


# ---------------------------------------------------------------------------
# CSS — dark glassmorphism theme
# Using Inter font from Google Fonts for a clean, modern look.
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

/* ── Hero banner ── */
.hero {
    text-align: center;
    padding: 2rem 1rem 1.5rem;
    background: linear-gradient(180deg, rgba(108, 99, 255, 0.12) 0%, transparent 100%);
    border-radius: 20px;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(108, 99, 255, 0.2);
}
.hero h1 {
    font-size: 2.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #a78bfa, #6c63ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 0.4rem;
}
.hero p { color: rgba(255, 255, 255, 0.5); font-size: 1rem; margin: 0; }

/* ── Status bar (4 stat boxes) ── */
.stat-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
.sbox {
    flex: 1;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
}
.sv { font-size: 1.3rem; font-weight: 700; color: #a78bfa; }
.sl { font-size: 0.68rem; color: rgba(255, 255, 255, 0.35); text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.2rem; }

/* ── Agent pipeline cards ── */
.acard {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 14px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 0.8rem;
}
.acard.act {
    border-color: rgba(108, 99, 255, 0.5);
    background: rgba(108, 99, 255, 0.07);
    box-shadow: 0 0 18px rgba(108, 99, 255, 0.13);
}
.acard.dn {
    border-color: rgba(16, 185, 129, 0.35);
    background: rgba(16, 185, 129, 0.05);
}
.ah { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.25rem; }
.an { font-weight: 600; font-size: 0.9rem; color: rgba(255, 255, 255, 0.88); }
.ab {
    font-size: 0.7rem;
    margin-left: auto;
    padding: 0.18rem 0.6rem;
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.06);
    color: rgba(255, 255, 255, 0.35);
}
.ab.run  { color: #a78bfa; background: rgba(167, 139, 250, 0.12); animation: pulse 1.5s ease-in-out infinite; }
.ab.dn   { color: #10b981; background: rgba(16, 185, 129, 0.12); }
.ad { font-size: 0.77rem; color: rgba(255, 255, 255, 0.38); padding-left: 1.9rem; }

/* ── Live activity log ── */
.logbox {
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 1rem;
    min-height: 220px;
    max-height: 300px;
    overflow-y: auto;
    font-family: 'SF Mono', 'Fira Code', monospace;
    font-size: 0.78rem;
    line-height: 1.7;
}
.logbox::-webkit-scrollbar { width: 3px; }
.logbox::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 2px; }
.li.info  { color: rgba(255, 255, 255, 0.5); }
.li.ok    { color: #10b981; }
.li.agent { color: #a78bfa; }
.li.err   { color: #f87171; }

/* ── Output card ── */
.outcard {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 16px;
    padding: 1.8rem;
    margin-top: 1.5rem;
    box-shadow: 0 0 35px rgba(16, 185, 129, 0.07);
}
.obadge {
    display: inline-block;
    background: rgba(16, 185, 129, 0.13);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 20px;
    padding: 0.25rem 0.85rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: #10b981;
    margin-bottom: 1rem;
}
.osubj {
    font-size: 1.05rem;
    font-weight: 700;
    color: white;
    margin-bottom: 0.85rem;
    padding-bottom: 0.7rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
}
.obody { color: rgba(255, 255, 255, 0.75); font-size: 0.9rem; line-height: 1.85; white-space: pre-wrap; }

/* ── "How it works" explainer ── */
.explain {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    margin-top: 0.5rem;
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.45);
    line-height: 1.75;
}
.explain b { color: rgba(255, 255, 255, 0.65); }

/* ── Animated loading dots ── */
.dot {
    display: inline-block;
    width: 7px; height: 7px;
    background: #a78bfa;
    border-radius: 50%;
    margin: 0 2px;
    animation: bop 1s ease-in-out infinite;
}
.dot:nth-child(2) { animation-delay: 0.15s; }
.dot:nth-child(3) { animation-delay: 0.3s; }
@keyframes bop   { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }
@keyframes pulse { 0%, 100% { opacity: 1; }               50% { opacity: 0.45; } }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state initialisation
# We store everything in st.session_state so values survive reruns.
# ---------------------------------------------------------------------------
_defaults = {
    "status":        "idle",   # idle | running | done | error
    "logs":          [],       # list of (type, message) tuples fed to the log panel
    "result":        None,     # final raw output string from the crew
    "error":         None,     # error message if something went wrong
    "research_done": False,    # True once Agent 1 completes
    "content_done":  False,    # True once Agent 2 completes
    "elapsed":       0,        # seconds taken
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ---------------------------------------------------------------------------
# Sidebar — campaign inputs and API keys
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🚀 Agency Marketing Crew")
    st.divider()

    st.markdown("#### 🔑 API Keys")
    groq_key = st.text_input(
        "Groq API Key",
        value=os.getenv("GROQ_API_KEY", ""),
        type="password",
        placeholder="gsk_...",
        help="Free API key → console.groq.com",
    )
    serper_key = st.text_input(
        "Serper API Key",
        value=os.getenv("SERPER_API_KEY", ""),
        type="password",
        placeholder="abc123...",
        help="Free API key → serper.dev",
    )

    st.divider()
    st.markdown("#### ⚙️ Campaign Settings")

    niche = st.text_area(
        "Target Niche",
        value="small and solo US dental clinics",
        height=72,
        help="Who are you marketing to?",
    )
    service = st.text_area(
        "Your Service",
        value=(
            "an AI voice bot (built on Retell AI + Twilio) that answers "
            "every incoming call and books appointments 24/7, even after "
            "hours or when the front desk is busy"
        ),
        height=105,
        help="What are you selling?",
    )
    content_type = st.selectbox(
        "Content Type",
        ["cold outreach email", "LinkedIn post", "Twitter thread", "Instagram caption"],
        help="Format of the output content.",
    )

    st.divider()

    # Disable the button while a run is in progress
    run_btn = st.button(
        "🚀 Generate Content",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.status == "running",
    )

    # Show reset button after a completed (or failed) run
    if st.session_state.status in ("done", "error"):
        if st.button("🔄 New Campaign", use_container_width=True):
            for k, v in _defaults.items():
                st.session_state[k] = v
            st.rerun()

    st.divider()
    st.markdown("""
    <div style='font-size: 0.73rem; color: rgba(255,255,255,0.35); line-height: 1.7;'>
        <b style='color: rgba(255,255,255,0.55)'>How it works</b><br>
        🔍 Agent 1 searches Google for real stats<br>
        ✍️ Agent 2 writes content from that research<br>
        ⚡ Groq (Llama 3.3 70B) · Serper Search API
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main page — hero banner + status bar
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero">
  <h1>🚀 Agency Marketing Crew</h1>
  <p>Two AI agents research your niche and write ready-to-send content in ~30 seconds</p>
</div>
""", unsafe_allow_html=True)

# Four status cards that update throughout the run
status_colors = {"idle": "#6b7280", "running": "#a78bfa", "done": "#10b981", "error": "#f87171"}
status_labels = {"idle": "⬜ Idle", "running": "🟣 Running", "done": "🟢 Done", "error": "🔴 Error"}
ss = st.session_state

st.markdown(f"""
<div class="stat-row">
  <div class="sbox">
    <div class="sv" style="color:{status_colors[ss.status]}">{status_labels[ss.status]}</div>
    <div class="sl">Status</div>
  </div>
  <div class="sbox">
    <div class="sv">{'✅' if ss.research_done else '⏳'}</div>
    <div class="sl">Research Agent</div>
  </div>
  <div class="sbox">
    <div class="sv">{'✅' if ss.content_done else '⏳'}</div>
    <div class="sl">Writer Agent</div>
  </div>
  <div class="sbox">
    <div class="sv">{ss.elapsed}s</div>
    <div class="sl">Elapsed</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Two-column layout
#   Left  — agent pipeline cards + how-it-works explainer
#   Right — live activity log
# ---------------------------------------------------------------------------
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<p style="font-size:.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.1em;color:rgba(255,255,255,.3);margin-bottom:.5rem">🤖 Agent Pipeline</p>', unsafe_allow_html=True)

    r       = ss.research_done
    c       = ss.content_done
    running = ss.status == "running"

    # Agent 1 card — highlights purple while running, green when done
    a1c = "dn" if r else ("act" if running else "")
    a1b = "dn" if r else ("run" if running else "")
    a1l = "✅ Done" if r else ("⚡ Running..." if running else "Waiting")
    st.markdown(f"""
    <div class="acard {a1c}">
      <div class="ah">
        <span style="font-size:1.2rem">🔍</span>
        <span class="an">Market Research Analyst</span>
        <span class="ab {a1b}">{a1l}</span>
      </div>
      <div class="ad">Searches the web for real pain points + statistics about your niche</div>
    </div>""", unsafe_allow_html=True)

    # Agent 2 card — only activates after Agent 1 is done
    a2c = "dn" if c else ("act" if (r and running) else "")
    a2b = "dn" if c else ("run" if (r and running) else "")
    a2l = "✅ Done" if c else ("⚡ Writing..." if (r and running) else "Waiting for Agent 1")
    st.markdown(f"""
    <div class="acard {a2c}">
      <div class="ah">
        <span style="font-size:1.2rem">✍️</span>
        <span class="an">Marketing Content Strategist</span>
        <span class="ab {a2b}">{a2l}</span>
      </div>
      <div class="ad">Turns research into ready-to-send content grounded in real data</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="explain">
      <b>Step 1 — Research</b><br>
      Agent 1 uses Serper (Google Search) to find real articles, statistics,
      and pain points about your niche. No fabricated data.<br><br>
      <b>Step 2 — Write</b><br>
      Agent 2 reads the research and writes your cold email / post, opening
      with a real statistic, no hype words, and one clear call to action.<br><br>
      <b>Output</b><br>
      A ready-to-copy email / post backed by real data — not generic AI filler.
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown('<p style="font-size:.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.1em;color:rgba(255,255,255,.3);margin-bottom:.5rem">📡 Live Activity Log</p>', unsafe_allow_html=True)

    # This placeholder is updated in real time by the log() helper below
    log_placeholder = st.empty()

    def render_logs():
        lines = "".join(
            f'<div class="li {t}">{m}</div>' for t, m in ss.logs
        ) or '<div class="li info">Waiting for crew to start — click Generate ⬅️</div>'
        if ss.status == "running":
            lines += '<div class="li agent" style="margin-top:4px"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>'
        log_placeholder.markdown(f'<div class="logbox">{lines}</div>', unsafe_allow_html=True)

    render_logs()

    if ss.status == "error" and ss.error:
        st.error(f"**Error:** {ss.error[:400]}")


# ---------------------------------------------------------------------------
# Output panel — appears at the bottom once the crew is done
# ---------------------------------------------------------------------------
out_placeholder = st.empty()

def render_output():
    if not ss.result:
        return
    raw = ss.result.strip()

    # Try to separate subject line from body for cold emails
    subject, body = "", raw
    for line in raw.split("\n"):
        if line.lower().startswith("subject:"):
            subject = line.split(":", 1)[-1].strip()
            body = raw[raw.lower().find("subject:") + 8 + len(subject):].strip()
            break

    out_placeholder.markdown(f"""
<div class="outcard">
  <div class="obadge">✅ Ready to Copy & Send</div>
  {'<div class="osubj">📧 ' + subject + '</div>' if subject else ''}
  <div class="obody">{body}</div>
</div>""", unsafe_allow_html=True)

render_output()

# Expander with raw text for easy copying
if ss.result:
    with st.expander("📋 Copy full output"):
        st.code(ss.result.strip(), language=None)


# ---------------------------------------------------------------------------
# Run crew — triggered by the sidebar button
#
# The crew runs SYNCHRONOUSLY in the main Streamlit thread.
# This is simpler and more reliable than background threading:
#   - No thread-safety issues with session state
#   - CrewAI callbacks can update the UI in real time
#   - Behaves exactly the same as running in the terminal
# ---------------------------------------------------------------------------
def log(log_type: str, message: str):
    """Append a line to the activity log and re-render it immediately."""
    ss.logs.append((log_type, message))
    render_logs()


if run_btn:
    # Validate inputs before starting
    if not groq_key:
        st.error("⚠️ Please enter your Groq API key in the sidebar.")
        st.stop()
    if not serper_key:
        st.error("⚠️ Please enter your Serper API key in the sidebar.")
        st.stop()

    # Reset state for a fresh run
    ss.status        = "running"
    ss.logs          = []
    ss.result        = None
    ss.error         = None
    ss.research_done = False
    ss.content_done  = False
    ss.elapsed       = 0
    start_time = time.time()

    try:
        from crewai import Agent, Task, Crew, Process, LLM
        from crewai_tools import SerperDevTool

        log("agent", "⚡ Loading LLM (Groq / Llama 3.3 70B Versatile)...")

        llm = LLM(
            model="groq/llama-3.3-70b-versatile",
            api_key=groq_key,
            temperature=0.6,
        )
        search_tool = SerperDevTool(api_key=serper_key)
        log("info", "🔧 Agents ready!")

        # Callbacks — called automatically when each task finishes
        def on_research_done(output):
            ss.research_done = True
            log("ok",    "✅ Research complete!")
            log("agent", "✍️  Agent 2: Writing your content...")

        def on_content_done(output):
            ss.content_done = True
            log("ok", "✅ Content written!")

        # Build agents (same config as agency_marketing_crew.py)
        researcher = Agent(
            role="Market Research Analyst",
            goal=(
                f"Find real, current pain points and at least one concrete statistic "
                f"about {niche} that connects to the problem {service} solves."
            ),
            backstory="Sharp market analyst. Never fabricates stats. Always cites sources.",
            tools=[search_tool],
            llm=llm,
            verbose=False,
        )

        content_writer = Agent(
            role="Marketing Content Strategist",
            goal="Turn research into credible marketing content that gets replies.",
            backstory=(
                "Writes for a real agency. Direct, specific, no hype. "
                "Always ends with one clear, low-pressure call to action."
            ),
            llm=llm,
            verbose=False,
        )

        # Tasks
        research_task = Task(
            description=(
                f"Research {niche}. Find 2-3 common operational pain points and "
                f"at least one concrete statistic showing the cost of NOT solving "
                f"the problem that {service} addresses."
            ),
            expected_output="Bullet list: 2-3 pain points + 1 stat with source.",
            agent=researcher,
            callback=on_research_done,
        )

        content_task = Task(
            description=(
                f"Using the research, write a {content_type} pitching {service} "
                f"to {niche}. Open with the pain point or stat, avoid hype, "
                f"end with one clear low-pressure call to action."
            ),
            expected_output="Ready-to-post marketing content.",
            agent=content_writer,
            context=[research_task],
            callback=on_content_done,
        )

        log("agent", "🔍 Agent 1: Searching Google for pain points...")

        crew = Crew(
            agents=[researcher, content_writer],
            tasks=[research_task, content_task],
            process=Process.sequential,
            verbose=False,
        )

        result = crew.kickoff(inputs={
            "niche":        niche,
            "our_service":  service,
            "content_type": content_type,
        })

        ss.result  = result.raw
        ss.elapsed = round(time.time() - start_time, 1)
        ss.status  = "done"
        log("ok", f"🎉 Done in {ss.elapsed}s! Scroll down to see your content.")
        render_output()

    except Exception as e:
        ss.error   = str(e)
        ss.status  = "error"
        ss.elapsed = round(time.time() - start_time, 1)
        log("err", f"❌ {str(e)[:250]}")
