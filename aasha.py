import streamlit as st
import json
import os
import time
import random
import requests
from streamlit_lottie import st_lottie
import google.generativeai as genai
from difflib import SequenceMatcher
from bs4 import BeautifulSoup
import html
import bcrypt

# Configure Gemini API
api_key= "gemini_api_key"

model = genai.GenerativeModel('gemini-2.0-flash')

st.set_page_config(page_title="AASHA AI", page_icon="🌸", layout="wide")

# Load users data from JSON file or create default
def load_users():
    if not os.path.exists("users.json"):
        with open("users.json", "w") as f:
            json.dump({"names": [], "usernames": [], "passwords": []}, f)
    with open("users.json", "r") as file:
        return json.load(file)

def save_users(data):
    with open("users.json", "w") as file:
        json.dump(data, file)

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

menu = st.sidebar.selectbox("Menu", ["Signup", "Login"])
users_data = load_users()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_idx" not in st.session_state:
    st.session_state.user_idx = None

if menu == "Signup":
    st.title("🌸 AASHA AI Signup")
    name = st.text_input("Full Name")
    username = st.text_input("Email ID / Username")
    password = st.text_input("Password", type="password")

    if st.button("Signup"):
        if username in users_data["usernames"]:
            st.error("User already exists. Please login.")
        elif not (name and username and password):
            st.warning("Please fill all fields.")
        else:
            hashed_pw = hash_password(password)
            users_data["names"].append(name)
            users_data["usernames"].append(username)
            users_data["passwords"].append(hashed_pw)
            save_users(users_data)
            st.success("Signup successful! You can now login.")

elif menu == "Login":
    st.title("🌸 AASHA AI Login")
    username_input = st.text_input("Email ID / Username")
    password_input = st.text_input("Password", type="password")

    if st.button("Login"):
        if not username_input or not password_input:
            st.warning("Please enter login details.")
        else:
            try:
                user_idx = users_data["usernames"].index(username_input)
                hashed_pw = users_data["passwords"][user_idx].encode()
                if bcrypt.checkpw(password_input.encode(), hashed_pw):
                    st.session_state.logged_in = True
                    st.session_state.user_idx = user_idx
                    st.success(f"Welcome {users_data['names'][user_idx]} to AASHA AI! 🌸")
                    st.balloons()
                else:
                    st.error("Invalid credentials.")
            except ValueError:
                st.error("Invalid credentials.")

if st.session_state.logged_in:

    system_prompt = """
You are *AASHA AI, an empathetic, AI-powered career mentor for women on the *JobsForHer platform. Speak like a supportive big sister and career buddy — clear, friendly, and motivating.

*IMPORTANT RESPONSE RULES (Strictly Follow):*
- *Maximum 4-5 short lines per response. Never exceed.*
- *Strictly avoid long paragraphs. Use bullets or numbered lists wherever possible.*
- No introductions or explanations unless explicitly asked.
- Use simple, direct, cheerful language.
- If unsure, politely ask for clarification in 1 line.

*Special Rule:*  
- If the user introduces themselves (e.g., "I am a Python developer"), reply in *1-2 cheerful lines* acknowledging them and offering help. Do *not* ask multiple questions or give a long list of services.  
  Example:  
  "Awesome! Love seeing Python devs here. Need job leads, projects, or a learning boost? Just say the word. 🚀"

*Core Responsibilities:*
- *Job Search Help:* Use search_jobs_api(query) and return top 3 clickable markdown job links.
- *Learning Roadmap:* Provide a *3-step plan* (Beginner → Intermediate → Advanced) with *2-3 free YouTube videos or other courses* using get_youtube_videos(topic).
- *Community Support:* Recommend *women-in-tech communities with join links* (prefer *HerKey*).
- *Interview Prep:* Give *2-3 quick tips* + *1-2 resources*.
- *Confidence Boost Mode:* If user feels low, send an uplifting 2-line message, suggest a quick action (like updating LinkedIn), and share a motivational quote in 1 line.

*Resume Guider:*
Act as a pro resume writer. If user says:  
"I’m creating a resume for [desired role]"  
Give a *clean, ATS-friendly format* guide with: 
- give pointwise draft structure
- Summary advice (clear, strong intro)
- Action-verb-based experience writing
- Metrics-driven achievement bullets
- Must-have vs optional sections (based on hiring trends)
- suggest tools like [Canva Resume Builder](https://www.canva.com/resumes/) or [Zety](https://zety.com/resume-builder) for design.
*Guardrails:*
- If asked anything inappropriate, respond: “I'm here to support your career journey. Let’s keep things respectful and empowering. 🌸”
- Never give medical, legal, or sensitive advice.
- Never ask for personal data.

*Tone:* Supportive, positive, friendly — like a caring mentor & friend.
"""

    with open("data.json") as f:
        intents = json.load(f)

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

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "show_faqs" not in st.session_state:
        st.session_state.show_faqs = False
    if "anim_index" not in st.session_state:
        st.session_state.anim_index = 0
    if "last_anim_time" not in st.session_state:
        st.session_state.last_anim_time = time.time()

    def save_user_history(username, history):
        os.makedirs("chat_histories", exist_ok=True)
        filepath = f"chat_histories/{username}.json"
        with open(filepath, "w") as f:
            json.dump(history, f)

    def load_user_history(username):
        filepath = f"chat_histories/{username}.json"
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                return json.load(f)
        return []

    username = users_data["usernames"][st.session_state.user_idx]
    if not st.session_state.chat_history:
        st.session_state.chat_history = load_user_history(username)

    with st.sidebar:
        st.markdown("## AASHA💖")
        st.markdown("<p style='font-size:14px; text-align:left;'>Visit <a href='https://www.herkey.com/' target='_blank' style='color:#f06292;'>HerKey</a> 🌐</p>", unsafe_allow_html=True)
        anim_file = lottie_files[st.session_state.anim_index]
        animation_data = load_lottie(anim_file)
        st_lottie(animation_data, height=300, key="lottie")

        st.markdown("## ❓ FAQs")
        if st.button("View FAQs"):
            st.session_state.show_faqs = not st.session_state.show_faqs

        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            save_user_history(username, [])
            st.success("Chat history cleared.")

        if st.button("Show Full History"):
            history = load_user_history(username)
            if not history:
                st.info("No previous history found.")
            else:
                for h in history:
                    who = "👩‍💼 You" if h["role"] == "user" else "🤖 AASHA"
                    st.markdown(f"{who}:** {h['parts'][0]}")

    def is_similar(a, b, threshold=0.6):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio() > threshold

    def get_intent_response(user_message):
        for intent in intents['intents']:
            for pattern in intent['patterns']:
                if is_similar(pattern, user_message):
                    return random.choice(intent['responses'])
        return None

    GUARDRAIL_KEYWORDS = ["joke about women", "kitchen", "illegal", "aadhar", "social security", "are you single"]

    def check_guardrails(user_message):
        return any(k in user_message.lower() for k in GUARDRAIL_KEYWORDS)

    def search_jobs(query):
        results = []
        try:
            url = f"https://internshala.com/internships/keywords-{query}/"
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(res.text, "html.parser")
            for div in soup.select(".individual_internship")[:5]:
                title = div.select_one(".profile").text.strip() if div.select_one(".profile") else "N/A"
                company = div.select_one(".company_name").text.strip() if div.select_one(".company_name") else "N/A"
                link = "https://internshala.com" + div.select_one("a")["href"] if div.select_one("a") else "N/A"
                results.append(f"🖥 At {company} — [Apply Here]({link})")
        except Exception as e:
            results.append(f"Fetch error: {e}")
        return "\n\n".join(results) if results else "No jobs found."

    def get_women_tech_communities():
        return (
            "Here are some amazing communities for women in tech:\n\n"
            "- [Women Who Code](https://www.womenwhocode.com/)\n"
            "- [HerTech](https://hertechtrail.org/)\n"
            "- [JobsForHer Community](https://www.jobsforher.com/)\n\n"
            "Join one and feel empowered! 💖"
        )

    chat = model.start_chat(history=st.session_state.chat_history)

    def send_message(user_input):
        user_message = user_input.strip()
        if user_message:
            st.session_state.chat_history.append({"role": "user", "parts": [user_message]})
            if check_guardrails(user_message):
                assistant_reply = "I'm here to support your career journey. Let’s keep things respectful. 🌸"
            elif "community" in user_message.lower():
                assistant_reply = get_women_tech_communities()
            else:
                response = get_intent_response(user_message)
                if response:
                    assistant_reply = response
                elif any(w in user_message.lower() for w in ["job", "internship"]):
                    assistant_reply = f"Helping with {user_message} opportunities.\n\n" + search_jobs(user_message)
                else:
                    full_prompt = f"{system_prompt}\nUser: {user_message}"
                    gemini_response = chat.send_message(full_prompt)
                    assistant_reply = gemini_response.text.strip()
            st.session_state.chat_history.append({"role": "model", "parts": [assistant_reply]})
            save_user_history(username, st.session_state.chat_history)

    st.markdown("<h1 style='text-align:center;'>🌸 AASHA AI</h1>", unsafe_allow_html=True)
    st.markdown("""
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
    """, unsafe_allow_html=True)

    if user_input := st.chat_input("Type your message here..."):
        send_message(user_input)

    for msg in st.session_state.chat_history:
        role_class = "user-msg" if msg["role"] == "user" else "bot-msg"
        safe_msg = html.escape(msg["parts"][0])
        st.markdown(f"<div class='chat-message {role_class}'>{safe_msg}</div>", unsafe_allow_html=True)

else:
    st.info("Please login to continue.")
