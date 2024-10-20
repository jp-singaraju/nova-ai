# import functions
import json
from datetime import datetime, timedelta
import openai
import os
from dotenv import load_dotenv

# load env vars
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def determine_message_type(message):
    # figure out if this is an event or reminder or other
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "Determine if the given message is an event or a reminder. Output a JSON object with a single key 'type' and value either 'event', 'reminder', or 'other'."},
            {"role": "user", "content": f"Determine message type: {message}"}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)["type"]

def process_event(message):
    # process the information if it is an event
    event_categories = {"summary", "location", "description", "start", "end", "attendees"}
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": f"You are a helpful assistant tasked with extracting information from a message and organizing it into the given categories: {event_categories}. Your goal is to create a structured calendar event based on the message content. For each category, extract relevant details from the message, and if no information is provided for a specific category, set its value to null. When information is incomplete or implicit, infer values logically based on the context, such as estimating location, description, or participants. For the attendees category, include the recipient and sender email in the format 'attendees': [{{'email': 'recipient@example.com', 'email': 'sender@example.com'}}]. If no time zone is specified, use the default 'timeZone': 'America/Los_Angeles', and format the start and end times like 'start': {{'dateTime': '2015-05-28T09:00:00-07:00', 'timeZone': 'America/Los_Angeles'}}, 'end': {{'dateTime': '2015-05-28T17:00:00-07:00', 'timeZone': 'America/Los_Angeles'}}. Only create an event if a start time is explicitly stated or strongly implied in the message. If a start time is present, estimate an appropriate end time by inferring the event’s duration based on the type of event or message content. The final output should be a JSON object, where each category is a key and the corresponding value is either the extracted or inferred information. Focus on extracting key details, especially the event’s start time, end time, title, location, attendees, and time zone, while ensuring the event is scheduled only when relevant information is provided."},
            {"role": "user", "content": f"Here is the given message: {message}"}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def process_reminder(message):
    # process the information if it is an reminder
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "Extract reminder information from the given message. Output a JSON object with keys: summary, start. For start, use format: {'dateTime': 'YYYY-MM-DDTHH:MM:SS-07:00', 'timeZone': 'America/Los_Angeles'}. If no specific time is mentioned, schedule for the next appropriate time."},
            {"role": "user", "content": f"Extract reminder information: {message}"}
        ],
        response_format={"type": "json_object"}
    )
    reminder_data = json.loads(response.choices[0].message.content)
    start_time = datetime.fromisoformat(reminder_data["start"]["dateTime"].replace("-07:00", ""))
    end_time = start_time + timedelta(minutes=30)
    reminder_data["end"] = {
        "dateTime": end_time.isoformat() + "-07:00",
        "timeZone": "America/Los_Angeles"
    }
    return reminder_data

def create_calendar_event(service, message):
    # create the calendar event based on the given information
    try:
        message_type = determine_message_type(message)
        if message_type == "event":
            data = process_event(message)
        elif message_type == "reminder":
            data = process_reminder(message)
        else:
            print("NO CALENDAR UPDATE NEEDED.")
            return
        calendar_item = service.events().insert(calendarId="primary", body=data, sendUpdates="all").execute()
        print("CALENDAR UPDATED.")
        return json.dumps({"status": "Calendar event created", "event": calendar_item})
    except Exception as e:
        print("ERROR CREATING CALENDAR EVENT: " + str(e))
        return