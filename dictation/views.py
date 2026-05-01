from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from openai import OpenAI
import os


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