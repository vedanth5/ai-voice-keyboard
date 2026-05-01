from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from openai import OpenAI
import os
import json


# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# 🔹 Basic test endpoint
def test(request):
    return JsonResponse({"message": "working"})

def detect_command(text):
    text = text.lower()

    if "delete last sentence" in text:
        return {"action": "delete_last_sentence"}

    elif "new paragraph" in text:
        return {"action": "new_paragraph"}

    elif "make it formal" in text:
        return {"action": "make_formal"}

    return {"action": "none"}

def detect_command_with_ai(text):
    prompt = f"""
    You are an AI assistant that detects user intent.

    Convert the following sentence into a JSON command.

    Possible actions:
    - delete_last_sentence
    - new_paragraph
    - make_formal
    - none

    Only return JSON like:
    {{"action": "..." }}

    Sentence:
    {text}
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    result = response.choices[0].message.content.strip()

    return result

# 🔹 AI Transcription Cleanup Endpoint
@api_view(['POST'])
def transcribe(request):
    try:
        raw_text = request.data.get("text")

        if not raw_text:
            return Response({"error": "No text provided"}, status=400)

        # Detect command
        command = detect_command(raw_text)

        # If command → return action
        if command["action"] != "none":
            return Response({
                "type": "command",
                "action": command["action"]
            })

        # AI-based command detection
        command_result = detect_command_with_ai(raw_text)

        try:
            command_json = json.loads(command_result)
        except:
            command_json = {"action": "none"}

        if command_json.get("action") != "none":
            return Response({
                "type": "command",
                "action": command_json["action"]
            })  

        # Otherwise → clean text 
        prompt = f"Fix grammar and punctuation:\n{raw_text}"

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        clean_text = response.choices[0].message.content.strip()

        return Response({
            "type": "text",
            "raw_text": raw_text,
            "clean_text": clean_text
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)