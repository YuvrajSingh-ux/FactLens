import os
from fastapi import FastAPI, UploadFile, Form
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

from claim_detection import process_audio_bytes_for_claims

app = FastAPI(title="Audio Claim Detection API")


@app.post("/process_audio/")
async def process_audio(
    audio_file: UploadFile,
    chunk_start_time: float = Form(...),
    session_id: str = Form(...)
) -> Dict[str, Any]:

    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        return {"error": "GROQ_API_KEY not set on server"}

    audio_bytes = await audio_file.read()

    result = process_audio_bytes_for_claims(
        audio_bytes=audio_bytes,
        chunk_start_time=chunk_start_time,
        groq_api_key=groq_api_key,
        session_id=session_id
    )

    # print("CLAIMS OUTPUT:\n", result)

    return result