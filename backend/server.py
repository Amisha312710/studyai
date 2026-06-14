from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_cors import CORS
from routes.onboarding import onboarding_bp
from routes.dashboard import dashboard_bp
from routes.study import study_bp
from routes.uploads import uploads_bp
from routes.quiz import quiz_bp
from routes.tutor import tutor_bp
from routes.scheduler import scheduler_bp
import os

app = Flask(__name__)
CORS(app)

app.register_blueprint(onboarding_bp, url_prefix='/api/onboarding')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
app.register_blueprint(study_bp, url_prefix='/api/study')
app.register_blueprint(uploads_bp, url_prefix='/api/uploads')
app.register_blueprint(quiz_bp, url_prefix='/api/quiz')
app.register_blueprint(tutor_bp, url_prefix='/api/tutor')
app.register_blueprint(scheduler_bp, url_prefix='/api/scheduler')

@app.route('/health')
def health():
    return {'status': '✅ StudyAI backend is running!'}

if __name__ == '__main__':
    app.run(port=3001, debug=True)