from flask import Blueprint, jsonify
from routes.onboarding import get_stored_profile
import requests
import os
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

@dashboard_bp.route('/', methods=['GET'])
def get_dashboard():
    profile = get_stored_profile()

    if not profile:
        return jsonify({'error': 'No profile found. Complete onboarding first.'}), 404

    # Calculate days until each exam
    exam_countdowns = {}
    for subject, date_str in profile.get('examDates', {}).items():
        if date_str:
            exam_date = datetime.strptime(date_str, '%Y-%m-%d')
            diff = (exam_date - datetime.now()).days
            exam_countdowns[subject] = max(diff, 0)

    # Mock progress — Phase 6 replaces with real scores
    mock_progress = {'ML': 35, 'NLP': 22}
    progress = {s: mock_progress.get(s, 0) for s in profile.get('subjects', [])}

    # Get today's completed hours from scheduler
    today_completed = 0
    try:
        from routes.scheduler import saved_schedule
        from datetime import datetime
        days_list = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
        today_name = days_list[datetime.now().weekday() + 1 if datetime.now().weekday() < 6 else 0]
        # Fix: Python weekday() 0=Monday, so adjust
        today_name = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][datetime.now().weekday()]
        if saved_schedule and 'days' in saved_schedule:
            today_day = next((d for d in saved_schedule['days'] if d['day'] == today_name), None)
            if today_day:
                done_sessions = [s for s in today_day.get('sessions', []) if s.get('done')]
                today_completed = round(sum(s.get('duration', 0) for s in done_sessions) / 60, 1)
    except:
        today_completed = 0

    # Real progress based on done sessions
    progress = {}
    try:
        from routes.scheduler import saved_schedule as sched
        if sched and 'days' in sched:
            all_sessions = [s for d in sched['days'] for s in d.get('sessions', [])]
            for subj in profile.get('subjects', []):
                subj_sessions = [s for s in all_sessions if s.get('subject') == subj]
                done = [s for s in subj_sessions if s.get('done')]
                if subj_sessions:
                    progress[subj] = round((len(done) / len(subj_sessions)) * 100)
                else:
                    progress[subj] = 0
        else:
            progress = {s: 0 for s in profile.get('subjects', [])}
    except:
        progress = {s: 0 for s in profile.get('subjects', [])}

    return jsonify({
        'profile': profile,
        'examCountdowns': exam_countdowns,
        'progress': progress,
        'streak': profile.get('streak', 0),
        'dailyTarget': profile.get('dailyHours', 2),
        'todayCompleted': today_completed
    })

@dashboard_bp.route('/strategy', methods=['POST'])
def get_ai_strategy():
    profile = get_stored_profile()

    if not profile:
        return jsonify({'error': 'No profile found.'}), 404

    prompt = f"""Generate today's study strategy for this student:
- Name: {profile['name']}
- Subjects: {', '.join(profile['subjects'])}
- Knowledge level: {profile['knowledgeLevel']}
- Available hours today: {profile['dailyHours']}
- Weak topics: {', '.join(profile.get('weakTopics', [])) or 'none listed'}
- Target grade: {profile['targetGrade']}

Give exactly 3 bullet points. Each bullet is one clear action for today. Under 80 words total."""

    try:
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'llama-3.3-70b-versatile',
                'max_tokens': 200,
                'messages': [
                    {'role': 'system', 'content': 'You are a focused study coach. Be concise and motivating.'},
                    {'role': 'user', 'content': prompt}
                ]
            }
        )
        data = response.json()
        strategy = data['choices'][0]['message']['content']
        return jsonify({'strategy': strategy})

    except Exception as e:
        print(f'Groq error: {e}')
        return jsonify({'error': 'Failed to generate strategy'}), 500