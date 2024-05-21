import random
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
import httpx
import tempfile
import subprocess

app = FastAPI()

WHISPER_API_URL = "https://api.whisper.com/v1/transcribe"
WHISPER_API_KEY = "hsinQ7tFbJSbzKxbASQT5qGR1HB8k4f4"

# 대답 더미 데이터
dummy_data = [
    "Hello, how can I help you today?",
    "Goodbye! Have a great day!",
    "Yes, that sounds like a good idea.",
    "No, I don't think that's a good idea.",
    "Maybe, let's think about it.",
    "I'm not sure, let me get back to you on that.",
]


def extract_audio_from_video(video_path: str, audio_path: str):
    command = [
        "ffmpeg",
        "-i", video_path,
        "-q:a", "0",
        "-map", "a",
        audio_path
    ]
    subprocess.run(command, check=True)


async def convert_video_to_audio(video_file: UploadFile):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        temp_video.write(await video_file.read())
        video_path = temp_video.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        audio_path = temp_audio.name

    extract_audio_from_video(video_path, audio_path)
    return audio_path


async def send_to_whisper(audio_path: str):
    with open(audio_path, "rb") as audio_file:
        audio_bytes = audio_file.read()

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            WHISPER_API_URL,
            headers={"Authorization": f"Bearer {WHISPER_API_KEY}"},
            files={"file": ("audio.wav", audio_bytes, "audio/wav")}
        )

    response.raise_for_status()
    return response.json()


@app.post("/upload-video/")
async def upload_video(file: UploadFile = File(...)):
    try:
        audio_path = await convert_video_to_audio(file)
        transcription = await send_to_whisper(audio_path)
        return transcription
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/random-answer")
def get_random_answer(question: str = Query(..., description="The question being asked")):
    return {"answer": random.choice(dummy_data)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
