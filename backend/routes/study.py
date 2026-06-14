from flask import Blueprint, request, jsonify
from routes.onboarding import get_stored_profile
from routes.uploads import get_context_for_topic
import requests
import os

study_bp = Blueprint('study', __name__)

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

ML_TOPICS = [
    'Linear Regression', 'Logistic Regression', 'Decision Trees',
    'Random Forests', 'SVM', 'Neural Networks', 'Backpropagation',
    'CNNs', 'RNNs', 'LSTMs', 'Clustering', 'K-Means',
    'Dimensionality Reduction', 'PCA', 'Gradient Descent',
    'Overfitting & Regularization', 'Bias-Variance Tradeoff',
    'Ensemble Methods', 'Boosting', 'Bagging'
]

NLP_TOPICS = [
    'Tokenization', 'Word Embeddings', 'Word2Vec', 'GloVe', 'TF-IDF',
    'Transformers', 'Attention Mechanism', 'Self-Attention', 'BERT',
    'GPT', 'Named Entity Recognition', 'Sentiment Analysis',
    'Seq2Seq', 'Encoder-Decoder', 'Positional Encoding',
    'Text Classification', 'Language Models', 'Fine-tuning'
]

def call_groq(system_prompt, user_prompt, max_tokens=1500):
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

def build_context_block(topic):
    context = get_context_for_topic(topic)
    if context:
        return f"""
=== STUDENT'S UPLOADED COURSE MATERIAL ===
{context}
===========================================
Use the above course material as your PRIMARY source.
Combine it with your general knowledge to give a complete answer.
"""
    return ""

@study_bp.route('/topics', methods=['GET'])
def get_topics():
    profile = get_stored_profile()
    subjects = profile.get('subjects', ['ML', 'NLP']) if profile else ['ML', 'NLP']
    topics = {}
    if 'ML' in subjects:
        topics['ML'] = ML_TOPICS
    if 'NLP' in subjects:
        topics['NLP'] = NLP_TOPICS
    return jsonify({'topics': topics})

@study_bp.route('/generate', methods=['POST'])
def generate_content():
    data = request.get_json()
    topic = data.get('topic', '')
    mode = data.get('mode', 'notes')
    profile = get_stored_profile()
    level = profile.get('knowledgeLevel', 'intermediate') if profile else 'intermediate'

    if not topic:
        return jsonify({'error': 'Topic is required'}), 400

    context_block = build_context_block(topic)
    has_notes = bool(context_block.strip())

    try:
        if mode == 'notes':
            result = generate_notes(topic, level, context_block)
        elif mode == 'flashcards':
            result = generate_flashcards(topic, level, context_block)
        elif mode == 'summary':
            result = generate_summary(topic, level, context_block)
        elif mode == 'explanation':
            result = generate_explanation(topic, level, context_block)
        else:
            return jsonify({'error': 'Invalid mode'}), 400

        return jsonify({
            'content': result,
            'topic': topic,
            'mode': mode,
            'used_uploaded_notes': has_notes
        })

    except Exception as e:
        print(f'Groq error: {e}')
        return jsonify({'error': 'Failed to generate content'}), 500

def generate_notes(topic, level, context_block=''):
    system = "You are an expert ML/NLP professor. Write clear, structured study notes."
    prompt = f"""{context_block}
Write detailed study notes on: {topic}
Student level: {level}

## Overview
2-3 sentences explaining what this is.

## Key Concepts
- Concept 1: explanation
- Concept 2: explanation
- Concept 3: explanation
- Concept 4: explanation
- Concept 5: explanation

## How It Works
Step by step explanation, 3-5 steps.

## Important Formulas / Rules
List any key formulas or rules (if applicable).

## Real World Example
One concrete, relatable example.

## Common Mistakes
2-3 things students often get wrong.

## Quick Recap
3 bullet points summarizing the most important things."""
    return call_groq(system, prompt, 1500)

def generate_flashcards(topic, level, context_block=''):
    system = "You are a study coach. Generate flashcards as strict JSON only. No extra text."
    prompt = f"""{context_block}
Generate 8 flashcards for: {topic}
Student level: {level}

Return ONLY this JSON, nothing else:
{{
  "flashcards": [
    {{"id": 1, "front": "Question here?", "back": "Answer here."}},
    {{"id": 2, "front": "Question here?", "back": "Answer here."}},
    {{"id": 3, "front": "Question here?", "back": "Answer here."}},
    {{"id": 4, "front": "Question here?", "back": "Answer here."}},
    {{"id": 5, "front": "Question here?", "back": "Answer here."}},
    {{"id": 6, "front": "Question here?", "back": "Answer here."}},
    {{"id": 7, "front": "Question here?", "back": "Answer here."}},
    {{"id": 8, "front": "Question here?", "back": "Answer here."}}
  ]
}}"""
    return call_groq(system, prompt, 1000)

def generate_summary(topic, level, context_block=''):
    system = "You are a concise study coach. Write punchy, memorable summaries."
    prompt = f"""{context_block}
Write a quick summary of: {topic}
Student level: {level}

## ⚡ Quick Summary: {topic}

**In one sentence:** [one sentence explanation]

**The 3 things you MUST know:**
1. [most important point]
2. [second most important point]
3. [third most important point]

**Remember this:** [one memorable analogy or trick]

**Exam tip:** [one thing that often comes up in exams]"""
    return call_groq(system, prompt, 600)

def generate_explanation(topic, level, context_block=''):
    system = "You are a patient teacher who explains things simply using analogies and examples."
    prompt = f"""{context_block}
Give an in-depth explanation of: {topic}
Student level: {level}

## 🔍 Deep Dive: {topic}

**The Simple Version**
Explain it like the student is hearing it for the first time. Use an analogy.

**Why It Matters**
Why do we need this? What problem does it solve?

**The Full Picture**
Detailed technical explanation now that context is set.

**Worked Example**
Walk through a concrete example step by step.

**Connections**
How does this connect to other ML/NLP concepts?

**Test Yourself**
3 questions the student should be able to answer after reading this."""
    return call_groq(system, prompt, 1500)