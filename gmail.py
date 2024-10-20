# import functions
import openai
import json
from dotenv import load_dotenv
import os
import base64
import email

# load env vars
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_latest_message(service, user_id):
    # get the latest message
    messages = service.users().messages().list(userId=user_id, maxResults=1, q="is:inbox").execute()
    if 'messages' in messages:
        latest_msg_id = messages['messages'][0]['id']
        return get_message_info(service, user_id, latest_msg_id)
    else:
        print("No messages found.")
        return None

def get_message_info(service, user_id, msg_id):
    # extract email details
    message = service.users().messages().get(userId=user_id, id=msg_id, format='raw').execute()
    msg_str = base64.urlsafe_b64decode(message['raw'].encode("utf-8")).decode("utf-8")
    fin_msg = email.message_from_string(msg_str)
    email_data = {
        "id": msg_id,
        "sender": fin_msg["from"],
        "recipients": fin_msg["to"],
        "subject": fin_msg["subject"],
        "date": fin_msg["date"],
        "plain_text": extract_plain_text(fin_msg),
        "attachments": extract_attachments(fin_msg)
    }
    return email_data

def extract_plain_text(fin_msg):
    # get the plain text from message
    if fin_msg.is_multipart():
        for part in fin_msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode("utf-8")
    else:
        return fin_msg.get_payload(decode=True).decode("utf-8")
    return ""

def extract_attachments(fin_msg):
    # find the attachments in this message
    attachments = []
    if fin_msg.is_multipart():
        for part in fin_msg.walk():
            if part.get_content_type() not in ["text/plain", "text/html"] and part.get_filename():
                attachment = {
                    "filename": part.get_filename(),
                    "fileType": part.get_content_type(),
                }
                attachments.append(attachment)
    return attachments

def download_attachments(service, user_id, msg_id, store_dir):
    # save the attachments locally
    message = service.users().messages().get(userId=user_id, id=msg_id).execute()
    for part in message['payload']['parts']:
        if part['filename'] and part['body'] and part['body']['attachmentId']:
            attachment = service.users().messages().attachments().get(id=part['body']['attachmentId'], userId=user_id, messageId=msg_id).execute()
            file_data = base64.urlsafe_b64decode(attachment['data'].encode('utf-8'))
            path = os.path.join(store_dir, part['filename'])
            with open(path, 'wb') as f:
                f.write(file_data)
    print("DOWNLOADS RETRIEVED.")

def extract_info(data):
    # extract info using gpt model
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts important information from email dictionary data. You should extract the important information from the given email (represented as a dictionary) and return only the relevant fields such as id, sender, recipients, subject, date, plain_text, and attachments as a JSON string. Only return the JSON string."},
            {"role": "user", "content": f"Here is the given email in dictionary format: {data}"}
        ],
    )
    extracted_info = response.choices[0].message.content
    print("MESSAGE RETRIEVED.")
    return json.loads(extracted_info)