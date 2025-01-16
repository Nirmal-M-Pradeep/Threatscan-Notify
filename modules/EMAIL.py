import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

def send_email(subject,body,to_email,file_path=None):
    try:
        sender_email="senderproject123@gmail.com"
        sender_pass="tbzx wgez puzd gntb"
        smtp_server="smtp.gmail.com"
        smtp_port=587

        msg=MIMEMultipart()
        msg['From']=sender_email
        msg['To']=to_email
        msg['Subject']=subject
        msg.attach(MIMEText(body,'plain'))

        if file_path and os.path.exists(file_path):
            with open(file_path,'rb') as attachment:
                part=MIMEBase('application','octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content=Disposition',f'attachment;filename="{os.path.basename(file_path)}"')
                msg.attach(part)

        with smtplib.SMTP(smtp_server,smtp_port) as server:
            server.starttls()
            server.login(sender_email,sender_pass)
            server.sendmail(sender_email,to_email,msg.as_string())

        print("Email Sent SuccessFully!!!")

    except Exception as e:
        print(f"Error sending the email:{str(e)}")

def checking_to_send_email(ASR_text,sentiment_result,detected_keywords,threshold=0.5,receiving_email="receiveproject123@gmail.com",file_path=None):
    try:
        sentiment_score=sentiment_result.get("score",0)
        if sentiment_score>=threshold and detected_keywords:
            subject="Sensitive Content Detected"
            body=(
                "Attention: Sensitive words have been detected in the uploaded audio file.\n\n"
                f"ASR Text: {ASR_text}\n\n"
                f"Sentiment: {sentiment_result['label']} (Score: {sentiment_score})\n\n"
                f"Detected Keywords: \n"
                
            )

            if isinstance(detected_keywords, str):
                body += f"- Raw Keywords: {detected_keywords}\n"
            elif isinstance(detected_keywords, list):
                for keyword_obj in detected_keywords:
                    if isinstance(keyword_obj, dict):
                        keyword = keyword_obj.get("keyword", "N/A")
                        category = keyword_obj.get("category", "N/A")
                        severity = keyword_obj.get("severity", "N/A")
                        body += f"- Keyword: {keyword}, Category: {category}, Severity: {severity}\n"
                    else:
                        body += f"- Keyword: {str(keyword_obj)}\n"
            else:
                body += f"- Keywords: {str(detected_keywords)}\n"

            body += "\nThe attached audio file contains the sensitive content."
            send_email(subject,body,receiving_email,file_path)
        else:
            print("No email was SENT,Either the sentiment score was below threshold or no keywords were detected")
    except Exception as e:
        print(f"error in checking_to_send_email:{str(e)}")



