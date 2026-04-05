# AI Madrasa

AI Madrasa is a small Streamlit app built for young learners (roughly ages 5-10) who are learning Islam in Bangla. The goal is simple: kids should be able to speak naturally, listen to responses, and learn without dealing with heavy typing.

## What this app does

The app has three learning modes:

1. AI Teacher
2. Quran Practice
3. Islamic Story Teller

### 1) AI Teacher
- Students can ask questions in Bangla by typing or speaking.
- The app sends the question to Gemini with child-friendly Islamic guidance.
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
- Google Gemini API (google-generativeai)
- gTTS (for Bangla speech playback)
- python-dotenv

## Project structure

- app.py: Main Streamlit application
- requirements.txt: Python dependencies
- .env: Local API key (not committed)

## Setup

### 1. Clone and enter project

```bash
git clone <your-repo-url>
cd AI\ Madrasa
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

### 4. Add Gemini API key

Create or edit .env file:

```env
GEMINI_API_KEY=your_real_key_here
```

You can get a key from Google AI Studio.

### 5. Run the app

```bash
streamlit run app.py
```

## Notes about voice features

- Voice input uses Streamlit audio input and Gemini for transcription.
- Voice output uses gTTS to generate MP3 playback.
- If audio input is unavailable, the app gracefully falls back and still works with typed input.

## Safety note

This app is designed with child-safe prompts and model safety settings. Even then, AI responses can still be imperfect. For important religious guidance, please verify with qualified scholars.

## Contribution

If you want to improve content quality, add more ayahs, or tune the UI for younger children, contributions are welcome.
