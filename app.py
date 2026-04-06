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


st.set_page_config(page_title="AI মাদ্রাসা", page_icon="🕌", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Anek+Bangla:wght@400;500;700;800&family=Manrope:wght@500;700&display=swap');

    :root {
        --bg-main: #f5f7fb;
        --bg-panel: #ffffff;
        --bg-sidebar: #111826;
        --txt-main: #1f2937;
        --txt-muted: #64748b;
        --line: #dbe2ea;
        --brand: #0f766e;
    }

    html, body, [data-testid="stAppViewContainer"], .stApp {
        height: 100%;
    }

    .stApp {
        font-family: 'Anek Bangla', sans-serif;
        background: linear-gradient(135deg, #f6f8fb 0%, #eef3fb 100%);
        color: var(--txt-main);
    }

    .block-container {
        max-width: 1280px;
        padding-top: 0.9rem;
        padding-bottom: 1.2rem;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #111826 100%);
        border-right: 1px solid rgba(148, 163, 184, 0.25);
    }

    [data-testid="stSidebar"] * {
        color: #e5edf7;
    }

    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] .stCheckbox label {
        color: #d7e0ec !important;
    }

    [data-testid="stSidebar"] .stRadio > div {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        border: 1px solid rgba(148, 163, 184, 0.25);
        padding: 0.3rem;
    }

    [data-testid="stSidebar"] .stButton > button {
        background: #0f766e !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 10px;
        font-weight: 700;
    }

    .app-shell {
        background: var(--bg-panel);
        border: 1px solid var(--line);
        border-radius: 18px;
        box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
        padding: 1rem 1.15rem;
    }

    .panel-header {
        background: linear-gradient(90deg, #0f766e 0%, #0ea5a5 100%);
        color: white;
        border-radius: 14px;
        padding: 0.9rem 1rem;
        margin-bottom: 0.8rem;
    }

    .panel-header h2 {
        margin: 0;
        font-size: 1.2rem;
        font-family: 'Manrope', sans-serif;
        letter-spacing: 0.2px;
    }

    .panel-header p {
        margin: 0.15rem 0 0;
        font-size: 0.86rem;
        opacity: 0.95;
    }

    .info-box,
    .story-box,
    .correct-box,
    .wrong-box,
    .arabic-text {
        border: 1px solid var(--line);
        background: #ffffff;
        border-radius: 12px;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
    }

    .info-box {
        border-left: 4px solid #0f766e;
        padding: 0.8rem;
        margin: 0.5rem 0 0.8rem;
        color: #334155;
    }

    .arabic-text {
        font-size: 1.45rem;
        text-align: right;
        direction: rtl;
        color: #0f172a;
        padding: 1rem;
        line-height: 2;
        font-family: 'Traditional Arabic', 'Scheherazade New', serif;
    }

    .correct-box {
        border-left: 4px solid #16a34a;
        padding: 0.9rem;
        margin-top: 0.6rem;
        text-align: center;
    }

    .wrong-box {
        border-left: 4px solid #dc2626;
        padding: 0.9rem;
        margin-top: 0.6rem;
    }

    .story-box {
        padding: 1rem;
        margin-top: 0.6rem;
        line-height: 1.72;
        white-space: pre-wrap;
    }

    .word-correct {
        color: #166534;
        font-weight: 700;
        background: #dcfce7;
        padding: 2px 6px;
        border-radius: 6px;
        display: inline-block;
        margin: 2px;
    }

    .word-wrong {
        color: #991b1b;
        font-weight: 700;
        background: #fee2e2;
        padding: 2px 6px;
        border-radius: 6px;
        text-decoration: line-through;
        display: inline-block;
        margin: 2px;
    }

    .word-missing {
        color: #9a3412;
        font-weight: 700;
        background: #ffedd5;
        padding: 2px 6px;
        border-radius: 6px;
        display: inline-block;
        margin: 2px;
        font-style: italic;
    }

    .stTextArea textarea,
    .stTextInput input,
    .stSelectbox > div > div {
        border-radius: 10px !important;
        border: 1px solid var(--line) !important;
    }

    .stButton > button {
        border-radius: 10px;
        font-weight: 700;
    }

    .stChatMessage {
        border-radius: 14px;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.6rem;
            padding-right: 0.6rem;
        }

        .panel-header h2 {
            font-size: 1.02rem;
        }

        .panel-header p {
            font-size: 0.77rem;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)


def init_session_state():
    if "mode" not in st.session_state:
        st.session_state.mode = "AI শিক্ষক"
    if "auto_tts" not in st.session_state:
        st.session_state.auto_tts = True
    if "teacher_messages" not in st.session_state:
        st.session_state.teacher_messages = [
            {
                "role": "assistant",
                "content": "আসসালামু আলাইকুম। আমি উস্তাদ AI। তুমি ইসলামিক যেকোনো সহজ প্রশ্ন করতে পারো।",
            }
        ]
    if "teacher_last_answer" not in st.session_state:
        st.session_state.teacher_last_answer = ""


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown("### AI মাদ্রাসা")
        st.caption("ChatGPT-style সাইড প্যানেল")

        mode = st.radio(
            "মোড বাছাই",
            ["AI শিক্ষক", "কুরআন অনুশীলন", "ইসলামিক গল্প"],
            key="mode",
            label_visibility="visible",
        )

        st.checkbox("অটো ভয়েস (TTS)", key="auto_tts")

        if st.button("নতুন চ্যাট", use_container_width=True):
            st.session_state.teacher_messages = [
                {
                    "role": "assistant",
                    "content": "নতুন চ্যাট শুরু হলো। তোমার প্রশ্ন লিখো বা ভয়েসে বলো।",
                }
            ]
            st.session_state.teacher_last_answer = ""

        st.divider()
        # if check_groq_ready():
        #     st.success("Groq API সংযুক্ত")
        # else:
        #     st.error("Groq API key সেট নেই")
        # st.caption(f"Model: {GROQ_MODEL}")

    return mode


def run_teacher_turn(question: str):
    st.session_state.teacher_messages.append({"role": "user", "content": question})
    with st.spinner("উস্তাদ AI ভাবছে..."):
        prompt = f"একজন ছোট বাচ্চা জিজ্ঞাসা করছে: {question}"
        response = get_ai_response(prompt, TEACHER_SYSTEM)
    st.session_state.teacher_messages.append({"role": "assistant", "content": response})
    st.session_state.teacher_last_answer = response


def render_panel_header(title: str, subtitle: str):
    st.markdown(
        f"""
<div class="panel-header">
    <h2>{html.escape(title)}</h2>
    <p>{html.escape(subtitle)}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def render_teacher_panel():
    render_panel_header("AI শিক্ষক চ্যাট", "ChatGPT-style কথোপকথন: লিখে বা ভয়েসে প্রশ্ন করো")

    voice_question = get_audio_input("মাইকে প্রশ্ন বলো (optional)", key="teacher_voice_chat")
    if voice_question is not None:
        with st.spinner("ভয়েস থেকে লেখা হচ্ছে..."):
            voice_text = transcribe_audio(voice_question, "ছোট বাচ্চার ইসলামিক প্রশ্ন")
        if voice_text:
            st.success(f"তুমি বলেছো: {voice_text}")
            run_teacher_turn(voice_text)
            st.rerun()

    for msg in st.session_state.teacher_messages:
        with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
            st.write(msg["content"])

    user_text = st.chat_input("তোমার প্রশ্ন লিখো...")
    if user_text:
        run_teacher_turn(user_text.strip())
        st.rerun()

    if st.session_state.auto_tts and st.session_state.teacher_last_answer:
        render_tts_player(st.session_state.teacher_last_answer, lang="bn", caption="শেষ উত্তরটি শুনতে পারো")


def render_quran_panel():
    render_panel_header("কুরআন অনুশীলন", "আয়াত বাছাই করে বাংলা উচ্চারণ মিলিয়ে দেখো")
    left_col, right_col = st.columns(2)
    result_state = {"status": "idle"}

    with left_col:
        st.markdown('<div class="info-box">লিখে বা মাইকে বলে তিলাওয়াত যাচাই করো।</div>', unsafe_allow_html=True)

        selected_ayah = st.selectbox("আয়াত বাছাই করো:", options=list(QURAN_AYAHS.keys()), key="quran_select")
        ayah_data = QURAN_AYAHS[selected_ayah]

        st.markdown(f'<div class="arabic-text">{ayah_data["arabic"]}</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**বাংলা উচ্চারণ:** {ayah_data['bangla']}")
        with c2:
            st.markdown(f"**অর্থ:** {ayah_data['meaning']}")

        if st.session_state.auto_tts:
            render_tts_player(
                f"{selected_ayah}. বাংলা উচ্চারণ: {ayah_data['bangla']}. অর্থ: {ayah_data['meaning']}",
                lang="bn",
                caption="উচ্চারণ ও অর্থ শুনতে পারো",
            )

        user_recitation = st.text_input("তুমি বাংলা উচ্চারণ লেখো:", placeholder=f"উদাহরণ: {ayah_data['bangla']}", key="quran_input")
        voice_recitation = get_audio_input("অথবা মাইকে উচ্চারণ বলো:", key="quran_voice")
        check_button = st.button("যাচাই করো", type="primary", key="quran_check")

        if check_button:
            recitation_text = user_recitation.strip()
            if not recitation_text and voice_recitation:
                with st.spinner("তোমার তিলাওয়াত লেখা হচ্ছে..."):
                    recitation_text = transcribe_audio(voice_recitation, "কুরআনের বাংলা উচ্চারণ")
                if recitation_text:
                    st.success(f"তুমি বলেছো: {recitation_text}")

            if not recitation_text:
                result_state = {"status": "empty"}
            else:
                result = compare_ayah(recitation_text, ayah_data["bangla"])
                if result["is_correct"]:
                    result_state = {"status": "correct", "ayah_bangla": ayah_data["bangla"]}
                else:
                    user_side = ""
                    correct_side = ""
                    for item in result["details"]:
                        if item["match"]:
                            user_side += f'<span class="word-correct">{item["user"]}</span> '
                            correct_side += f'<span class="word-correct">{item["correct"]}</span> '
                        else:
                            if item["user"]:
                                user_side += f'<span class="word-wrong">{item["user"]}</span> '
                            else:
                                user_side += '<span class="word-missing">(বাদ পড়েছে)</span> '
                            correct_side += f'<span class="word-missing">{item["correct"]}</span> '
                    result_state = {
                        "status": "wrong",
                        "mistakes": result["mistakes"],
                        "user_side": user_side,
                        "correct_side": correct_side,
                        "ayah_bangla": ayah_data["bangla"],
                    }

    with right_col:
        st.markdown('<div class="info-box"><strong>ফলাফল প্যানেল</strong><br><br>যাচাই করার পর ফলাফল এখানে দেখাবে।</div>', unsafe_allow_html=True)

        if result_state["status"] == "empty":
            st.info("প্রথমে বাংলা উচ্চারণ লেখো বা মাইকে রেকর্ড করো।")
        elif result_state["status"] == "correct":
            st.markdown('<div class="correct-box"><h3>মাশাআল্লাহ! একদম সঠিক।</h3><p>এভাবেই নিয়মিত অনুশীলন করো।</p></div>', unsafe_allow_html=True)
            if st.session_state.auto_tts:
                render_tts_player("মাশাআল্লাহ। একদম সঠিক হয়েছে।", lang="bn", caption="ফিডব্যাক শুনতে পারো")
        elif result_state["status"] == "wrong":
            st.markdown(
                f'<div class="wrong-box"><h3>আরেকটু চেষ্টা করো। ({result_state["mistakes"]}টি শব্দে ভুল)</h3><p>নিচে কোথায় ভুল হয়েছে দেখো।</p></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <div class="info-box" style="margin-top:0.8rem;">
                    <strong>তোমার উত্তর</strong><br><br>{result_state["user_side"]}
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <div class="info-box" style="margin-top:0.8rem;">
                    <strong>সঠিক উত্তর</strong><br><br>{result_state["correct_side"]}
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.session_state.auto_tts:
                render_tts_player(
                    f"আরেকটু চেষ্টা করো। সঠিক উচ্চারণ হলো: {result_state['ayah_bangla']}",
                    lang="bn",
                    caption="সঠিক উচ্চারণ শুনতে পারো",
                )


def render_story_panel():
    render_panel_header("ইসলামিক গল্প", "বিষয় দাও, markdown ছাড়া পরিষ্কার গল্প নাও")
    left_col, right_col = st.columns(2)
    story_state = {"status": "idle", "content": ""}

    with left_col:
        st.markdown('<div class="info-box">তালিকা থেকে বা নিজের বিষয় দিয়ে গল্প তৈরি করো।</div>', unsafe_allow_html=True)

        story_option = st.radio("গল্পের ধরন:", ["তালিকা থেকে বাছাই", "নিজে বিষয় লেখো"], horizontal=True, key="story_option")
        if story_option == "তালিকা থেকে বাছাই":
            story_topic = st.selectbox("গল্পের বিষয়:", options=STORY_TOPICS, key="story_select")
        else:
            story_topic = st.text_input("গল্পের বিষয় লেখো:", placeholder="উদাহরণ: একজন সৎ ছেলের গল্প", key="story_custom")

        voice_story_topic = get_audio_input("অথবা মাইকে গল্পের বিষয় বলো:", key="story_voice")
        story_button = st.button("গল্প তৈরি করো", type="primary", use_container_width=True)

        if story_button:
            topic_to_use = story_topic.strip() if isinstance(story_topic, str) else ""
            if not topic_to_use and voice_story_topic:
                with st.spinner("বিষয়টি লেখা হচ্ছে..."):
                    topic_to_use = transcribe_audio(voice_story_topic, "বাচ্চাদের গল্পের বিষয়")
                if topic_to_use:
                    st.success(f"তুমি বিষয় বলেছো: {topic_to_use}")

            if not topic_to_use:
                story_state = {"status": "empty", "content": ""}
            else:
                with st.spinner("গল্প লেখা হচ্ছে..."):
                    prompt = f"ছোট বাচ্চাদের জন্য একটি ইসলামিক গল্প লেখো। বিষয়: {topic_to_use}"
                    story = sanitize_story_text(get_ai_response(prompt, STORY_SYSTEM))
                story_state = {"status": "ready", "content": story}

    with right_col:
        st.markdown('<div class="info-box"><strong>গল্প আউটপুট প্যানেল</strong><br><br>গল্প তৈরি করার পর এখানে দেখাবে।</div>', unsafe_allow_html=True)

        if story_state["status"] == "empty":
            st.info("প্রথমে গল্পের বিষয় লেখো বা মাইকে রেকর্ড করো।")
        elif story_state["status"] == "ready":
            st.markdown(f'<div class="story-box">{html.escape(story_state["content"])}</div>', unsafe_allow_html=True)
            if st.session_state.auto_tts:
                render_tts_player(story_state["content"], lang="bn", caption="গল্প শুনতে প্লে করো")


def render_app():
    init_session_state()
    mode = render_sidebar()

    if not check_groq_ready():
        st.warning(
            "`.env` ফাইলে `GROQ_API_KEY` সেট করা নেই।\n\n"
            "উদাহরণ:\n"
            "`GROQ_API_KEY=your_groq_api_key_here`\n"
            "`GROQ_MODEL=llama-3.1-8b-instant`"
        )

    st.markdown('<div class="app-shell">', unsafe_allow_html=True)
    if mode == "AI শিক্ষক":
        render_teacher_panel()
    elif mode == "কুরআন অনুশীলন":
        render_quran_panel()
    else:
        render_story_panel()
    st.markdown('</div>', unsafe_allow_html=True)


render_app()
