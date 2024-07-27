from flask import Flask, render_template, request, jsonify
import os
import time
import google.generativeai as genai
import logging
import markdown

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

genai.configure(api_key=os.environ.get('API_KEY'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = os.path.join('uploads', 'recorded_audio.wav')
    file.save(filename)

    try:
        file_data = upload_and_process_audio(filename)
        custom_input = request.form.get('customInput', 'Please provide the singer\'s name and song title.')
        response = generate_content(file_data, custom_input)
        delete_file(file_data)

        markdown_content = response.text
        html_content = markdown.markdown(markdown_content)
        
        return jsonify({'summary': html_content})
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({'error': 'Failed to generate response. Please try again.'}), 500

def upload_and_process_audio(audio_file_name):
    print(f"Uploading file...")
    audio_file = genai.upload_file(path=audio_file_name)
    print(f"Completed upload: {audio_file.uri}")

    while audio_file.state.name == "PROCESSING":
        print('.', end='', flush=True)
        time.sleep(10)
        audio_file = genai.get_file(audio_file.name)

    if audio_file.state.name == "FAILED":
        raise ValueError(f"File processing failed: {audio_file.state.name}")

    file = genai.get_file(name=audio_file.name)
    print(f"Retrieved file '{file.display_name}' as: {audio_file.uri}")

    return file

def generate_content(file, prompt):
    print("Making LLM inference request...")
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")

    response = model.generate_content([prompt, file], request_options={"timeout": 600})
    print(response.text)
    return response

def delete_file(file):
    print(f'Deleting file {file.uri}')
    genai.delete_file(file.name)
    print(f'Deleted file {file.uri}')

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
