import html
import os
import re
import tempfile
from io import BytesIO

import librosa
import noisereduce as nr
import soundfile as sf
import speech_recognition as sr
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from gtts import gTTS


load_dotenv()

GROQ_API_KEY = (os.getenv("GROQ_API_KEY") or "").strip()
GROQ_MODEL = (os.getenv("GROQ_MODEL") or "llama-3.1-8b-instant").strip()
GROQ_MAX_TOKENS = int((os.getenv("GROQ_MAX_TOKENS") or "1024").strip())
GROQ_CONTINUATION_ROUNDS = int((os.getenv("GROQ_CONTINUATION_ROUNDS") or "2").strip())

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
- অনৈসলামিক বা অনুপযুক্ত প্রশ্নের উত্তর দেওয়া থেকে বিরত থাকো
"""

STORY_SYSTEM = """
তুমি একজন দক্ষ ইসলামিক গল্পকার। তুমি বাংলাদেশের ৫-১০ বছর বয়সী বাচ্চাদের জন্য ইসলামিক গল্প বলো।

নিয়ম:
- গল্প সহজ বাংলায় লেখো
- গল্প ৮-১২ বাক্যের মধ্যে রাখো
- গল্পে ইসলামিক নৈতিক শিক্ষা থাকতে হবে
- গল্পের শেষে "শিক্ষা:" দিয়ে নৈতিক শিক্ষা লেখো
- কোনো ইমোজি ব্যবহার করবে না
- কোনো Markdown ফরম্যাটিং (যেমন **, #, -, 1.) ব্যবহার করবে না
- কুরআন বা হাদিসের মনগড়া উদ্ধৃতি দিও না
- গল্প যেন ইসলামিক মূল্যবোধের সাথে সামঞ্জস্যপূর্ণ হয়
- নবী-রাসূলদের গল্প বলতে গেলে শুধু প্রসিদ্ধ ও সর্বজনবিদিত ঘটনা বলো
- গল্পের শুরুতে একটি সুন্দর শিরোনাম দাও
"""


@st.cache_resource(show_spinner=False)
def get_groq_client() -> Groq | None:
    if not GROQ_API_KEY:
        return None
    try:
        return Groq(api_key=GROQ_API_KEY)
    except Exception:
        return None


def check_groq_ready() -> bool:
    return get_groq_client() is not None


def get_ai_response(prompt: str, system_instruction: str = "") -> str:
    client = get_groq_client()
    if client is None:
        return "`.env` ফাইলে `GROQ_API_KEY` সেট করা নেই।"

    try:
        messages = [
            {"role": "system", "content": system_instruction.strip()},
            {"role": "user", "content": prompt.strip()},
        ]
        parts = []

        for _ in range(max(1, GROQ_CONTINUATION_ROUNDS + 1)):
            completion = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=0.5,
                max_tokens=max(200, GROQ_MAX_TOKENS),
            )

            choice = completion.choices[0]
            generated_part = (choice.message.content or "").strip()
            finish_reason = (choice.finish_reason or "").strip().lower()

            if generated_part:
                parts.append(generated_part)
                messages.append({"role": "assistant", "content": generated_part})

            if finish_reason != "length":
                break

            messages.append(
                {
                    "role": "user",
                    "content": "Continue from where you stopped. Do not repeat previous sentences.",
                }
            )

        final_text = "\n".join(part for part in parts if part).strip()
        return final_text or "AI থেকে উত্তর পাওয়া যায়নি।"
    except Exception as e:
        return f"Groq API ত্রুটি: {str(e)}"


def _denoise_audio_to_wav(audio_bytes: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as src_file:
        src_file.write(audio_bytes)
        src_path = src_file.name

    denoised_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    denoised_path = denoised_file.name
    denoised_file.close()

    signal, sample_rate = librosa.load(src_path, sr=None)
    reduced_signal = nr.reduce_noise(y=signal, sr=sample_rate)
    sf.write(denoised_path, reduced_signal, sample_rate)

    try:
        os.remove(src_path)
    except OSError:
        pass

    return denoised_path


def transcribe_audio(uploaded_audio, hint: str) -> str:
    if uploaded_audio is None:
        return ""

    try:
        del hint
        recognizer = sr.Recognizer()
        audio_bytes = uploaded_audio.getvalue()
        clean_wav_path = _denoise_audio_to_wav(audio_bytes)

        with sr.AudioFile(clean_wav_path) as source:
            audio_data = recognizer.record(source)

        try:
            text = recognizer.recognize_google(audio_data, language="bn-BD").strip()
        except sr.UnknownValueError:
            text = ""
        except sr.RequestError:
            text = ""

        try:
            os.remove(clean_wav_path)
        except OSError:
            pass

        return text
    except Exception:
        return ""


@st.cache_data(show_spinner=False)
def build_tts_audio(text: str, lang: str = "bn") -> bytes:
    if not text.strip():
        return b""

    try:
        buf = BytesIO()
        gTTS(text=text, lang="bn" if lang == "bn" else "en", slow=False).write_to_fp(buf)
        return buf.getvalue()
    except Exception:
        return b""


def render_tts_player(text: str, lang: str = "bn", caption: str = "শুনতে প্লে করো"):
    audio_bytes = build_tts_audio(text, lang=lang)
    if audio_bytes:
        st.audio(audio_bytes, format="audio/mp3")
        st.caption(caption)
    else:
        st.caption("এই মুহূর্তে ভয়েস প্লেব্যাক চালু করা যায়নি")


def sanitize_story_text(text: str) -> str:
    if not text:
        return ""

    cleaned = text.replace("**", "").replace("__", "")
    cleaned = re.sub(r"`{1,3}", "", cleaned)
    cleaned = re.sub(r"^\s{0,3}#{1,6}\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*[-*+]\s+", " ", cleaned)
    cleaned = re.sub(r"\s*\d+\.\s+", " ", cleaned)
    cleaned = re.sub(r"[\U0001F300-\U0001FAFF\U00002700-\U000027BF\U0001F1E6-\U0001F1FF]", "", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned).strip()
    return cleaned


def get_audio_input(label: str, key: str):
    audio_input_fn = getattr(st, "audio_input", None)
    if callable(audio_input_fn):
        return audio_input_fn(label, key=key)
    st.caption("ভয়েস ইনপুট ব্যবহার করতে Streamlit 1.39+ দরকার")
    return None


def compare_ayah(user_input: str, correct_text: str) -> dict:
    user_words = user_input.strip().split()
    correct_words = correct_text.strip().split()

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

    return {
        "is_correct": mistakes == 0,
        "mistakes": mistakes,
        "total_words": len(correct_words),
        "details": results,
    }


st.set_page_config(page_title="AI মাদ্রাসা", page_icon="🕌", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
<style>
    :root {
        --ink: #1e2433;
        --muted: #5b6378;
        --brand-primary: #005f73;
        --brand-secondary: #0a9396;
        --brand-accent: #ee9b00;
        --paper: rgba(255, 255, 255, 0.9);
        --line: rgba(30, 36, 51, 0.14);
        --shadow: 0 10px 30px rgba(24, 35, 52, 0.14);
    }

    @import url('https://fonts.googleapis.com/css2?family=Anek+Bangla:wght@400;500;700;800&family=Sora:wght@500;700&display=swap');

    html, body, [data-testid="stAppViewContainer"], .stApp {
        height: 100vh;
        overflow: hidden;
    }

    .stApp {
        font-family: 'Anek Bangla', sans-serif;
        color: var(--ink);
        background:
            radial-gradient(circle at 15% 10%, rgba(0, 95, 115, 0.16), transparent 38%),
            radial-gradient(circle at 90% 12%, rgba(238, 155, 0, 0.2), transparent 36%),
            linear-gradient(150deg, #f4fbfc 0%, #fff8ec 52%, #eef3ff 100%);
    }

    .block-container {
        max-width: 1240px;
        height: 100vh;
        padding-top: 0.6rem;
        padding-bottom: 0.55rem;
        display: flex;
        flex-direction: column;
        gap: 0.45rem;
    }

    .main-header {
        background: linear-gradient(118deg, #084b60 0%, #0a9396 56%, #ee9b00 100%);
        color: #ffffff;
        padding: 1.05rem 1.1rem;
        border-radius: 22px 22px 22px 8px;
        text-align: left;
        margin-bottom: 0.4rem;
        box-shadow: 0 16px 34px rgba(8, 75, 96, 0.25);
        position: relative;
        overflow: hidden;
    }

    .main-header::before {
        content: '';
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at 20% 20%, rgba(255,255,255,0.18), transparent 36%);
        opacity: 0.9;
    }

    .main-header h1 {
        font-family: 'Sora', sans-serif;
        font-size: 1.95rem;
        font-weight: 800;
        margin-bottom: 0.08rem;
        letter-spacing: 0.2px;
        position: relative;
    }

    .main-header p {
        font-size: 0.9rem;
        opacity: 0.94;
        position: relative;
        max-width: 840px;
    }

    .hero-metrics {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        margin-top: 0.55rem;
        position: relative;
        z-index: 2;
    }

    .metric-pill {
        background: rgba(255, 255, 255, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.38);
        border-radius: 999px;
        padding: 0.2rem 0.65rem;
        font-size: 0.78rem;
        letter-spacing: 0.2px;
    }

    .top-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.65rem;
        margin: 0.15rem 0 0.45rem;
    }

    .mode-card {
        border: 1px solid var(--line);
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.84);
        padding: 0.72rem 0.8rem;
        box-shadow: var(--shadow);
    }

    .mode-card h4 {
        margin: 0;
        color: #13344e;
        font-size: 0.92rem;
        font-family: 'Sora', sans-serif;
    }

    .mode-card p {
        margin: 0.18rem 0 0;
        color: var(--muted);
        font-size: 0.8rem;
        line-height: 1.35;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        justify-content: center;
        border-bottom: 1px dashed var(--line);
        padding: 0.15rem 0.1rem 0.45rem;
        flex-wrap: wrap;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.84);
        border-radius: 10px;
        padding: 8px 15px;
        font-size: 0.92rem;
        font-weight: 700;
        border: 1px solid var(--line);
        transition: all 0.2s ease;
        color: #12324a;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(10, 147, 150, 0.14);
        transform: translateY(-2px);
        box-shadow: 0 8px 14px rgba(24, 35, 52, 0.14);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(120deg, #005f73, #0a9396) !important;
        color: white !important;
        border-color: transparent !important;
        box-shadow: 0 10px 20px rgba(0, 95, 115, 0.28);
    }

    [data-baseweb="tab-panel"] {
        height: calc(100vh - 190px);
        overflow-y: auto;
        padding: 0.2rem 0.2rem 1rem;
        scrollbar-width: thin;
    }

    .section-title {
        text-align: center;
        margin: 0.1rem 0 0.2rem;
        color: #173d57;
        font-family: 'Sora', sans-serif;
        font-size: 1.15rem;
        letter-spacing: 0.2px;
    }

    .response-box,
    .correct-box,
    .wrong-box,
    .story-box,
    .info-box,
    .arabic-text {
        border: 1px solid var(--line);
        backdrop-filter: blur(5px);
        background: var(--paper);
        box-shadow: var(--shadow);
    }

    .response-box {
        border-left: 5px solid var(--brand-primary);
        border-radius: 12px;
        padding: 1rem;
        margin-top: 0.6rem;
        font-size: 0.98rem;
        line-height: 1.6;
        color: #24384e;
    }

    .correct-box {
        border-left: 5px solid #2a9d8f;
        border-radius: 12px;
        padding: 1rem;
        margin-top: 0.6rem;
        text-align: center;
    }

    .wrong-box {
        border-left: 5px solid #ca6702;
        border-radius: 12px;
        padding: 1rem;
        margin-top: 0.6rem;
    }

    .story-box {
        border-radius: 14px;
        padding: 1.1rem;
        margin-top: 0.6rem;
        font-size: 1rem;
        line-height: 1.75;
        color: #2d3344;
        box-shadow: 0 14px 22px rgba(24, 35, 52, 0.12);
        white-space: pre-wrap;
    }

    .arabic-text {
        font-size: 1.45rem;
        text-align: right;
        direction: rtl;
        color: #15244a;
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        line-height: 2;
        font-family: 'Traditional Arabic', 'Scheherazade New', serif;
    }

    .word-correct {
        color: #1f8a57;
        font-weight: 700;
        background: #e4f8eb;
        padding: 2px 6px;
        border-radius: 6px;
        display: inline-block;
        margin: 2px;
    }

    .word-wrong {
        color: #b42334;
        font-weight: 700;
        background: #ffe8ea;
        padding: 2px 6px;
        border-radius: 6px;
        text-decoration: line-through;
        display: inline-block;
        margin: 2px;
    }

    .word-missing {
        color: #a45d08;
        font-weight: 700;
        background: #fff2de;
        padding: 2px 6px;
        border-radius: 6px;
        display: inline-block;
        margin: 2px;
        font-style: italic;
    }

    .info-box {
        border-left: 5px solid #0a9396;
        border-radius: 12px;
        padding: 0.9rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        color: #254a67;
    }

    .section-emoji {
        font-size: 1.35rem;
        text-align: center;
        margin-bottom: 0.05rem;
        color: #335a73;
    }

    .stAudio audio {
        width: 100%;
        min-height: 40px;
        border-radius: 11px;
        border: 1px solid rgba(0, 95, 115, 0.25);
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .stButton > button {
        border-radius: 11px;
        font-weight: 700;
        letter-spacing: 0.2px;
        padding: 0.5rem 1.2rem;
        min-height: 42px;
        font-size: 0.95rem;
        transition: all 0.22s ease;
        border: 1px solid rgba(0, 95, 115, 0.24);
        background: linear-gradient(120deg, #005f73, #0a9396) !important;
        color: #fff !important;
        box-shadow: 0 8px 16px rgba(0, 95, 115, 0.26);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 22px rgba(0, 95, 115, 0.28);
    }

    .stSelectbox > div > div,
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stRadio > div {
        background: rgba(255, 255, 255, 0.92);
        border-radius: 12px;
        border: 1px solid var(--line);
        color: var(--ink);
    }

    .stTextArea > div > div > textarea {
        font-family: 'Anek Bangla', sans-serif;
        font-size: 1rem;
    }

    .stTextArea textarea:focus,
    .stTextInput input:focus {
        border-color: #0a9396 !important;
        box-shadow: 0 0 0 0.15rem rgba(10, 147, 150, 0.16);
    }

    @media (max-width: 992px) {
        .main-header h1 { font-size: 1.52rem; }
        .main-header p { font-size: 0.8rem; }
        .stTabs [data-baseweb="tab"] { padding: 7px 12px; font-size: 0.88rem; }
        [data-baseweb="tab-panel"] { height: calc(100vh - 175px); }
    }

    @media (max-width: 768px) {
        .block-container { padding-left: 0.7rem; padding-right: 0.7rem; }
        .main-header { padding: 0.7rem 0.62rem; border-radius: 12px; margin-bottom: 0.5rem; }
        .main-header h1 { font-size: 1.22rem; margin-bottom: 0.2rem; }
        .hero-metrics { gap: 0.3rem; }
        .metric-pill { font-size: 0.72rem; }
        .top-grid { grid-template-columns: 1fr; gap: 0.4rem; }
        .mode-card h4 { font-size: 0.88rem; }
        .mode-card p { font-size: 0.78rem; }
        .stTabs [data-baseweb="tab-list"] {
            justify-content: flex-start;
            overflow-x: auto;
            scrollbar-width: thin;
            padding: 0 0.2rem 0.4rem;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 10px;
            padding: 7px 10px;
            min-height: 40px;
            white-space: nowrap;
            font-size: 0.83rem;
        }
        [data-baseweb="tab-panel"] { height: calc(100vh - 165px); }
        .response-box, .correct-box, .wrong-box, .story-box, .info-box, .arabic-text {
            padding: 0.9rem;
            border-radius: 10px;
        }
        .arabic-text { font-size: 1.25rem; line-height: 1.6; }
        .stButton > button { width: 100%; }
    }

    @media (max-width: 420px) {
        .main-header h1 { font-size: 1.08rem; }
        .main-header p { font-size: 0.72rem; }
        .stTabs [data-baseweb="tab"] { font-size: 0.73rem; padding: 6px 9px; }
        [data-baseweb="tab-panel"] { height: calc(100vh - 154px); }
    }
</style>
""",
    unsafe_allow_html=True,
)


def render_top_overview():
    st.markdown(
        """
<div class="main-header">
    <h1>AI মাদ্রাসা স্টুডিও</h1>
    <p>এক স্ক্রিনে স্মার্ট ইসলামিক শেখা: প্রশ্ন করো, কুরআন অনুশীলন করো, আর পরিষ্কার গল্প তৈরি করো।</p>
    <div class="hero-metrics">
        <span class="metric-pill">Groq AI চালিত</span>
        <span class="metric-pill">STT + TTS ইন্টিগ্রেটেড</span>
        <span class="metric-pill">মোবাইল রেসপনসিভ</span>
    </div>
</div>
<div class="top-grid">
    <div class="mode-card">
        <h4>AI শিক্ষক</h4>
        <p>টেক্সট বা ভয়েসে প্রশ্ন করো, ছোট ও স্পষ্ট উত্তরে বুঝে নাও।</p>
    </div>
    <div class="mode-card">
        <h4>কুরআন অনুশীলন</h4>
        <p>উচ্চারণ মিলিয়ে দেখো, ভুল শব্দ চিহ্নিত করো, সাথে সাথে ফিডব্যাক শোনো।</p>
    </div>
    <div class="mode-card">
        <h4>ইসলামিক গল্প</h4>
        <p>বিষয় দাও, plain-text গল্প নাও, আর ভয়েসে শুনে শেখা সম্পূর্ণ করো।</p>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_teacher_tab():
    st.markdown('<div class="section-emoji">শিক্ষক</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">AI শিক্ষক</div>', unsafe_allow_html=True)
    st.markdown('<div class="info-box">লিখে বা মাইকে বলে প্রশ্ন করতে পারো। AI শিক্ষক সহজ বাংলায় ছোট উত্তর দেবে।</div>', unsafe_allow_html=True)

    user_question = st.text_area("তোমার প্রশ্ন লেখো:", placeholder="উদাহরণ: নামাজ কেন পড়তে হয়?", height=90, key="teacher_input")
    voice_question = get_audio_input("অথবা মাইকে প্রশ্ন বলো:", key="teacher_voice")
    ask_button = st.button("জিজ্ঞাসা করো", type="primary", use_container_width=True)

    if not ask_button:
        return

    question_to_ask = user_question.strip()
    if not question_to_ask and voice_question:
        with st.spinner("তোমার কথা লেখা হচ্ছে..."):
            question_to_ask = transcribe_audio(voice_question, "ছোট বাচ্চার ইসলামিক প্রশ্ন")
        if question_to_ask:
            st.success(f"তুমি বলেছো: {question_to_ask}")

    if not question_to_ask:
        st.info("প্রথমে প্রশ্ন লিখো বা মাইকে রেকর্ড করো।")
        return

    with st.spinner("উস্তাদ AI ভাবছে..."):
        prompt = f"একজন ছোট বাচ্চা জিজ্ঞাসা করছে: {question_to_ask}"
        response = get_ai_response(prompt, TEACHER_SYSTEM)

    st.markdown(f'<div class="response-box"><strong>উস্তাদ AI বলছে:</strong><br><br>{html.escape(response)}</div>', unsafe_allow_html=True)
    render_tts_player(response, lang="bn", caption="উত্তর শুনতে প্লে করো")


def render_quran_tab():
    st.markdown('<div class="section-emoji">কুরআন</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">কুরআন অনুশীলন</div>', unsafe_allow_html=True)
    st.markdown('<div class="info-box">একটি আয়াত বেছে নাও, বাংলা উচ্চারণ লিখে বা বলে যাচাই করো।</div>', unsafe_allow_html=True)

    selected_ayah = st.selectbox("আয়াত বাছাই করো:", options=list(QURAN_AYAHS.keys()), key="quran_select")
    ayah_data = QURAN_AYAHS[selected_ayah]

    st.markdown(f'<div class="arabic-text">{ayah_data["arabic"]}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**বাংলা উচ্চারণ:** {ayah_data['bangla']}")
    with c2:
        st.markdown(f"**অর্থ:** {ayah_data['meaning']}")

    render_tts_player(
        f"{selected_ayah}. বাংলা উচ্চারণ: {ayah_data['bangla']}. অর্থ: {ayah_data['meaning']}",
        lang="bn",
        caption="উচ্চারণ ও অর্থ শুনতে পারো",
    )

    user_recitation = st.text_input("তুমি বাংলা উচ্চারণ লেখো:", placeholder=f"উদাহরণ: {ayah_data['bangla']}", key="quran_input")
    voice_recitation = get_audio_input("অথবা মাইকে উচ্চারণ বলো:", key="quran_voice")
    check_button = st.button("যাচাই করো", type="primary", key="quran_check")

    if not check_button:
        return

    recitation_text = user_recitation.strip()
    if not recitation_text and voice_recitation:
        with st.spinner("তোমার তিলাওয়াত লেখা হচ্ছে..."):
            recitation_text = transcribe_audio(voice_recitation, "কুরআনের বাংলা উচ্চারণ")
        if recitation_text:
            st.success(f"তুমি বলেছো: {recitation_text}")

    if not recitation_text:
        st.info("প্রথমে বাংলা উচ্চারণ লেখো বা মাইকে রেকর্ড করো।")
        return

    result = compare_ayah(recitation_text, ayah_data["bangla"])
    if result["is_correct"]:
        st.markdown('<div class="correct-box"><h3>মাশাআল্লাহ! একদম সঠিক।</h3><p>এভাবেই নিয়মিত অনুশীলন করো।</p></div>', unsafe_allow_html=True)
        render_tts_player("মাশাআল্লাহ। একদম সঠিক হয়েছে।", lang="bn", caption="ফিডব্যাক শুনতে পারো")
        return

    st.markdown(f'<div class="wrong-box"><h3>আরেকটু চেষ্টা করো। ({result["mistakes"]}টি শব্দে ভুল)</h3><p>নিচে কোথায় ভুল হয়েছে দেখো।</p></div>', unsafe_allow_html=True)

    comparison_html = "<div style='margin-top:0.8rem; padding:0.8rem; background:#fafafa; border-radius:12px;'>"
    comparison_html += "<p><strong>তোমার উত্তর:</strong> "
    for item in result["details"]:
        if item["match"]:
            comparison_html += f'<span class="word-correct">{item["user"]}</span> '
        elif item["user"]:
            comparison_html += f'<span class="word-wrong">{item["user"]}</span> '
        else:
            comparison_html += '<span class="word-missing">(বাদ পড়েছে)</span> '
    comparison_html += "</p><p><strong>সঠিক উত্তর:</strong> "
    for item in result["details"]:
        if item["match"]:
            comparison_html += f'<span class="word-correct">{item["correct"]}</span> '
        else:
            comparison_html += f'<span class="word-missing">{item["correct"]}</span> '
    comparison_html += "</p></div>"

    st.markdown(comparison_html, unsafe_allow_html=True)
    st.info(f"আবার চেষ্টা করো। সঠিক উচ্চারণ: **{ayah_data['bangla']}**")
    render_tts_player(f"আরেকটু চেষ্টা করো। সঠিক উচ্চারণ হলো: {ayah_data['bangla']}", lang="bn", caption="সঠিক উচ্চারণ শুনতে পারো")


def render_story_tab():
    st.markdown('<div class="section-emoji">গল্প</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">ইসলামিক গল্প</div>', unsafe_allow_html=True)
    st.markdown('<div class="info-box">তালিকা থেকে বা নিজের দেয়া বিষয়ের উপর গল্প তৈরি করো। আউটপুট থাকবে পরিষ্কার plain text।</div>', unsafe_allow_html=True)

    story_option = st.radio("গল্পের ধরন:", ["তালিকা থেকে বাছাই", "নিজে বিষয় লেখো"], horizontal=True, key="story_option")

    if story_option == "তালিকা থেকে বাছাই":
        story_topic = st.selectbox("গল্পের বিষয়:", options=STORY_TOPICS, key="story_select")
    else:
        story_topic = st.text_input("গল্পের বিষয় লেখো:", placeholder="উদাহরণ: একজন সৎ ছেলের গল্প", key="story_custom")

    voice_story_topic = get_audio_input("অথবা মাইকে গল্পের বিষয় বলো:", key="story_voice")
    story_button = st.button("গল্প তৈরি করো", type="primary", use_container_width=True)

    if not story_button:
        return

    topic_to_use = story_topic.strip() if isinstance(story_topic, str) else ""
    if not topic_to_use and voice_story_topic:
        with st.spinner("বিষয়টি লেখা হচ্ছে..."):
            topic_to_use = transcribe_audio(voice_story_topic, "বাচ্চাদের গল্পের বিষয়")
        if topic_to_use:
            st.success(f"তুমি বিষয় বলেছো: {topic_to_use}")

    if not topic_to_use:
        st.info("প্রথমে গল্পের বিষয় লেখো বা মাইকে রেকর্ড করো।")
        return

    with st.spinner("গল্প লেখা হচ্ছে..."):
        prompt = f"ছোট বাচ্চাদের জন্য একটি ইসলামিক গল্প লেখো। বিষয়: {topic_to_use}"
        story = sanitize_story_text(get_ai_response(prompt, STORY_SYSTEM))

    st.markdown(f'<div class="story-box">{html.escape(story)}</div>', unsafe_allow_html=True)
    render_tts_player(story, lang="bn", caption="গল্প শুনতে প্লে করো")


def render_app():
    render_top_overview()

    if not check_groq_ready():
        st.warning(
            "`.env` ফাইলে `GROQ_API_KEY` সেট করা নেই।\n\n"
            "উদাহরণ:\n"
            "`GROQ_API_KEY=your_groq_api_key_here`\n"
            "`GROQ_MODEL=llama-3.1-8b-instant`"
        )

    t1, t2, t3 = st.tabs(["AI শিক্ষক", "কুরআন অনুশীলন", "ইসলামিক গল্প"])
    with t1:
        render_teacher_tab()
    with t2:
        render_quran_tab()
    with t3:
        render_story_tab()


render_app()
