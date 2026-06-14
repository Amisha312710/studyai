from flask import Blueprint, request, jsonify
import os
import json

uploads_bp = Blueprint('uploads', __name__)

# Folder jahan files save hongi
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')
METADATA_FILE = os.path.join(UPLOAD_FOLDER, 'metadata.json')

# Folder bana do agar exist nahi karta
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_metadata(meta):
    with open(METADATA_FILE, 'w') as f:
        json.dump(meta, f, indent=2)

def extract_text_from_pdf(filepath):
    """Extract all text from a PDF file"""
    try:
        import PyPDF2
        text = ''
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
        return text.strip()
    except Exception as e:
        print(f'PDF extraction error: {e}')
        return ''

def extract_text_from_txt(filepath):
    """Extract text from plain text file"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read().strip()
    except Exception as e:
        print(f'TXT extraction error: {e}')
        return ''


@uploads_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    topic = request.form.get('topic', 'General')
    subject = request.form.get('subject', 'ML')

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Only allow PDF and TXT
    allowed = ['.pdf', '.txt']
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        return jsonify({'error': 'Only PDF and TXT files allowed'}), 400

    # Save file
    safe_name = file.filename.replace(' ', '_')
    filepath = os.path.join(UPLOAD_FOLDER, safe_name)
    file.save(filepath)

    # Extract text
    if ext == '.pdf':
        text = extract_text_from_pdf(filepath)
    else:
        text = extract_text_from_txt(filepath)

    if not text:
        return jsonify({'error': 'Could not extract text from file. Make sure PDF has real text (not scanned images).'}), 400

    # Trim to 8000 chars to avoid token limits
    # 8000 chars ≈ ~2000 tokens, leaves room for prompt + response
    trimmed_text = text[:8000]
    was_trimmed = len(text) > 8000

    # Save metadata
    meta = load_metadata()
    file_id = safe_name
    meta[file_id] = {
        'filename': file.filename,
        'topic': topic,
        'subject': subject,
        'filepath': filepath,
        'text_preview': trimmed_text[:200],
        'full_text': trimmed_text,
        'char_count': len(text),
        'was_trimmed': was_trimmed
    }
    save_metadata(meta)

    print(f'✅ Uploaded: {file.filename} | Topic: {topic} | Chars: {len(text)}')

    return jsonify({
        'success': True,
        'file_id': file_id,
        'filename': file.filename,
        'topic': topic,
        'char_count': len(text),
        'was_trimmed': was_trimmed,
        'preview': trimmed_text[:200]
    })


@uploads_bp.route('/list', methods=['GET'])
def list_uploads():
    meta = load_metadata()
    # Return without full_text to keep response small
    result = []
    for file_id, info in meta.items():
        result.append({
            'file_id': file_id,
            'filename': info['filename'],
            'topic': info['topic'],
            'subject': info['subject'],
            'char_count': info['char_count'],
            'was_trimmed': info['was_trimmed'],
            'preview': info['text_preview']
        })
    return jsonify({'uploads': result})


@uploads_bp.route('/delete/<file_id>', methods=['DELETE'])
def delete_upload(file_id):
    meta = load_metadata()
    if file_id not in meta:
        return jsonify({'error': 'File not found'}), 404

    # Delete actual file
    filepath = meta[file_id]['filepath']
    if os.path.exists(filepath):
        os.remove(filepath)

    # Remove from metadata
    del meta[file_id]
    save_metadata(meta)

    return jsonify({'success': True})


def get_context_for_topic(topic):
    """
    Called by study.py — finds uploaded notes relevant to a topic
    Returns the text content if found, empty string if not
    """
    meta = load_metadata()
    relevant_texts = []

    topic_lower = topic.lower()
    for file_id, info in meta.items():
        file_topic = info.get('topic', '').lower()
        filename = info.get('filename', '').lower()

        # Match if topic name is in file's topic tag OR filename
        if (topic_lower in file_topic or
            file_topic in topic_lower or
            topic_lower in filename or
            file_topic == 'general'):
            relevant_texts.append(info['full_text'])

    if relevant_texts:
        # Combine all relevant texts, max 6000 chars total
        combined = '\n\n---\n\n'.join(relevant_texts)
        return combined[:6000]
    return ''