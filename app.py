"""
app.py
------
Streamlit chat interface for the AI IT Support Assistant.
Run with:  streamlit run app.py
"""

import streamlit as st

from ai_engine import ai_mode_enabled, generate_response
from knowledge_base import KnowledgeBase

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(page_title="AI IT Support Assistant", page_icon="🛠️", layout="centered")

# Light theme with blue / purple accents. Plain CSS, no animations.
st.markdown(
    """
<style>
/* ---- Base: white / light background (forced, even if browser is in dark mode) ---- */
.stApp { background: linear-gradient(180deg, #f5f7ff 0%, #ffffff 40%); }
.stApp, .stApp p, .stApp li, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3 { color: #1f2937; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 820px; padding-top: 2rem; padding-bottom: 6rem; }

/* ---- Header ---- */
.hero {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    border-radius: 20px; padding: 1.6rem 1.8rem; margin-bottom: 1.2rem;
    box-shadow: 0 8px 24px rgba(79, 70, 229, 0.18);
}
.hero h1 { color: #ffffff !important; margin: 0; font-size: 1.9rem; }
.hero p  { color: #e0e7ff !important; margin: 0.4rem 0 0 0; font-size: 1rem; }

/* ---- Cards ---- */
.card {
    background: #ffffff; border: 1px solid #e5e7eb; border-radius: 16px;
    padding: 1.1rem 1.3rem; margin-bottom: 1rem;
    box-shadow: 0 2px 10px rgba(17, 24, 39, 0.04);
}
.card h3 { margin: 0 0 0.4rem 0; font-size: 1.1rem; color: #4338ca !important; }
.card p  { margin: 0; color: #4b5563 !important; }
.mode-badge {
    display: inline-block; padding: 0.15rem 0.7rem; border-radius: 999px;
    font-size: 0.8rem; font-weight: 600; background: #ede9fe; color: #5b21b6 !important;
}

/* ---- Chat bubbles ---- */
[data-testid="stChatMessage"] {
    border-radius: 18px; padding: 1rem 1.2rem; margin-bottom: 0.8rem;
    background: #ffffff; border: 1px solid #e5e7eb;
    box-shadow: 0 2px 8px rgba(17, 24, 39, 0.04);
}
/* user bubble = light blue, assistant bubble = white */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: #eef2ff; border-color: #c7d2fe;
}
[data-testid="stChatMessage"] h3 {
    font-size: 1.02rem; color: #4338ca !important; margin-top: 0.9rem; margin-bottom: 0.3rem;
}
[data-testid="stChatMessage"] h3:first-child { margin-top: 0; }
[data-testid="stChatMessage"] code { background: #ede9fe; color: #5b21b6; border-radius: 6px; }

/* ---- Buttons ---- */
.stButton > button {
    border-radius: 12px; border: 1px solid #c7d2fe; background: #ffffff;
    color: #4338ca; text-align: left; padding: 0.55rem 0.9rem; width: 100%;
}
.stButton > button:hover { border-color: #7c3aed; color: #7c3aed; background: #f5f3ff; }

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] { background: #f5f3ff; }

/* ---- Chat input ---- */
[data-testid="stChatInput"] { border-radius: 16px; border: 1px solid #c7d2fe; background: #ffffff; }
[data-testid="stChatInput"] textarea { color: white; }

/* ---- Small screens ---- */
@media (max-width: 640px) {
    .block-container { padding-left: 0.8rem; padding-right: 0.8rem; }
    .hero { padding: 1.1rem; }
    .hero h1 { font-size: 1.45rem; }
}
</style>
""",
    unsafe_allow_html=True,
)

EXAMPLES = [
    ("📶", "My Wi-Fi is connected but there is no internet"),
    ("📧", "Outlook keeps crashing when I open it"),
    ("🔐", "User cannot log in because the account is locked"),
    ("🖨️", "The printer is not printing"),
    ("🔒", "VPN will not connect from home"),
    ("💳", "Payment API is returning HTTP 500 error"),
]


# ---------------------------------------------------------------------------
# Load the knowledge base once and keep it in memory
# ---------------------------------------------------------------------------
@st.cache_resource
def load_kb():
    return KnowledgeBase()


kb = load_kb()

# ---------------------------------------------------------------------------
# Session state (chat history)
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []      # list of {"role": ..., "content": ...}
if "pending" not in st.session_state:
    st.session_state.pending = None     # question chosen from the example buttons


def use_example(text):
    st.session_state.pending = text


def clear_chat():
    st.session_state.messages = []
    st.session_state.pending = None


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🛠️ IT Support Assistant")
    if ai_mode_enabled():
        st.success("Claude AI mode is ON")
    else:
        st.info("Demo mode (no API key). Template answers are used.")
    st.caption(f"📚 {len(kb.df)} articles loaded from the knowledge base")
    st.button("🗑️ Clear chat", on_click=clear_chat, use_container_width=True)

# ---------------------------------------------------------------------------
# Header + welcome
# ---------------------------------------------------------------------------
st.markdown(
    """
<div class="hero">
  <h1>🛠️ AI IT Support Assistant</h1>
  <p>Describe a technical problem in plain English and get troubleshooting steps from the knowledge base.</p>
</div>
""",
    unsafe_allow_html=True,
)

mode_text = "Claude AI mode" if ai_mode_enabled() else "Demo mode"
st.markdown(
    f"""
<div class="card">
  <h3>👋 Welcome!</h3>
  <p>Type your issue in the chat box below. Answers come <b>only</b> from the company knowledge base,
  so you will never get invented fixes. If nothing relevant is found, I will ask for more details.</p>
  <p style="margin-top:0.6rem;"><span class="mode-badge">{mode_text}</span></p>
</div>
""",
    unsafe_allow_html=True,
)

# Example problems (shown only while the chat is empty)
if not st.session_state.messages:
    st.markdown("**💡 Try one of these examples:**")
    cols = st.columns(2)
    for i, (icon, text) in enumerate(EXAMPLES):
        cols[i % 2].button(f"{icon}  {text}", key=f"ex_{i}", on_click=use_example, args=(text,))

# ---------------------------------------------------------------------------
# Show previous messages
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# Handle a new question (typed or from an example button)
# ---------------------------------------------------------------------------
typed = st.chat_input("Describe the IT problem, e.g. 'VPN not connecting'")
question = typed or st.session_state.pending
st.session_state.pending = None

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(question)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Searching the knowledge base..."):
            entry, score = kb.search(question)
            reply, mode = generate_response(question, entry, kb.topics())
        st.markdown(reply)
        if entry:
            st.caption(f"Match confidence (TF-IDF similarity): {score:.0%}")

    st.session_state.messages.append({"role": "assistant", "content": reply})
