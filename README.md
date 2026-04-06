# AI Madrasa

AI Madrasa is a small Streamlit app built for young learners (roughly ages 5-10) who are learning Islam in Bangla. The goal is simple: kids should be able to speak naturally, listen to responses, and learn without dealing with heavy typing.

This version uses **Groq API** for AI text generation.

## What this app does

The app has three learning modes:

1. AI Teacher
2. Quran Practice
3. Islamic Story Teller

### 1) AI Teacher
- Students can ask questions in Bangla by typing or speaking.
- The app sends the question to Groq with child-friendly Islamic guidance.
- Answer comes back in simple Bangla.
- The answer is also playable as audio.

### 2) Quran Practice
- A short ayah is selected from a preset list.
- The learner can type or speak the Bangla pronunciation.
- The app compares input word by word and highlights mistakes.

### 3) Islamic Story Teller
- Choose a topic from a list, or provide a custom one.
- Custom topics can be spoken through microphone input.
- The app generates a short Islamic story in easy Bangla.
- Story can be played back as audio.

## Voice quality

- Voice recording is cleaned with noise reduction before transcription.
- Transcription uses Python `SpeechRecognition` (Google Web Speech backend, no API key required).
- Speech output uses Python `gTTS`.
- Voice features are now applied across all learning tabs (Teacher, Quran Practice, Story Teller).

## Screenshots

### Home / Main Interface
![Main interface](ss/Screenshot%20from%202026-04-05%2020-30-12.png)

### Quran Practice
![Quran practice](ss/Screenshot%20from%202026-04-05%2020-30-24.png)

### Story / Teacher View
![Story and teacher view](ss/Screenshot%20from%202026-04-05%2020-30-34.png)

## Tech stack

- Python
- Streamlit
- Groq API (LLM)
- STT: `SpeechRecognition`
- TTS: `gTTS`
- noisereduce + librosa + soundfile (audio denoising)

## Project structure

- app.py: Main Streamlit application
- requirements.txt: Python dependencies

## Setup

### 1. Clone and enter project

```bash
git clone <your-repo-url>
cd AI-for-Madrasa-Students
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Groq API key

Create `.env` in project root and add:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
GROQ_MAX_TOKENS=1024
GROQ_CONTINUATION_ROUNDS=2
```

`GROQ_MODEL` is optional; the app uses `llama-3.1-8b-instant` by default.
`GROQ_MAX_TOKENS` and `GROQ_CONTINUATION_ROUNDS` are optional and help get more complete responses when output is long.

### 5. Run the app

```bash
streamlit run app.py
```

## Notes about voice features

- Voice input uses Streamlit audio input, then noise reduction and Python `SpeechRecognition` transcription.
- Voice output uses `gTTS` (MP3).
- If audio input is unavailable, the app gracefully falls back and still works with typed input.

## Safety note

This app is designed with child-safe prompts and model safety settings. Even then, AI responses can still be imperfect. For important religious guidance, please verify with qualified scholars.

## Contribution

If you want to improve content quality, add more ayahs, or tune the UI for younger children, contributions are welcome.
