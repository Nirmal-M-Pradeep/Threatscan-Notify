from flask import Flask, render_template, request, jsonify
import os
from modules.NOISE import Noise
from modules.ASR import ASR
from modules.NLP import integration,sentiment_analyze,keyword_detection,get_chunk_id,load_data,chunk_text
from modules.EMAIL import checking_to_send_email
import uuid
import whisper
from transformers import pipeline
import torch
import subprocess


app=Flask(__name__)


gpu="cuda" if torch.cuda.is_available() else "cpu"

gpu1=0 if torch.cuda.is_available() else -1

whisper_model=whisper.load_model("small", device=gpu)

sentiment_analyzer = pipeline("text-classification", model="C:\\Windows\\System32\\twitter-roberta-base-offensive",device=gpu1)
nlp_ner = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=gpu1)

sensitive_data="D:\\MINIPROJECTRSET\\threatdataset.csv"


upload_folder='uploads'
app.config['UPLOAD_FOLDER']=upload_folder

progress={"message":""}
processed_chunk=set()

ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv'}
ALLOWED_AUDIO_EXTENSIONS = {'.mp3','.wav'}

def is_video_file(filename):
    return any(filename.lower().endswith(ext) for ext in ALLOWED_VIDEO_EXTENSIONS)

def is_audio_file(filename):
    return any(filename.lower().endswith(ext) for ext in ALLOWED_AUDIO_EXTENSIONS)

def extract_audio_from_video(video_path, output_folder):
    try:
        audio_filename = f"{uuid.uuid4()}.mp3"
        audio_path = os.path.join(output_folder, audio_filename)

        command = [
            "ffmpeg",
            "-i", video_path,        
            "-vn",                   
            "-acodec", "mp3",        
            audio_path               
        ]
        subprocess.run(command, check=True)
        return audio_path
    except Exception as e:
        raise RuntimeError(f"Error extracting audio from video: {str(e)}")



def load_processed_chunks():
    if os.path.exists("D:\\MINIPROJECTRSET\\processedchunks.txt"):
        with open("D:\\MINIPROJECTRSET\\processedchunks.txt", 'r') as f:
            return set(f.read().splitlines())
    return set()

def save_processed_chunks(chunks):
    
    with open("D:\\MINIPROJECTRSET\\processedchunks.txt", 'w') as f:
        f.writelines(f"{chunk}\n" for chunk in chunks)

processed_chunk=load_processed_chunks()

def set_progress(message):
    progress["message"]=message

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_audio():
    try:

        translate = request.form.get('translate', 'false').lower() == 'true'

    
        if 'file' not in request.files:
            return jsonify({"error":"No file part in the request"}),400
        
        file=request.files['file']

        if file.filename == '':
            return jsonify({"error":"No file selected"}),400
        
        file_extension=os.path.splitext(file.filename)[1].lower()

        if not (is_audio_file(file.filename) or is_video_file(file.filename)):
            return jsonify({"error": "Invalid file format. Only MP3 or supported video formats are allowed."}), 400




        if file:

            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)


            unique_filename = f"{uuid.uuid4()}{file_extension}" 
            file_path=os.path.join(app.config['UPLOAD_FOLDER'],unique_filename)
            file.save(file_path)

            if is_video_file(file.filename):
                set_progress("Extracting Audio from Video...")
                print("Extracting Audio from Video...")
                file_path=extract_audio_from_video(file_path,app.config['UPLOAD_FOLDER'])

            try:
                print("Reducing the noise of given audio")
                reduced_path=Noise(file_path)

                print("Setting progress to 'Transcribing audio...'")
                set_progress("Transcribing audio...")  

                print(f"Starting transcription for file: {file_path}")
                transcribe, file_path = ASR(reduced_path, whisper_model, translate)

                
                print(f"Transcription completed. Text: {transcribe}")

                transcription_chunks = chunk_text(transcribe)

                print("starting analysis")
                set_progress("Analyzing text...")
                nlp_result=integration(transcribe,sensitive_data,sentiment_analyzer=sentiment_analyzer,nlp_ner=nlp_ner)

                set_progress("Analyzing sentiment..")
                sentiment_result=nlp_result['sentiment']
                set_progress("Detecting Keywords")
                detected_keywords=nlp_result['sensitive_keywords']
                
                print ("analysis complete")
                

                set_progress("Sending email alert...")
                email_status=checking_to_send_email(transcribe,sentiment_result,detected_keywords,file_path=file_path)
                email_message="Email Alert has not been sent to Concerned Authorities" if email_status else "Email Alert has been sent to Concerned Authorities"

                set_progress("Complete")
                

                return jsonify({
                    "transcriptionChunks": transcription_chunks,
                    "sentiment": nlp_result["sentiment"],
                    "keywords": nlp_result["sensitive_keywords"],
                    "emailStatus":email_message
                    
                }), 200
            
            except Exception as e:
                return jsonify({"error": f"Processing failed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"ERROR":f"An Error has happened:{str(e)}"}),500

    finally:
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
            print("audio file has been removed from directory \n")

@app.route('/analyze', methods=['POST'])
def analyze_chunk():
    try:
        data = request.json
        chunk_text = data.get('chunk')

        if not chunk_text:
            return jsonify({"error": "Invalid input: 'chunk' is required"}), 400

        chunk_id = get_chunk_id(chunk_text)

        if chunk_id in processed_chunk:
            return jsonify({"message": "Chunk already processed"}), 200

        processed_chunk.add(chunk_id)
        save_processed_chunks(processed_chunk)

        sentiment_result = sentiment_analyze(chunk_text, sentiment_analyzer)
        detected_categories, detected_keywords = keyword_detection(
            chunk_text, load_data(sensitive_data), nlp_ner=nlp_ner
        )

        return jsonify({
            "sentiment": sentiment_result,
            "keywords": detected_keywords,
            "categories": detected_categories,
        }), 200

    except Exception as e:
        print(f"Error processing chunk: {str(e)}")
        return jsonify({"error": f"An error occurred while processing the chunk: {str(e)}"}), 500

    
@app.route('/progress', methods=['GET'])
def get_progress():
    print(f"Progress status: {progress['message']}")
    return jsonify(progress)


if __name__ == '__main__':
    app.run(debug=True)
 

