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


# 🔹 AI Transcription Cleanup Endpoint
@api_view(['POST'])
def transcribe(request):
    try:
        raw_text = request.data.get("text")

        # ✅ Validate input
        if not raw_text:
            return Response(
                {"error": "No text provided"},
                status=400
            )

        # ✅ Prompt for AI cleanup
        prompt = f"""
        Fix grammar and punctuation of this text without changing its meaning:

        {raw_text}
        """

        # ✅ OpenAI call
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        clean_text = response.choices[0].message.content.strip()

        # ✅ Final response
        return Response({
            "raw_text": raw_text,
            "clean_text": clean_text
        })

    except Exception as e:
        return Response({
            "error": str(e)
        }, status=500)