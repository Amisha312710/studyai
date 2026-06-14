from flask import Blueprint, request, jsonify
from routes.onboarding import get_stored_profile
from routes.uploads import get_context_for_topic
import requests
import os
import base64
import tempfile
from elevenlabs.client import ElevenLabs
from elevenlabs import save

tutor_bp = Blueprint('tutor', __name__)

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY', '')

# ElevenLabs client
client = ElevenLabs(
    api_key=ELEVENLABS_API_KEY
)

conversation_history = []

# ElevenLabs Voice IDs
VOICE_EN = "pNInz6obpgDQGcFmaJgB"  # Adam
VOICE_HI = "EXAVITQu4vr4xnSDxMaL"  # Sarah (good multilingual)

HINDI_TRIGGERS = [
    'hindi', 'हिंदी', 'हिन्दी', 'hindi mein', 'hindi me',
    'hindi main', 'samjhao', 'समझाओ', 'बताओ', 'hindi explain',
    'explain in hindi', 'in hindi', 'hindi mai', 'hindi main batao',
    'hinglish', 'roman hindi'
]


def detect_hindi_request(message):
    msg_lower = message.lower()
    return any(trigger in msg_lower for trigger in HINDI_TRIGGERS)


def get_system_prompt(profile, hindi=False):
    name = profile.get('name', 'Student') if profile else 'Student'
    level = profile.get('knowledgeLevel', 'intermediate') if profile else 'intermediate'
    subjects = ', '.join(profile.get('subjects', ['ML', 'NLP'])) if profile else 'ML, NLP'
    weak = ', '.join(profile.get('weakTopics', [])) if profile else 'none'

    if hindi:
        return f"""Tu {name} ka personal AI tutor hai jo {subjects} padhata hai.
Student ka level hai: {level}.
Unke weak topics hain: {weak}.

Tera style:
- Bilkul natural Hinglish mein baat kar
- Roman script use kar
- Technical terms English mein hi rakh
- Pehle intuition de, phir concept, phir example
- Bohot engaging aur conversational rehna
- Chhoti chhoti sentences use kar
- Analogies use kar

Jawab plain text mein de.
Koi markdown nahi.
Koi bullet points nahi.
Koi numbering nahi."""

    else:
        return f"""You are {name}'s personal AI tutor specializing in {subjects}.
Student level: {level}.
Weak topics: {weak}.

Teaching style:
- Explain like Richard Feynman
- Start with intuition first
- Use conversational language
- Use vivid analogies
- Keep sentences short for natural TTS
- Use real-world examples
- Be warm and engaging

CRITICAL:
Plain text only.
No markdown.
Use bullet points to explain long answers.
No numbering."""


@tutor_bp.route('/chat', methods=['POST'])
def chat():
    global conversation_history

    data = request.get_json()

    message = data.get('message', '').strip()
    topic_context = data.get('topic', '')

    if not message:
        return jsonify({'error': 'Message is required'}), 400

    profile = get_stored_profile()

    is_hindi = detect_hindi_request(message)

    # Get uploaded notes context
    context_block = ''

    if topic_context:
        context = get_context_for_topic(topic_context)

        if context:
            context_block = f"""

Relevant course material uploaded by the student:

{context[:3000]}

Use this material for more relevant answers.
"""

    messages = [
        {
            'role': 'system',
            'content': get_system_prompt(profile, is_hindi) + context_block
        }
    ]

    # Last 14 messages for memory
    messages += conversation_history[-14:]

    messages.append({
        'role': 'user',
        'content': message
    })

    try:

        # GROQ LLaMA
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'llama-3.3-70b-versatile',
                'max_tokens': 1200,
                'temperature': 0.7,
                'messages': messages
            }
        )

        response_json = response.json()

        reply = response_json['choices'][0]['message']['content']

        # Clean for TTS
        clean_reply = clean_for_tts(reply)

        # Save history
        conversation_history.append({
            'role': 'user',
            'content': message
        })

        conversation_history.append({
            'role': 'assistant',
            'content': reply
        })

        if len(conversation_history) > 28:
            conversation_history = conversation_history[-28:]

        # Select voice
        voice = VOICE_HI if is_hindi else VOICE_EN

        # ElevenLabs TTS
        audio_base64 = text_to_speech_elevenlabs(
            clean_reply,
            voice
        )

        return jsonify({
            'reply': reply,
            'audio': audio_base64,
            'language': 'hindi' if is_hindi else 'english',
            'history_length': len(conversation_history)
        })

    except Exception as e:
        print(f'Tutor error: {e}')

        return jsonify({
            'error': 'Failed to get response'
        }), 500


@tutor_bp.route('/transcribe', methods=['POST'])
def transcribe():

    if 'audio' not in request.files:
        return jsonify({
            'error': 'No audio file'
        }), 400

    audio_file = request.files['audio']

    try:

        response = requests.post(
            'https://api.groq.com/openai/v1/audio/transcriptions',
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}'
            },
            files={
                'file': (
                    audio_file.filename,
                    audio_file.read(),
                    audio_file.content_type
                )
            },
            data={
                'model': 'whisper-large-v3-turbo'
            }
        )

        result = response.json()

        text = result.get('text', '').strip()

        return jsonify({
            'text': text
        })

    except Exception as e:
        print(f'Transcription error: {e}')

        return jsonify({
            'error': 'Transcription failed'
        }), 500


@tutor_bp.route('/clear', methods=['POST'])
def clear_history():
    global conversation_history

    conversation_history = []

    return jsonify({
        'success': True
    })


def clean_for_tts(text):
    """Clean markdown for natural TTS"""

    import re

    text = text.replace('*', '')
    text = text.replace('#', '')
    text = text.replace('`', '')
    text = text.replace('**', '')
    text = text.replace('__', '')
    text = text.replace('~~', '')

    # Remove numbered lists
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)

    # Remove bullets
    text = re.sub(r'^[-•]\s+', '', text, flags=re.MULTILINE)

    # Replace newlines
    text = re.sub(r'\n{2,}', '. ', text)
    text = re.sub(r'\n', ' ', text)

    # Remove extra spaces
    text = re.sub(r' {2,}', ' ', text)

    return text.strip()


def text_to_speech_elevenlabs(text, voice_id):
    """Generate TTS using ElevenLabs"""

    try:

        if len(text) > 2500:
            text = text[:2500]

        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            output_format="mp3_44100_128",
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings={
                "stability": 0.45,
                "similarity_boost": 0.85,
                "style": 0.35,
                "use_speaker_boost": True
            }
        )

        with tempfile.NamedTemporaryFile(
            suffix=".mp3",
            delete=False
        ) as tmp:

            temp_path = tmp.name

        save(audio, temp_path)

        with open(temp_path, "rb") as f:
            audio_bytes = f.read()

        os.unlink(temp_path)

        return base64.b64encode(audio_bytes).decode("utf-8")

    except Exception as e:
        print(f'ElevenLabs TTS error: {e}')
        return None