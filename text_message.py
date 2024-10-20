# import functions
import os
from dotenv import load_dotenv
import openai
from sinch import SinchClient
import json

# load env vars
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def parse_message(message):
    # parse input message to get information
    example_conversation = {"phone_number": "+19725039779", "message": "Hey John, Nova here. Jeff just told me about you. Are you interested in driving the minivan around the city to ship our new merch?"}
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
                {"role": "system", "content": f"You are an assistant that analyzes conversations between two people about a third person. Your task is to extract a valid phone number in the format +XXXXXXXXXXX (e.g., +12145067234) from the conversation, analyze the discussion to understand key points about the third person, and synthesize this information into a concise message directed to the third person (the phone number owner). If both a valid phone number and relevant information are present, return a JSON object with phone_number and message keys. The message should be written as if coming from the recipient of the original conversation, addressing the third person directly about the discussed topic. Include the recipient's name if mentioned. Return null if either the phone number or relevant information is missing. Ignore conversation parts unrelated to the third person or the extracted number. For example: {example_conversation}."},
                {"role": "user", "content": f"Extract the phone number and message content from this text: {message}"}
            ],
        response_format={"type": "json_object"}
        )
    return response.choices[0].message.content

def send_text(message):
    # init the sinch client
    sinch_client = SinchClient(
        key_id="c282428c-f911-4d89-abce-5fe7c638e7ba",
        key_secret="33.sSkemtozGFojdCfbykvfYZJ",
        project_id="5244202a-7235-4684-9fb1-1b96dc48a89b"
    )

    # parse the message
    parsed_data = parse_message(message)
    if parsed_data.lower() == "null":
        print("NO TEXT MESSAGE SENT.")
        return

    # convert the string response to a dictionary
    data = json.loads(parsed_data)

    # send the SMS
    send_batch_response = sinch_client.sms.batches.send(
        body=data["message"],
        to=[data["phone_number"]],
        from_="+12064743901",
        delivery_report="none"
    )
    print("TEXT MESSAGE SENT.")
    return send_batch_response