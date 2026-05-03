from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from openai import OpenAI
import os
import json
import re
from rapidfuzz import fuzz


# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# 🔹 Basic test endpoint
def test(request):
    return JsonResponse({"message": "working"})

INTENTS = {
    "delete_last_sentence": [
        "delete last sentence",
        "remove last sentence",
        "delete previous sentence",
        "remove previous line",
        "undo last sentence"
    ],
    "new_line": [
        "go to next line",
        "new line",
        "start new line"
    ],
    "new_paragraph": [
        "new paragraph"
    ],
    "make_formal": [
        "make it formal"
    ]
}

def detect_command(text):
    text = normalize(text)

    best_match = None
    highest_score = 0

    for action, phrases in INTENTS.items():
        for phrase in phrases:
            score = fuzz.partial_ratio(text, phrase)

            if score > highest_score:
                highest_score = score
                best_match = action

    if highest_score > 75:  # threshold
        return {"action": best_match}

    return {"action": "none"}

def normalize(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text



def detect_command_with_ai(text):
    prompt = f"""
Return ONLY valid JSON. No explanation.

Format:
{{"action": "one_of_the_actions"}}

Actions:
delete_last_sentence, new_line, new_paragraph, make_formal, none

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