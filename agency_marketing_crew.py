"""
agency_marketing_crew.py
------------------------
Core crew logic: two AI agents that turn a target niche into
ready-to-post marketing content for an automation agency.

HOW IT WORKS
------------
  Agent 1 – Market Research Analyst
    Searches the web (via Serper) for real pain points and stats
    about a given niche. Never fabricates data.

  Agent 2 – Marketing Content Strategist
    Reads Agent 1's research and writes a cold email / LinkedIn post /
    Twitter thread — grounded in real stats, no hype, one clear CTA.

USAGE (terminal)
----------------
  python agency_marketing_crew.py

USAGE (web UI)
--------------
  streamlit run app.py
"""

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool


# ---------------------------------------------------------------------------
# 1. Load environment variables (.env file)
#    GROQ_API_KEY  – free at console.groq.com
#    SERPER_API_KEY – free at serper.dev (Google Search API)
# ---------------------------------------------------------------------------
load_dotenv()

GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("Missing GROQ_API_KEY — add it to your .env file")
if not SERPER_API_KEY:
    raise ValueError("Missing SERPER_API_KEY — add it to your .env file")


# ---------------------------------------------------------------------------
# 2. LLM configuration
#    Using Groq's llama-3.3-70b-versatile:
#    - Free tier (no credit card needed)
#    - Excellent tool-calling support needed by Agent 1
#    - Fast inference (~10-15 seconds per run)
# ---------------------------------------------------------------------------
llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY,
    temperature=0.6,
)


# ---------------------------------------------------------------------------
# 3. Tools
#    SerperDevTool wraps the Serper API (Google Search).
#    Agent 1 uses this to find real-world pain points and statistics.
# ---------------------------------------------------------------------------
search_tool = SerperDevTool(api_key=SERPER_API_KEY)


# ---------------------------------------------------------------------------
# 4. Agents
#    Each agent has a role, a goal, and a backstory that shapes its
#    personality and output style.
# ---------------------------------------------------------------------------

researcher = Agent(
    role="Market Research Analyst",
    goal=(
        "Find real, current pain points and at least one concrete statistic "
        "about {niche} that connects to the problem {our_service} solves."
    ),
    backstory=(
        "You are a sharp market analyst working for a small automation agency. "
        "You only use data you can verify. You never fabricate statistics. "
        "When you find a stat, you always note where it came from."
    ),
    tools=[search_tool],
    llm=llm,
    verbose=True,
)

content_writer = Agent(
    role="Marketing Content Strategist",
    goal=(
        "Turn the research into a short, credible piece of {content_type} "
        "that gets replies — not generic AI filler."
    ),
    backstory=(
        "You write for a real, small agency. You are direct and specific. "
        "You never use hype words like 'revolutionary' or 'game-changing'. "
        "Every piece of content you write opens with a real pain point or "
        "statistic, and ends with exactly one low-pressure call to action."
    ),
    llm=llm,
    verbose=True,
)


# ---------------------------------------------------------------------------
# 5. Tasks
#    Tasks define exactly what each agent should produce.
#    Agent 2's task has context=[research_task] so it automatically
#    receives Agent 1's output before writing.
# ---------------------------------------------------------------------------

research_task = Task(
    description=(
        "Research {niche}.\n\n"
        "Find:\n"
        "  • 2-3 common operational pain points this audience faces\n"
        "  • At least one concrete statistic or real-world example that "
        "    shows the cost of NOT solving the problem {our_service} addresses\n\n"
        "Be specific. Cite where each stat or example came from."
    ),
    expected_output=(
        "A short bullet list:\n"
        "  • Pain point 1 (with source)\n"
        "  • Pain point 2 (with source)\n"
        "  • Pain point 3 (with source)\n"
        "  • Key statistic (with source)"
    ),
    agent=researcher,
)

content_task = Task(
    description=(
        "Using ONLY the research provided, write a {content_type} that pitches "
        "{our_service} to {niche}.\n\n"
        "Rules:\n"
        "  • Open with the most compelling pain point or statistic — not a generic intro\n"
        "  • Keep it concrete and specific — use the actual numbers from the research\n"
        "  • Avoid hype language (no 'revolutionary', 'cutting-edge', 'game-changing')\n"
        "  • End with exactly one low-pressure call to action (e.g. 'reply if you want "
        "    a quick demo')\n"
        "  • For cold emails: include a subject line"
    ),
    expected_output=(
        "Ready-to-send {content_type}, properly formatted.\n"
        "For emails: Subject line first, then body."
    ),
    agent=content_writer,
    context=[research_task],
)


# ---------------------------------------------------------------------------
# 6. Crew
#    The crew runs tasks sequentially:
#    research_task → content_task
#    Agent 2 automatically gets Agent 1's output as context.
# ---------------------------------------------------------------------------
crew = Crew(
    agents=[researcher, content_writer],
    tasks=[research_task, content_task],
    process=Process.sequential,
    verbose=True,
)


# ---------------------------------------------------------------------------
# 7. Run
#    Edit the inputs below to target a different niche or service.
#    content_type options: "cold outreach email", "LinkedIn post",
#                          "Twitter thread", "Instagram caption"
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    inputs = {
        "niche":        "small and solo US dental clinics",
        "our_service":  (
            "an AI voice bot (built on Retell AI + Twilio) that answers "
            "every incoming call and books appointments 24/7, even after "
            "hours or when the front desk is busy"
        ),
        "content_type": "cold outreach email",
    }

    result = crew.kickoff(inputs=inputs)

    print("\n" + "=" * 50)
    print("FINAL MARKETING CONTENT")
    print("=" * 50)
    print(result.raw)
