import streamlit as st
import google.generativeai as genai
import json
import random
from streamlit_lottie import st_lottie
import time

# API config
genai.configure(api_key=st.secrets["gemini_api_key"])
model = genai.GenerativeModel('gemini-2.0-flash')

# Page config
st.set_page_config(page_title="AASHA AI Chat", page_icon="🌸", layout="wide")

# System prompt
system_prompt = """
You are AASHA, an AI-powered career assistant chatbot designed for women exploring jobs, internships, and upskilling opportunities on the "Jobs For Her" platform. You can talk like a friend and mentor to users, answering queries about the JobsForHer website, job search, upskilling, and guiding them efficiently.

Your role is to help users with:
- Exploring suitable jobs or internships based on their profile or preferences.
- Skill-gap analysis and personalized learning roadmap suggestions.
- Contextual conversation flow with memory of the current session.
- Bias detection alerts in job descriptions.
- Feedback collection and fallback response logging.
- Displaying insightful analytics of user interests and chatbot performance (simulated).

Keep answers concise and relevant to the user's query, exceed only if they ask for a detailed explanation.
Also, explain how to use the JobsForHer website to search jobs, join sessions, and participate in learning communities. Suggest job categories based on user queries.
You must ensure:
- Session-based memory only (no long-term data storage).
- No collection of sensitive personal data.
- Responses are ethically aligned, supportive, and empowering.
- If unsure, admit gracefully and suggest feedback.
- Multi-turn logic and fallback intelligence.
- Fallback logging & analytics updating.
- Empathy, encouragement, and non-judgmental support.

💎 WOW FACTOR: “Career Confidence Boost” Mode
When a user expresses doubt or frustration, analyze their goals and past achievements, generate an empowering message, and suggest a small win (like updating a resume or recalling a proud moment). Also share a quote for motivation.
"""

# Load intents
with open("data.json") as f:
    intents = json.load(f)

# Load Lottie animations
def load_lottie(filepath):
    with open(filepath, "r") as f:
        return json.load(f)

lottie_files = [
    "Animation - 111111111111.json",
    "Animation - 1745602570779.json",
    "Animation - 1745602403827.json",
    "Animation - 1745602307325.json",
    "Animation - 1745603060476.json",
    "Animation - 1745602632999.json",
    "Animation - 1745603548246.json"
]

# Session state defaults
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "user_input" not in st.session_state:
    st.session_state.user_input = ""
if "show_faqs" not in st.session_state:
    st.session_state.show_faqs = False
if "anim_index" not in st.session_state:
    st.session_state.anim_index = 0
if "last_anim_time" not in st.session_state:
    st.session_state.last_anim_time = time.time()

# Sidebar: FAQs and Animation
with st.sidebar:
    st.markdown("## AASHA💖")

    # Auto-change animation every 5 seconds
    if time.time() - st.session_state.last_anim_time > 3.5:
        st.session_state.anim_index = (st.session_state.anim_index + 1) % len(lottie_files)
        st.session_state.last_anim_time = time.time()

    anim_file = lottie_files[st.session_state.anim_index]
    animation_data = load_lottie(anim_file)
    st_lottie(animation_data, height=300, key="lottie")

    # FAQs toggle button
    st.markdown("## ❓ FAQs")
    if st.button("View FAQs"):
        st.session_state.show_faqs = not st.session_state.show_faqs

    if st.session_state.show_faqs:
        st.markdown("### ℹ️ Frequently Asked Questions")
        for intent in intents['intents']:
            with st.expander(f"💬 {intent['tag'].capitalize()}"):
                for q in intent['patterns']:
                    st.markdown(f"- **Q:** {q}")
                st.markdown(f"**A:** {random.choice(intent['responses'])}")

# Start Gemini chat
chat = model.start_chat(history=st.session_state.chat_history)

# Intent response fetch
def get_intent_response(user_message):
    for intent in intents['intents']:
        for pattern in intent['patterns']:
            if pattern.lower() in user_message.lower():
                return random.choice(intent['responses'])
    return None

# Layout: Chat
st.markdown(
    "<h1 style='text-align:center; font-size:60px;'>🌸 Aasha AI</h1>", 
    unsafe_allow_html=True
)
st.markdown(
    "<h3 style='text-align:center;'>Job & Life Support for Women</h3>", 
    unsafe_allow_html=True
)

# Chat style CSS
st.markdown(
    """
    <style>
    .chat-message {
        padding: 10px 15px;
        border-radius: 20px;
        margin: 5px 0;
        max-width: 75%;
        word-wrap: break-word;
    }
    .user-msg {
        background-color: #add8e6;
        color: black;
        align-self: flex-end;
    }
    .bot-msg {
        background-color: #ffc0cb;
        color: black;
        align-self: flex-start;
    }
    </style>
    """, unsafe_allow_html=True
)

# Display chat history
st.markdown('<div class="chat-history">', unsafe_allow_html=True)
for msg in st.session_state.chat_history:
    role_class = "user-msg" if msg["role"] == "user" else "bot-msg"
    st.markdown(f"<div class='chat-message {role_class}'>{msg['parts'][0]}</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Chat input and send
def send_message():
    user_message = st.session_state.user_input.strip()
    if user_message:
        st.session_state.chat_history.append({"role": "user", "parts": [user_message]})

        response = get_intent_response(user_message)
        if response:
            assistant_reply = response
        else:
            full_prompt = f"{system_prompt}\nUser: {user_message}"
            gemini_response = chat.send_message(full_prompt)
            assistant_reply = gemini_response.text.strip()

        st.session_state.chat_history.append({"role": "model", "parts": [assistant_reply]})
        st.session_state.user_input = ""

st.text_input("Type your message here and press Enter...", key="user_input", on_change=send_message)

st.markdown("---")
st.caption("Made with 💖 by TechnoAI-Girls for AASHA Hackathon 🌸")
