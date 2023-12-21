from flask import Flask, request, render_template, jsonify, send_from_directory, url_for
import base64
import time
import errno
from openai import OpenAI
from elevenlabs import generate, set_api_key, voices
import os

port = int(os.environ.get("PORT", 5000))




app = Flask(__name__)
client = OpenAI()

UPLOAD_FOLDER = 'uploaded_images'
AUDIO_FOLDER = 'narration'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['AUDIO_FOLDER'] = AUDIO_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2 Megabytes

set_api_key(os.environ.get("ELEVENLABS_API_KEY"))

@app.route('/', methods=['GET'])
def index():
    return render_template('upload.html')

@app.route('/', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if file and file.filename:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        return jsonify({'filename': filename})

@app.route('/narrate', methods=['POST'])
def narrate_image():
    file = request.files.get('file')
    if file and file.filename:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        base64_image = encode_image(filename)
        analysis = analyze_image(base64_image, [])
        audio_filename = play_audio(analysis)
        audio_url = url_for('serve_audio', filename=audio_filename) if audio_filename else None
        return jsonify({'analysis': analysis, 'audio_file': audio_url})


def encode_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except IOError as e:
        print(f"Error encoding image: {e}")
        return None

def play_audio(text):
    try:
        audio = generate(text, voice=os.environ.get("ELEVENLABS_VOICE_ID"))
        unique_id = base64.urlsafe_b64encode(os.urandom(50)).decode("utf-8").rstrip("=")
        dir_path = os.path.join(AUDIO_FOLDER, unique_id)
        os.makedirs(dir_path, exist_ok=True)
        audio_filename = os.path.join(dir_path, "audio.wav")
        with open(audio_filename, "wb") as f:
            f.write(audio)
        return os.path.join(unique_id, "audio.wav")
    except Exception as e:
        print(f"Error generating audio: {e}")
        return None

def generate_new_line(base64_image):
    return [{"role": "user", "content": [{"type": "text", "text": "Describe this image"}, {"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64_image}"}]}]

def analyze_image(base64_image, script):
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[{"role": "system", "content": "You are Sir David Attenborough. Narrate the picture of the human as if it is a nature documentary. Make it snarky and funny. Don't repeat yourself. Make it short, no more than one sentence. use punctuations as if spoken, not written, meaning more pauses. If I do anything remotely interesting, make a big deal about it!"}] + script + generate_new_line(base64_image),
        max_tokens=30,
    )
    return response.choices[0].message.content

@app.route('/narration/<path:filename>')
def serve_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)

if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(AUDIO_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))