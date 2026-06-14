from flask import Blueprint, request, jsonify
from routes.onboarding import get_stored_profile
from routes.uploads import get_context_for_topic
import requests
import os
import json
import re

quiz_bp = Blueprint('quiz', __name__)

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

def call_groq(system_prompt, user_prompt, max_tokens=2000):
    response = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {GROQ_API_KEY}',
            'Content-Type': 'application/json'
        },
        json={
            'model': 'llama-3.3-70b-versatile',
            'max_tokens': max_tokens,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
        }
    )
    data = response.json()
    return data['choices'][0]['message']['content']


@quiz_bp.route('/generate', methods=['POST'])
def generate_quiz():
    data = request.get_json()
    topic = data.get('topic', '')
    difficulty = data.get('difficulty', 'medium')
    num_questions = int(data.get('num_questions', 5))

    if not topic:
        return jsonify({'error': 'Topic is required'}), 400

    # Clamp
    num_questions = max(3, min(10, num_questions))

    profile = get_stored_profile()
    level = profile.get('knowledgeLevel', 'intermediate') if profile else 'intermediate'

    # Pull uploaded notes as context
    context = get_context_for_topic(topic)
    context_block = ''
    if context:
        context_block = f"""
=== STUDENT'S UPLOADED COURSE MATERIAL ===
{context}
===========================================
Use the above course material as your PRIMARY source for generating quiz questions.
"""

    system = (
        "You are an expert quiz generator for ML and NLP university courses. "
        "You ONLY output valid JSON. No preamble, no explanation, no markdown fences."
    )

    difficulty_guidance = {
        'easy': 'straightforward recall and definition questions suitable for beginners',
        'medium': 'conceptual understanding and application questions',
        'hard': 'advanced analysis, edge cases, and tricky distractors that test deep understanding'
    }

    prompt = f"""{context_block}
Generate exactly {num_questions} multiple-choice quiz questions about: {topic}
Student knowledge level: {level}
Difficulty: {difficulty} — {difficulty_guidance.get(difficulty, 'medium difficulty')}

Rules:
- Each question has exactly 4 options labeled A, B, C, D
- Exactly one option is correct
- Distractors should be plausible, not obviously wrong
- Include a brief explanation for the correct answer
- Questions should vary in style (definition, application, comparison, calculation where relevant)

Return ONLY this JSON structure, nothing else:
{{
  "topic": "{topic}",
  "difficulty": "{difficulty}",
  "questions": [
    {{
      "id": 1,
      "question": "Question text here?",
      "options": {{
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text",
        "D": "Option D text"
      }},
      "correct": "A",
      "explanation": "Brief explanation of why A is correct and why the others are wrong."
    }}
  ]
}}"""

    try:
        raw = call_groq(system, prompt, 2500)

        # Strip any accidental markdown fences
        clean = raw.strip()
        clean = re.sub(r'^```json\s*', '', clean)
        clean = re.sub(r'^```\s*', '', clean)
        clean = re.sub(r'\s*```$', '', clean)

        quiz_data = json.loads(clean)

        return jsonify({
            'success': True,
            'quiz': quiz_data,
            'used_uploaded_notes': bool(context)
        })

    except json.JSONDecodeError as e:
        print(f'JSON parse error: {e}\nRaw: {raw[:500]}')
        return jsonify({'error': 'Failed to parse quiz from AI. Please try again.'}), 500
    except Exception as e:
        print(f'Quiz generation error: {e}')
        return jsonify({'error': 'Failed to generate quiz. Check backend and Groq key.'}), 500


@quiz_bp.route('/explain', methods=['POST'])
def explain_answer():
    """Get a deeper explanation for a specific question after the quiz."""
    data = request.get_json()
    topic = data.get('topic', '')
    question = data.get('question', '')
    correct_option = data.get('correct_option', '')
    student_answer = data.get('student_answer', '')

    system = "You are a patient ML/NLP tutor. Give concise, clear explanations."
    prompt = f"""The student got this question wrong during a quiz on {topic}.

Question: {question}
Correct answer: {correct_option}
Student chose: {student_answer}

In 3-4 sentences, explain:
1. Why the correct answer is right
2. Why the student's choice is wrong
3. One tip to remember the correct concept

Be encouraging and educational."""

    try:
        explanation = call_groq(system, prompt, 400)
        return jsonify({'explanation': explanation})
    except Exception as e:
        return jsonify({'error': 'Failed to get explanation'}), 500
