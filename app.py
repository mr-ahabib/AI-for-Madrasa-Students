
import os
from io import BytesIO
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
from gtts import gTTS


load_dotenv()  # Load .env file if present

# Configure Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY and API_KEY != "your_gemini_api_key_here":
    genai.configure(api_key=API_KEY)

# Gemini model to use
MODEL_NAME = "gemini-2.0-flash"

# Safety settings — keep outputs child-safe
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_LOW_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

QURAN_AYAHS = {
    "সূরা আল-ফাতিহা (আয়াত ১)": {
        "arabic": "بِسْمِ اللَّهِ الرَّحْمَـٰنِ الرَّحِيمِ",
        "bangla": "বিসমিল্লাহির রাহমানির রাহীম",
        "meaning": "পরম করুণাময় অতি দয়ালু আল্লাহর নামে",
    },
    "সূরা আল-ফাতিহা (আয়াত ২)": {
        "arabic": "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
        "bangla": "আলহামদুলিল্লাহি রাব্বিল আলামীন",
        "meaning": "সমস্ত প্রশংসা আল্লাহর জন্য, যিনি সারা বিশ্বের প্রতিপালক",
    },
    "সূরা আল-ফাতিহা (আয়াত ৩)": {
        "arabic": "الرَّحْمَـٰنِ الرَّحِيمِ",
        "bangla": "আর রাহমানির রাহীম",
        "meaning": "পরম করুণাময়, অতি দয়ালু",
    },
    "সূরা আল-ফাতিহা (আয়াত ৪)": {
        "arabic": "مَالِكِ يَوْمِ الدِّينِ",
        "bangla": "মালিকি ইয়াওমিদ্দীন",
        "meaning": "বিচার দিনের মালিক",
    },
    "সূরা আল-ইখলাস (আয়াত ১)": {
        "arabic": "قُلْ هُوَ اللَّهُ أَحَدٌ",
        "bangla": "কুল হুওয়াল্লাহু আহাদ",
        "meaning": "বলো, তিনি আল্লাহ, এক-অদ্বিতীয়",
    },
    "সূরা আল-ইখলাস (আয়াত ২)": {
        "arabic": "اللَّهُ الصَّمَدُ",
        "bangla": "আল্লাহুস সামাদ",
        "meaning": "আল্লাহ কারো মুখাপেক্ষী নন",
    },
    "সূরা আল-ইখলাস (আয়াত ৩)": {
        "arabic": "لَمْ يَلِدْ وَلَمْ يُولَدْ",
        "bangla": "লাম ইয়ালিদ ওয়া লাম ইউলাদ",
        "meaning": "তিনি কাউকে জন্ম দেননি এবং তাঁকেও জন্ম দেওয়া হয়নি",
    },
    "সূরা আল-ইখলাস (আয়াত ৪)": {
        "arabic": "وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ",
        "bangla": "ওয়া লাম ইয়াকুল্লাহু কুফুওয়ান আহাদ",
        "meaning": "এবং তাঁর সমতুল্য কেউ নেই",
    },
    "সূরা আন-নাস (আয়াত ১)": {
        "arabic": "قُلْ أَعُوذُ بِرَبِّ النَّاسِ",
        "bangla": "কুল আউযু বিরাব্বিন নাস",
        "meaning": "বলো, আমি আশ্রয় চাই মানুষের প্রতিপালকের কাছে",
    },
    "সূরা আল-ফালাক (আয়াত ১)": {
        "arabic": "قُلْ أَعُوذُ بِرَبِّ الْفَلَقِ",
        "bangla": "কুল আউযু বিরাব্বিল ফালাক",
        "meaning": "বলো, আমি আশ্রয় চাই ঊষার প্রতিপালকের কাছে",
    },
}

# Story topics for the story teller
STORY_TOPICS = [
    "হযরত নূহ (আ.) এর নৌকার গল্প",
    "হযরত ইব্রাহিম (আ.) এর সাহসিকতা",
    "হযরত ইউসুফ (আ.) এর ধৈর্যের গল্প",
    "হযরত মূসা (আ.) এর শৈশব",
    "সত্যবাদী ছেলের গল্প",
    "দয়ালু মেয়েটির গল্প",
    "ভালো প্রতিবেশীর গল্প",
    "সৎ ব্যবসায়ীর গল্প",
    "ছোট্ট হাফেজের গল্প",
    "নামাজের গুরুত্ব নিয়ে গল্প",
]



def check_api_key() -> bool:
    """Check if Gemini API key is configured."""
    return bool(API_KEY) and API_KEY != "your_gemini_api_key_here"


def get_gemini_response(prompt: str, system_instruction: str = "") -> str:
    """
    Send a prompt to Gemini and return the response text.
    Includes safety settings and system instructions for child-safe Islamic content.
    """
    if not check_api_key():
        return "⚠️ Gemini API কী সেট করা হয়নি। অনুগ্রহ করে .env ফাইলে আপনার API কী যোগ করুন।"

    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            safety_settings=SAFETY_SETTINGS,
            system_instruction=system_instruction or None,
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ ত্রুটি হয়েছে: {str(e)}"


def transcribe_audio(uploaded_audio, hint: str) -> str:
    """Transcribe microphone audio to Bangla text using Gemini multimodal input."""
    if uploaded_audio is None or not check_api_key():
        return ""

    try:
        audio_bytes = uploaded_audio.getvalue()
        mime_type = uploaded_audio.type or "audio/wav"

        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            safety_settings=SAFETY_SETTINGS,
        )
        response = model.generate_content(
            [
                (
                    "তুমি অডিও ট্রান্সক্রিপশন সহায়ক। শুধু যা শোনা যায় তা বাংলায় পরিষ্কারভাবে লিখবে। "
                    "অতিরিক্ত ব্যাখ্যা দেবে না। "
                    f"প্রসঙ্গ: {hint}"
                ),
                {"mime_type": mime_type, "data": audio_bytes},
            ]
        )
        return (response.text or "").strip()
    except Exception:
        return ""


@st.cache_data(show_spinner=False)
def build_tts_audio(text: str, lang: str = "bn") -> bytes:
    """Convert text to speech and return MP3 bytes for Streamlit playback."""
    buf = BytesIO()
    gTTS(text=text, lang=lang).write_to_fp(buf)
    return buf.getvalue()


def get_audio_input(label: str, key: str):
    """Safely render audio input for environments with different Streamlit versions."""
    audio_input_fn = getattr(st, "audio_input", None)
    if callable(audio_input_fn):
        return audio_input_fn(label, key=key)
    st.caption("⚠️ ভয়েস ইনপুট ব্যবহার করতে Streamlit 1.39+ দরকার")
    return None


def compare_ayah(user_input: str, correct_text: str) -> dict:
    """
    Compare user's input with the correct ayah text.
    Returns a dict with: is_correct, user_words, correct_words, and per-word match status.
    """
    # Normalize whitespace
    user_words = user_input.strip().split()
    correct_words = correct_text.strip().split()

    # Build word-by-word comparison
    max_len = max(len(user_words), len(correct_words))
    results = []
    mistakes = 0

    for i in range(max_len):
        u = user_words[i] if i < len(user_words) else ""
        c = correct_words[i] if i < len(correct_words) else ""
        match = u == c
        if not match:
            mistakes += 1
        results.append({"user": u, "correct": c, "match": match})

    is_correct = mistakes == 0
    return {
        "is_correct": is_correct,
        "mistakes": mistakes,
        "total_words": len(correct_words),
        "details": results,
    }


st.set_page_config(
    page_title="🕌 AI মাদ্রাসা",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for child-friendly, colorful design
st.markdown(
    """
<style>
    :root {
        --brand-green: #2e7d32;
        --brand-green-soft: #e8f5e9;
        --brand-blue: #1976d2;
        --brand-orange: #f57c00;
        --text-dark: #123524;
    }

    /* --- Google Font --- */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Bengali:wght@400;600;700;800&display=swap');

    /* --- Global Styles --- */
    .stApp {
        font-family: 'Noto Sans Bengali', sans-serif;
        background:
            radial-gradient(circle at 8% 12%, rgba(46, 204, 113, 0.12) 0%, transparent 30%),
            radial-gradient(circle at 92% 18%, rgba(33, 150, 243, 0.1) 0%, transparent 30%),
            linear-gradient(180deg, #f8fffb 0%, #f6fbff 100%);
    }

    .block-container {
        max-width: 1100px;
        padding-top: 1.2rem;
        padding-bottom: 2.2rem;
    }

    /* --- Header Banner --- */
    .main-header {
        background: linear-gradient(135deg, #1a7a4c 0%, #2ecc71 50%, #f39c12 100%);
        color: white;
        padding: 2rem 1.5rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(46, 204, 113, 0.3);
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
        animation: shimmer 8s infinite linear;
    }
    @keyframes shimmer {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        position: relative;
    }
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.95;
        position: relative;
    }

    /* --- Tab Styling --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        justify-content: center;
        border-bottom: none;
        padding: 0 1rem;
        flex-wrap: wrap;
    }
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #f0f7f4, #e8f5e9);
        border-radius: 16px;
        padding: 16px 28px;
        font-size: 1.1rem;
        font-weight: 700;
        border: 2px solid #c8e6c9;
        transition: all 0.3s ease;
        color: #2e7d32;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #c8e6c9, #a5d6a7);
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(46, 125, 50, 0.2);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2e7d32, #43a047) !important;
        color: white !important;
        border-color: #2e7d32 !important;
        box-shadow: 0 4px 20px rgba(46, 125, 50, 0.4);
    }

    /* --- Card Containers --- */
    .feature-card {
        background: linear-gradient(145deg, #ffffff, #f8fdf9);
        border: 2px solid #e8f5e9;
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.1);
    }

    /* --- Response Box --- */
    .response-box {
        background: linear-gradient(145deg, #e8f5e9, #f1f8e9);
        border-left: 5px solid #4caf50;
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
        font-size: 1.05rem;
        line-height: 1.8;
        color: #1b5e20;
    }

    /* --- Correct Answer --- */
    .correct-box {
        background: linear-gradient(145deg, #e8f5e9, #c8e6c9);
        border-left: 5px solid #2e7d32;
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
        text-align: center;
    }

    /* --- Wrong Answer --- */
    .wrong-box {
        background: linear-gradient(145deg, #fff3e0, #ffe0b2);
        border-left: 5px solid #f57c00;
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
    }

    /* --- Story Box --- */
    .story-box {
        background: linear-gradient(145deg, #fff8e1, #fff3e0);
        border: 2px solid #ffe082;
        border-radius: 20px;
        padding: 2rem;
        margin-top: 1rem;
        font-size: 1.05rem;
        line-height: 2;
        color: #4e342e;
        box-shadow: 0 4px 20px rgba(255, 193, 7, 0.15);
    }

    /* --- Arabic Text --- */
    .arabic-text {
        font-size: 1.8rem;
        text-align: right;
        direction: rtl;
        color: #1a237e;
        padding: 1rem;
        background: linear-gradient(145deg, #e8eaf6, #c5cae9);
        border-radius: 12px;
        margin: 0.5rem 0;
        line-height: 2.2;
        font-family: 'Traditional Arabic', 'Scheherazade New', serif;
    }

    /* --- Word Highlight (correct) --- */
    .word-correct {
        color: #2e7d32;
        font-weight: 700;
        background: #e8f5e9;
        padding: 2px 6px;
        border-radius: 6px;
        display: inline-block;
        margin: 2px;
    }

    /* --- Word Highlight (wrong) --- */
    .word-wrong {
        color: #c62828;
        font-weight: 700;
        background: #ffebee;
        padding: 2px 6px;
        border-radius: 6px;
        text-decoration: line-through;
        display: inline-block;
        margin: 2px;
    }

    /* --- Word Highlight (missing) --- */
    .word-missing {
        color: #e65100;
        font-weight: 700;
        background: #fff3e0;
        padding: 2px 6px;
        border-radius: 6px;
        display: inline-block;
        margin: 2px;
        font-style: italic;
    }

    /* --- Info Box --- */
    .info-box {
        background: linear-gradient(145deg, #e3f2fd, #bbdefb);
        border-left: 5px solid #1976d2;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 1rem 0;
        font-size: 0.95rem;
        color: #0d47a1;
    }

    /* --- Emoji Section Headers --- */
    .section-emoji {
        font-size: 3rem;
        text-align: center;
        margin-bottom: 0.5rem;
    }

    /* --- Footer --- */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #81c784;
        font-size: 0.9rem;
        margin-top: 3rem;
        border-top: 2px solid #e8f5e9;
    }

    .stAudio {
        margin-top: 0.6rem;
    }

    .stAudio audio {
        width: 100%;
        min-height: 42px;
        border-radius: 10px;
    }

    /* hide Streamlit default footer & hamburger */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Button styling */
    .stButton > button {
        border-radius: 14px;
        font-weight: 700;
        padding: 0.6rem 2rem;
        min-height: 46px;
        font-size: 1rem;
        transition: all 0.3s ease;
        border: none;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    }

    /* Selectbox styling */
    .stSelectbox > div > div {
        border-radius: 12px;
        border: 2px solid #c8e6c9;
    }

    /* Text area styling */
    .stTextArea > div > div > textarea {
        border-radius: 12px;
        border: 2px solid #c8e6c9;
        font-family: 'Noto Sans Bengali', sans-serif;
        font-size: 1rem;
    }

    /* Text input styling */
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 2px solid #c8e6c9;
        font-family: 'Noto Sans Bengali', sans-serif;
        font-size: 1rem;
    }

    .stTextArea textarea:focus,
    .stTextInput input:focus {
        border-color: var(--brand-green) !important;
        box-shadow: 0 0 0 0.15rem rgba(46, 125, 50, 0.15);
    }

    @media (max-width: 992px) {
        .main-header h1 {
            font-size: 2.1rem;
        }

        .main-header p {
            font-size: 1rem;
        }

        .stTabs [data-baseweb="tab"] {
            padding: 12px 18px;
            font-size: 1rem;
        }
    }

    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.9rem;
            padding-right: 0.9rem;
        }

        .main-header {
            padding: 1.4rem 1rem;
            border-radius: 14px;
            margin-bottom: 1.1rem;
        }

        .main-header h1 {
            font-size: 1.85rem;
            margin-bottom: 0.2rem;
        }

        .section-emoji {
            font-size: 2.2rem;
        }

        .stTabs [data-baseweb="tab-list"] {
            justify-content: flex-start;
            overflow-x: auto;
            scrollbar-width: thin;
            padding: 0 0.2rem 0.4rem;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 12px;
            padding: 10px 14px;
            min-height: 44px;
            white-space: nowrap;
            font-size: 0.95rem;
        }

        .response-box,
        .correct-box,
        .wrong-box,
        .story-box,
        .info-box,
        .arabic-text {
            padding: 1rem;
            border-radius: 10px;
        }

        .arabic-text {
            font-size: 1.5rem;
            line-height: 1.9;
        }

        .stButton > button {
            width: 100%;
        }
    }

    @media (max-width: 420px) {
        .main-header h1 {
            font-size: 1.55rem;
        }

        .main-header p {
            font-size: 0.9rem;
        }

        .stTabs [data-baseweb="tab"] {
            font-size: 0.88rem;
            padding: 9px 12px;
        }

        .footer {
            font-size: 0.82rem;
            padding: 1.3rem 0.3rem;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)


st.markdown(
    """
<div class="main-header">
    <h1>🕌 AI মাদ্রাসা</h1>
    <p>ছোটদের জন্য ইসলামিক শিক্ষা ব্যবস্থা — AI দ্বারা পরিচালিত</p>
</div>
""",
    unsafe_allow_html=True,
)

# API key warning
if not check_api_key():
    st.warning(
        "⚠️ Gemini API কী সেট করা হয়নি। অনুগ্রহ করে `.env` ফাইলে `GEMINI_API_KEY` সেট করুন।\n\n"
        "➡️ API কী পেতে যান: https://aistudio.google.com/apikey"
    )

tab1, tab2, tab3 = st.tabs(
    ["📖 AI শিক্ষক", "🕋 কুরআন অনুশীলন", "📚 ইসলামিক গল্প"]
)

with tab1:
    st.markdown('<div class="section-emoji">🧑‍🏫</div>', unsafe_allow_html=True)
    st.markdown(
        "<h2 style='text-align:center; color:#2e7d32;'>AI শিক্ষক — তোমার প্রশ্ন জিজ্ঞাসা করো!</h2>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class="info-box">
        💡 <strong>কিভাবে ব্যবহার করবে:</strong> লিখে বা মাইকে বলে প্রশ্ন করতে পারো।
        AI শিক্ষক সহজ বাংলায় উত্তর দেবে! ইসলাম, নামাজ, দোয়া, আদব — যেকোনো বিষয়ে জিজ্ঞাসা করতে পারো।
    </div>
    """,
        unsafe_allow_html=True,
    )

    # System instruction for the AI Teacher
    TEACHER_SYSTEM = """
তুমি একজন দয়ালু ও জ্ঞানী ইসলামিক শিক্ষক। তোমার নাম "উস্তাদ AI"।
তুমি বাংলাদেশের ৫-১০ বছর বয়সী ছোট বাচ্চাদের ইসলাম শেখাও।

নিয়ম:
- সবসময় সহজ বাংলায় উত্তর দাও
- উত্তর ছোট এবং বোধগম্য রাখো (৩-৫ বাক্যে)
- ইসলামিক শিক্ষা এবং মূল্যবোধ অনুসারে উত্তর দাও
- কুরআন বা হাদিস থেকে সরাসরি উদ্ধৃতি দিতে গেলে শুধু সেগুলোই দাও যা তুমি নিশ্চিত
- যদি কোনো বিষয়ে নিশ্চিত না হও, বলো "এটা আমি নিশ্চিত নই, তোমার উস্তাদ/আব্বু/আম্মুকে জিজ্ঞাসা করো"
- সবসময় উৎসাহব্যঞ্জক এবং বন্ধুত্বপূর্ণ ভাষা ব্যবহার করো
- ইমোজি ব্যবহার করো যেন বাচ্চাদের ভালো লাগে
- অনৈসলামিক বা অনুপযুক্ত প্রশ্নের উত্তর দেওয়া থেকে বিরত থাকো
"""

    # Text input for the question
    user_question = st.text_area(
        "তোমার প্রশ্ন লেখো:",
        placeholder="উদাহরণ: নামাজ কেন পড়তে হয়?",
        height=100,
        key="teacher_input",
    )
    voice_question = get_audio_input("🎙️ অথবা মাইকে প্রশ্ন বলো:", key="teacher_voice")

    col1, col2 = st.columns([1, 3])
    with col1:
        ask_button = st.button("🎤 জিজ্ঞাসা করো", type="primary", use_container_width=True)

    if ask_button:
        question_to_ask = user_question.strip()

        if not question_to_ask and voice_question:
            with st.spinner("🎧 তোমার কথা লেখা হচ্ছে..."):
                question_to_ask = transcribe_audio(voice_question, "ছোট বাচ্চার ইসলামিক প্রশ্ন")
            if question_to_ask:
                st.success(f"🗣️ তুমি বলেছো: {question_to_ask}")

        if not question_to_ask:
            st.info("📝 প্রথমে প্রশ্ন লিখো বা মাইকে বলে রেকর্ড করো!")
        else:
            with st.spinner("🤔 উস্তাদ AI ভাবছে..."):
                prompt = f"একজন ছোট বাচ্চা জিজ্ঞাসা করছে: {question_to_ask}"
                response = get_gemini_response(prompt, TEACHER_SYSTEM)

            st.markdown(
                f"""
            <div class="response-box">
                <strong>🧑‍🏫 উস্তাদ AI বলছে:</strong><br><br>
                {response}
            </div>
            """,
                unsafe_allow_html=True,
            )

            try:
                st.audio(build_tts_audio(response, lang="bn"), format="audio/mp3")
                st.caption("🔊 উপরের প্লেয়ার থেকে উত্তর শুনতে পারো")
            except Exception:
                st.caption("⚠️ এই মুহূর্তে ভয়েস প্লেব্যাক চালু করা যায়নি")


with tab2:
    st.markdown('<div class="section-emoji">📖</div>', unsafe_allow_html=True)
    st.markdown(
        "<h2 style='text-align:center; color:#1a237e;'>কুরআন অনুশীলন — আয়াত মুখস্থ করো!</h2>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class="info-box">
        💡 <strong>কিভাবে ব্যবহার করবে:</strong> নিচে থেকে একটি আয়াত বাছাই করো।
        তারপর বাংলা উচ্চারণ লিখে বা মাইকে বলে "যাচাই করো" বাটনে ক্লিক করো।
        সঠিক হলে সবুজ ✅ আর ভুল হলে কোথায় ভুল হয়েছে দেখাবে! 🔍
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Ayah selection
    selected_ayah = st.selectbox(
        "📜 আয়াত বাছাই করো:",
        options=list(QURAN_AYAHS.keys()),
        key="quran_select",
    )

    ayah_data = QURAN_AYAHS[selected_ayah]

    # Show the Arabic text and meaning
    st.markdown(
        f'<div class="arabic-text">{ayah_data["arabic"]}</div>',
        unsafe_allow_html=True,
    )

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(f"**🔤 বাংলা উচ্চারণ:** {ayah_data['bangla']}")
    with col_m2:
        st.markdown(f"**📖 অর্থ:** {ayah_data['meaning']}")

    st.markdown("---")

    # User input for recitation
    user_recitation = st.text_input(
        "তুমি বাংলা উচ্চারণ লেখো:",
        placeholder=f"উদাহরণ: {ayah_data['bangla']}",
        key="quran_input",
    )
    voice_recitation = get_audio_input("🎙️ অথবা মাইকে উচ্চারণ বলো:", key="quran_voice")

    check_button = st.button("✅ যাচাই করো", type="primary", key="quran_check")

    if check_button:
        recitation_text = user_recitation.strip()

        if not recitation_text and voice_recitation:
            with st.spinner("🎧 তোমার তিলাওয়াত লেখা হচ্ছে..."):
                recitation_text = transcribe_audio(voice_recitation, "কুরআনের বাংলা উচ্চারণ")
            if recitation_text:
                st.success(f"🗣️ তুমি বলেছো: {recitation_text}")

        if not recitation_text:
            st.info("📝 প্রথমে বাংলা উচ্চারণ লেখো বা মাইকে বলে রেকর্ড করো!")
        else:
            result = compare_ayah(recitation_text, ayah_data["bangla"])

            if result["is_correct"]:
                st.balloons()
                st.markdown(
                    """
                <div class="correct-box">
                    <h3>✅ মাশাআল্লাহ! একদম সঠিক! 🌟</h3>
                    <p>তুমি খুব ভালো করেছো! এভাবে চেষ্টা চালিয়ে যাও! 💚</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                <div class="wrong-box">
                    <h3>🔍 আরেকটু চেষ্টা করো! ({result['mistakes']}টি শব্দে ভুল)</h3>
                    <p>নিচে দেখো কোথায় ভুল হয়েছে:</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                # Word-by-word comparison display
                comparison_html = "<div style='margin-top:1rem; padding:1rem; background:#fafafa; border-radius:12px;'>"
                comparison_html += "<p><strong>তোমার উত্তর:</strong> "
                for item in result["details"]:
                    if item["match"]:
                        comparison_html += f'<span class="word-correct">{item["user"]}</span> '
                    elif item["user"]:
                        comparison_html += f'<span class="word-wrong">{item["user"]}</span> '
                    else:
                        comparison_html += f'<span class="word-missing">(বাদ পড়েছে)</span> '
                comparison_html += "</p>"

                comparison_html += "<p><strong>সঠিক উত্তর:</strong> "
                for item in result["details"]:
                    if item["match"]:
                        comparison_html += f'<span class="word-correct">{item["correct"]}</span> '
                    else:
                        comparison_html += f'<span class="word-missing">{item["correct"]}</span> '
                comparison_html += "</p></div>"

                st.markdown(comparison_html, unsafe_allow_html=True)

                st.info(f"💪 আবার চেষ্টা করো! সঠিক উচ্চারণ: **{ayah_data['bangla']}**")

with tab3:
    st.markdown('<div class="section-emoji">📚</div>', unsafe_allow_html=True)
    st.markdown(
        "<h2 style='text-align:center; color:#e65100;'>ইসলামিক গল্প — গল্প শোনো!</h2>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class="info-box">
        💡 <strong>কিভাবে ব্যবহার করবে:</strong> নিচে থেকে একটি গল্পের বিষয় বাছাই করো
        অথবা নিজে লিখে/মাইকে বলে একটি বিষয় দাও। তারপর "গল্প শোনাও" বাটনে ক্লিক করো! 📖
    </div>
    """,
        unsafe_allow_html=True,
    )

    # System instruction for the Story Teller
    STORY_SYSTEM = """
তুমি একজন দক্ষ ইসলামিক গল্পকার। তুমি বাংলাদেশের ৫-১০ বছর বয়সী বাচ্চাদের জন্য ইসলামিক গল্প বলো।

নিয়ম:
- গল্প সহজ বাংলায় লেখো
- গল্প ৮-১২ বাক্যের মধ্যে রাখো
- গল্পে ইসলামিক নৈতিক শিক্ষা থাকতে হবে
- গল্পের শেষে "🌟 শিক্ষা:" দিয়ে নৈতিক শিক্ষা লেখো
- ইমোজি ব্যবহার করো যেন বাচ্চাদের মজা লাগে
- কুরআন বা হাদিসের মনগড়া উদ্ধৃতি দিও না
- গল্প যেন ইসলামিক মূল্যবোধের সাথে সামঞ্জস্যপূর্ণ হয়
- নবী-রাসূলদের গল্প বলতে গেলে শুধু প্রসিদ্ধ ও সর্বজনবিদিত ঘটনা বলো
- গল্পের শুরুতে একটি সুন্দর শিরোনাম দাও
"""

    # Story topic selection
    story_option = st.radio(
        "গল্পের ধরন বাছাই করো:",
        ["📋 তালিকা থেকে বাছাই করো", "✏️ নিজে বিষয় লেখো"],
        horizontal=True,
        key="story_option",
    )

    if story_option == "📋 তালিকা থেকে বাছাই করো":
        selected_topic = st.selectbox(
            "🎯 গল্পের বিষয়:",
            options=STORY_TOPICS,
            key="story_select",
        )
        story_topic = selected_topic
    else:
        story_topic = st.text_input(
            "✏️ গল্পের বিষয় লেখো:",
            placeholder="উদাহরণ: একজন সৎ ছেলের গল্প",
            key="story_custom",
        )

    voice_story_topic = get_audio_input("🎙️ অথবা মাইকে গল্পের বিষয় বলো:", key="story_voice")

    story_button = st.button("📖 গল্প শোনাও!", type="primary", use_container_width=True)

    if story_button:
        topic_to_use = story_topic.strip() if isinstance(story_topic, str) else ""

        if story_option == "✏️ নিজে বিষয় লেখো" and not topic_to_use and voice_story_topic:
            with st.spinner("🎧 বিষয়টি লেখা হচ্ছে..."):
                topic_to_use = transcribe_audio(voice_story_topic, "বাচ্চাদের গল্পের বিষয়")
            if topic_to_use:
                st.success(f"🗣️ তুমি বিষয় বলেছো: {topic_to_use}")

        if not topic_to_use:
            st.info("📝 প্রথমে গল্পের বিষয় লেখো বা মাইকে বলে রেকর্ড করো!")
        else:
            with st.spinner("📝 গল্প লেখা হচ্ছে... একটু অপেক্ষা করো! ✨"):
                prompt = f"ছোট বাচ্চাদের জন্য একটি ইসলামিক গল্প লেখো। বিষয়: {topic_to_use}"
                story = get_gemini_response(prompt, STORY_SYSTEM)

            st.markdown(
                f"""
            <div class="story-box">
                {story}
            </div>
            """,
                unsafe_allow_html=True,
            )

            try:
                st.audio(build_tts_audio(story, lang="bn"), format="audio/mp3")
                st.caption("🔊 উপরের প্লেয়ার থেকে গল্প শুনতে পারো")
            except Exception:
                st.caption("⚠️ এই মুহূর্তে ভয়েস প্লেব্যাক চালু করা যায়নি")

            # Option to generate another story
            st.markdown("---")
            st.info("🔄 আরেকটি গল্প শুনতে চাইলে উপরে থেকে নতুন বিষয় বাছাই করে আবার বাটনে ক্লিক করো!")

