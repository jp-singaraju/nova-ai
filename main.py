# import functions
import os
from gmail import get_latest_message, extract_info, download_attachments
from gcal import create_calendar_event
from text_message import send_text
from authentication import authenticate
from flask import Flask

app = Flask(__name__)

def get_message_and_add_downloads():
    # write the main function
    store_dir = "./attachments/"
    os.makedirs(store_dir, exist_ok=True)

    # authenticate to google api
    service = authenticate("gmail")
    latest_email = get_latest_message(service, "me")
    extracted_info = extract_info(latest_email)

    # if there are attachments, download them
    if latest_email.get("attachments"):
        msg_id = latest_email["id"]
        download_attachments(service, "me", msg_id, store_dir)
    return extracted_info

def add_event_to_calendar(message):
    # add an event to calendar
    service = authenticate("calendar")
    event = create_calendar_event(service, message)
    return event

# run the app route for the webhook
@app.route('/webhook')
def process_incoming_email():
    message = get_message_and_add_downloads()
    add_event_to_calendar(message)
    send_text(message)
    return

if __name__ == "__main__":
    app.run(port=5000)