import json, os
from flask import Blueprint, request, jsonify

onboarding_bp = Blueprint('onboarding', __name__)
PROFILE_FILE = 'profile.json'

# In-memory store — holds student profile while server is running
student_profile = {}

@onboarding_bp.route('/profile', methods=['POST'])
def save_profile():
    global student_profile
    data = request.get_json()
    student_profile = {
        'name': data.get('name'),
        'university': data.get('university'),
        'semester': data.get('semester'),
        'knowledgeLevel': data.get('knowledgeLevel', 'beginner'),
        'subjects': data.get('subjects', []),
        'examDates': data.get('examDates', {}),
        'dailyHours': data.get('dailyHours', 2),
        'targetGrade': data.get('targetGrade', 'A'),
        'weakTopics': data.get('weakTopics', []),
        'streak': 0
    }
    # Save to file
    with open(PROFILE_FILE, 'w') as f:
        json.dump(student_profile, f)
    print(f'✅ Profile saved for: {student_profile["name"]}')
    return jsonify({'success': True, 'profile': student_profile}), 201

def get_stored_profile():
    global student_profile
    if student_profile:
        return student_profile
    # Load from file if memory is empty
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, 'r') as f:
            student_profile = json.load(f)
    return student_profile