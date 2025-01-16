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
        
        if not file.filename.lower().endswith(('.mp3')):
            return jsonify({"error": "Invalid file format. Only mp3 format is supported"}), 400

        if file:

            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)


            unique_filename = f"{uuid.uuid4()}.mp3" 
            file_path=os.path.join(app.config['UPLOAD_FOLDER'],unique_filename)
            file.save(file_path)

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

                
                sentiment_result=nlp_result['sentiment']
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
 

