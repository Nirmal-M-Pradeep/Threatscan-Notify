import os

def ASR(file_path,model,translate=False):
    try:
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Failed to save the file at {file_path}")
        
        try:
            result=model.transcribe(file_path,task="translate" if translate else "transcribe")
            transcribe= result["text"]
            if not transcribe:
                raise ValueError("Empty transcription result.")
            print(f"Transcription result: {transcribe}")
        except Exception as e:
            raise RuntimeError(f"Error in transcribing the file :{str(e)}")
        
        return transcribe, file_path
        
    
    except Exception as e:
       raise FileNotFoundError(f"File saving error: {str(e)}")
    
    except Exception as E:
        raise RuntimeError(f"An error occurred in ASR: {str(e)}")
    
    


