import os
import time
import tempfile
from flask import Flask, request, send_file, after_this_request
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
from auth_routes import auth

load_dotenv()

app = Flask(__name__)
CORS(app)

app.register_blueprint(auth)

# Create the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/chat", methods=["POST"])
def chat():
    file = request.files["file"]

    # temp file for audio input
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as input_temp_file:
        input_temp_file_path = input_temp_file.name
        file.save(input_temp_file_path)

    # audio input -> STT
    whisper_start = time.time()
    with open(input_temp_file_path, "rb") as audio_file:
        user_text = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text",
        )
    whisper_time = time.time() - whisper_start

    # chat completion
    gpt4_start = time.time()
    response = client.responses.create(
        model="gpt-4o-mini",
        input=f"Translate this input into English. Just output the translation: {user_text}",
        max_output_tokens=100,
    )
    gpt4_time = time.time() - gpt4_start

    response = response.output[0].content[0].text

    # temp file for audio return
    speech_temp_fd, speech_file_path = tempfile.mkstemp(suffix=".mp3")
    os.close(speech_temp_fd)

    # chat completion -> TTS
    tts_start = time.time()
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="shimmer",
        input=response,
        instructions="Speak in a calm, motherly tone",
    ) as tts_response:
        tts_response.stream_to_file(speech_file_path)
    tts_time = time.time() - tts_start

    print(f"Transcription: {user_text}")
    print(f"GPT answer: {response}")
    print(f"Whisper transcription took: {whisper_time:.2f} seconds")
    print(f"GPT-4o response took: {gpt4_time:.2f} seconds")
    print(f"TTS took: {tts_time:.2f} seconds")
    print(f"Total time: {time.time() - whisper_start:.2f} seconds")

    @after_this_request
    def cleanup(response):
        try:
            os.remove(input_temp_file_path)
            os.remove(speech_file_path)
        except Exception as e:
            print("Cleanup error:", e)
        return response

    return send_file(
        speech_file_path,
        mimetype="audio/mpeg",
        as_attachment=True,
        download_name="response.mp3"
    )

if __name__ == "__main__":
    app.run(debug=True, port=8000)
