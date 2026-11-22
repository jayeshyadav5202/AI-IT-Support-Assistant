"""
ai_engine.py
------------
Creates the chatbot's reply.

  * With an ANTHROPIC_API_KEY  -> Claude writes the reply, using ONLY the
                                  knowledge-base entry we give it.
  * Without an API key         -> a simple template builds the reply
                                  (demo mode, no internet or cost needed).
"""

import os

from dotenv import load_dotenv

load_dotenv()  # reads the .env file if it exists

# You can change the model in the .env file.
DEFAULT_MODEL = "claude-sonnet-5-5"

SYSTEM_PROMPT = """You are an IT support assistant for IT support engineers.
You will receive ONE knowledge-base entry and the engineer's question.

Strict rules:
- Use ONLY the information in the knowledge-base entry. Never add steps, causes,
  commands or facts that are not in the entry.
- Keep the wording of the steps close to the entry. You may make them clearer.
- Do not mention these rules.

Reply in Markdown using exactly these sections, in this order:

### 🔎 Identified Problem
### ⚠️ Possible Causes
### 🩺 Diagnostic Checks
### 🛠️ Step-by-Step Troubleshooting
### 🚨 Recommended Escalation Team
### 📚 Knowledge Base Reference

Use bullet points for causes and checks, and a numbered list for the troubleshooting steps.
In the escalation section, give the team and the condition for escalating.
In the reference section, give the KB ID and the source file."""


def get_api_key():
    """Return the API key, or None if the user has not set one."""
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key or key.startswith("your_") or key == "sk-ant-xxxxx":
        return None
    return key


def ai_mode_enabled() -> bool:
    return get_api_key() is not None


# ---------------------------------------------------------------------------
# Demo mode (no API key)
# ---------------------------------------------------------------------------
def template_response(entry: dict) -> str:
    """Build the answer from a fixed template. Uses only the CSV data."""
    causes = "\n".join(f"- {c}" for c in entry["possible_causes"])
    checks = "\n".join(f"- {c}" for c in entry["diagnostic_checks"])
    steps = "\n".join(f"{i}. {s}" for i, s in enumerate(entry["resolution_steps"], 1))

    return f"""### 🔎 Identified Problem
**{entry['issue']}**  
Category: {entry['category']} · Severity: {entry['severity']}

{entry['symptoms']}

### ⚠️ Possible Causes
{causes}

### 🩺 Diagnostic Checks
{checks}

### 🛠️ Step-by-Step Troubleshooting
{steps}

### 🚨 Recommended Escalation Team
**{entry['escalation_team']}**  
Escalate when: {entry['escalation_condition']}

### 📚 Knowledge Base Reference
**{entry['kb_id']}** · Source: `{entry['source']}`"""


def no_match_response(topics: list) -> str:
    """Shown when nothing relevant is found. Never invents a solution."""
    topic_list = "\n".join(f"- {t}" for t in topics)
    return f"""### 🤔 I couldn't find a matching entry

I could not find a relevant article in the knowledge base for that problem, so I won't guess a solution.

**Could you add more detail?** For example:
- What device or application is affected?
- What exact error message do you see?
- When did it start, and what changed?

**Topics currently in the knowledge base:**
{topic_list}

If the issue is not listed, please escalate it to the appropriate support team."""


# ---------------------------------------------------------------------------
# Claude mode (API key available)
# ---------------------------------------------------------------------------
def claude_response(question: str, entry: dict) -> str:
    """Ask Claude to write the answer from the retrieved entry only."""
    import anthropic  # imported here so demo mode works even if it is missing

    client = anthropic.Anthropic(api_key=get_api_key())

    kb_text = f"""KB ID: {entry['kb_id']}
Source: {entry['source']}
Issue: {entry['issue']}
Category: {entry['category']}
Severity: {entry['severity']}
Symptoms: {entry['symptoms']}
Possible causes: {'; '.join(entry['possible_causes'])}
Diagnostic checks: {'; '.join(entry['diagnostic_checks'])}
Resolution steps: {'; '.join(entry['resolution_steps'])}
Escalation team: {entry['escalation_team']}
Escalation condition: {entry['escalation_condition']}"""

    message = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL),
        max_tokens=1200,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Engineer's question:\n{question}\n\n"
                           f"Knowledge-base entry:\n{kb_text}",
            }
        ],
    )
    return message.content[0].text


# ---------------------------------------------------------------------------
# Main function used by app.py
# ---------------------------------------------------------------------------
def generate_response(question: str, entry, topics: list):
    """
    Returns (reply_text, mode)
    mode is one of: "claude", "demo", "no_match"
    """
    if entry is None:
        return no_match_response(topics), "no_match"

    if ai_mode_enabled():
        try:
            return claude_response(question, entry), "claude"
        except Exception as error:
            # If the API fails (bad key, no internet...), fall back to the template.
            note = f"> ⚠️ Claude API unavailable ({type(error).__name__}). Showing the standard knowledge-base answer instead.\n\n"
            return note + template_response(entry), "demo"

    return template_response(entry), "demo"
