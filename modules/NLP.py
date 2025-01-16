import os
import spacy
import hashlib
import pandas as pd

def load_data(sensitive_data_file_path):
    try:
        df=pd.read_csv(sensitive_data_file_path)
        if 'category' not in df.columns or 'word' not in df.columns:
            raise ValueError("CSV file must have 'category' and 'word' columns.")
        

        sensitive_words = (
            df.groupby('category')['word']
            .apply(list)
            .to_dict()
        )
        return sensitive_words
    except Exception as e:
        raise ValueError(f"Error reading CSV file with pandas: {str(e)}")
        


def get_chunk_id(chunk):
    return hashlib.md5(chunk.encode('utf-8')).hexdigest()

def chunk_text(ASR_text,max_length=400,overlap_size=50):

    nlp = spacy.load("en_core_web_sm")
    doc = nlp(ASR_text)

    chunks = []
    current_chunk = ""
    for sentence in doc.sents:
        sentence_text = sentence.text.strip()

        
        if len(current_chunk) + len(sentence_text) > max_length:
            chunks.append(current_chunk.strip())
            print(f"Created chunk: {current_chunk.strip()}")

            
            overlap_start = max(0, len(current_chunk) - overlap_size)
            current_chunk = current_chunk[overlap_start:] + sentence_text
        else:
            
            current_chunk += " " + sentence_text

    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
        print(f"Created final chunk: {current_chunk.strip()}")

    
    return chunks

#def batch_process_keywords(sensitive_data,batch_size=30):


    #if not isinstance(sensitive_data, dict):
        #raise ValueError("sensitive_data must be a dictionary")
    
    
    #all_categories=list(sensitive_data.keys())
    #batched_data=[]

    #for i in range(0,len(all_categories),batch_size):
        #batch=all_categories[i:i + batch_size]
        #batched_data.append(batch)

    #return batched_data


def sentiment_analyze(ASR_text,sentiment_analyzer):
    try:
        result=sentiment_analyzer(ASR_text)

        if not isinstance(result, list):
            raise ValueError("Unexpected sentiment analyzer output format")
        
        label=result[0]['label'].lower()
        score=result[0]['score']

        return {"label": label, "score": score}

        
    
    except Exception as e:
        return {"Sentiment Analysis Failed": str(e)}

def keyword_detection(ASR_text,sensitive_data,batch_size=30, nlp_ner=None,threshold=0.7):
    
    detected_categories={}
    
    detected_words={}

    chunks=chunk_text(ASR_text)


    
    #sensitive_batch=batch_process_keywords(sensitive_data,batch_size)

    
    for chunk in chunks:
        
        try:
            candidate_label = list(sensitive_data.keys()) + ["non-sensitive"]
            print(f"Processing chunk: {chunk} with labels: {candidate_label}")

            print(f"Processing chunk: {chunk} with labels : {candidate_label}")

                
            

            results=nlp_ner(chunk,candidate_labels=candidate_label)

            print("Results from nlp_ner:", results)

            if 'labels' not in results or 'scores' not in results:
                raise ValueError("Invalid output format from nlp_ner pipeline.")

            for label, score in zip(results['labels'], results['scores']):
                if score > threshold :
                    if label != "non-sensitive":
                        detected_categories[label] = max(
                        detected_categories.get(label, 0), round(score, 2))

        
    
            chunk_lower=chunk.lower()
            for category, keywords in sensitive_data.items():
                found_keywords = [keyword for keyword in keywords if keyword in chunk_lower]
                if found_keywords:
                    detected_words[category] = detected_words.get(category, []) + found_keywords
            
        except Exception as e:
            print(f"Error in keyword detection for chunk {chunk}: {str(e)}")
            

    return detected_categories,detected_words

def integration(ASR_text,sensitive_data,nlp_ner=None,sentiment_analyzer=None):

    if sensitive_data is None:
        raise ValueError("Database file path must be provided")
    if not os.path.exists(sensitive_data):
        raise FileNotFoundError(f"The Database required is not found : {sensitive_data}")
    sensitive_words_file=load_data(sensitive_data)

    if nlp_ner is None:
        raise ValueError("nlp_ner pipeline must be provided for keyword detection.")
    
    

    print("Starting Analysis...")

    

    detected_categories,detected_keywords=keyword_detection(ASR_text,sensitive_words_file,batch_size=30,nlp_ner=nlp_ner)
    sentiment_result=sentiment_analyze(ASR_text,sentiment_analyzer)

    return{
        "sentiment": sentiment_result,
        "sensitive_categories": detected_categories,
        "sensitive_keywords": detected_keywords
    }



            

