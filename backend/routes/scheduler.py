from flask import Blueprint, request, jsonify
import requests
import os
import json

scheduler_bp = Blueprint('scheduler', __name__)
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

saved_schedule = {}
_stored_profile = None

def get_profile():
    try:
        from routes.onboarding import get_stored_profile
        p = get_stored_profile()
        if p:
            return p
    except Exception as e:
        print(f'Profile load error: {e}')
    return None

@scheduler_bp.route('/generate', methods=['POST'])
def generate_schedule():
    profile = get_profile()
    if not profile:
        return jsonify({'error': 'No profile found'}), 404

    data = request.get_json()
    focus_areas = data.get('focusAreas', [])

    name = profile.get('name', 'Student')
    subjects = profile.get('subjects', [])
    weak_topics = profile.get('weakTopics', [])
    daily_hours = profile.get('dailyHours', 2)
    exam_dates = profile.get('examDates', {})
    target_grade = profile.get('targetGrade', 'A')
    level = profile.get('knowledgeLevel', 'intermediate')

    exam_info = ', '.join([f"{s} exam on {d}" for s, d in exam_dates.items() if d]) or 'no exam dates set'
    weak_info = ', '.join(weak_topics) or 'none specified'
    focus_info = ', '.join(focus_areas) or 'balanced across all topics'

    prompt = f"""Create a 7-day study schedule for {name}.

Student profile:
- Subjects: {', '.join(subjects)}
- Knowledge level: {level}
- Daily study hours available: {daily_hours} hours
- Weak topics that need extra attention: {weak_info}
- Exam dates: {exam_info}
- Target grade: {target_grade}
- Focus areas requested: {focus_info}

Rules:
- Distribute topics across 7 days (Monday to Sunday)
- Give more time to weak topics
- Include revision days closer to exam dates
- Keep Sunday lighter (1-2 sessions max)
- Each session should be 30-90 minutes
- Mix different topics across the week for better retention
- Include at least one revision/practice session per subject per week

Return ONLY valid JSON, no markdown, no explanation:
{{
  "week_goal": "one sentence describing the week's main goal",
  "days": [
    {{
      "day": "Monday",
      "date_label": "Day 1",
      "sessions": [
        {{
          "id": "mon-1",
          "topic": "Topic Name",
          "subject": "ML",
          "duration": 60,
          "type": "study",
          "notes": "Focus on one specific aspect"
        }}
      ]
    }}
  ]
}}

Types can be: study, revision, practice, break
Subjects must be exactly: {', '.join(subjects)}
Generate exactly 7 days."""

    try:
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {GROQ_API_KEY}', 'Content-Type': 'application/json'},
            json={
                'model': 'llama-3.3-70b-versatile',
                'max_tokens': 2000,
                'messages': [
                    {'role': 'system', 'content': 'You are a study schedule expert. Return only valid JSON.'},
                    {'role': 'user', 'content': prompt}
                ]
            }
        )
        raw = response.json()['choices'][0]['message']['content']
        clean = raw.strip().replace('```json', '').replace('```', '').strip()
        schedule = json.loads(clean)

        global saved_schedule
        saved_schedule = schedule
        return jsonify({'success': True, 'schedule': schedule})

    except json.JSONDecodeError as e:
        print(f'JSON parse error: {e}')
        return jsonify({'error': 'Failed to parse schedule. Try again.'}), 500
    except Exception as e:
        print(f'Scheduler error: {e}')
        return jsonify({'error': 'Failed to generate schedule'}), 500


@scheduler_bp.route('/save', methods=['POST'])
def save_schedule():
    global saved_schedule
    data = request.get_json()
    saved_schedule = data.get('schedule', {})
    return jsonify({'success': True})


@scheduler_bp.route('/get', methods=['GET'])
def get_schedule():
    return jsonify({'schedule': saved_schedule})