import random
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
import httpx
import tempfile
import subprocess
import os
import logging

app = FastAPI()

WHISPER_API_URL = "https://api.lemonfox.ai/v1/audio/transcriptions"  # Whisper API URL이 정확한지 확인하세요.
WHISPER_API_KEY = "WHISPER_API_KEY"
SAVE_DIRECTORY = "SAVE_DIRECTORY"  # 오디오, 비디오 파일 임시 저장 경로를 지정하세요.

# 대답 더미 데이터
dummy_data = [
    "Hello, how can I help you today?",
    "Goodbye! Have a great day!",
    "Yes, that sounds like a good idea.",
    "No, I don't think that's a good idea.",
    "Maybe, let's think about it.",
    "I'm not sure, let me get back to you on that.",
]

# logging.basicConfig(level=logging.INFO)


def extract_audio_from_video(video_path: str, audio_path: str):
    command = [
        "ffmpeg",
        "-i", video_path,
        "-q:a", "0",
        "-map", "a",
        audio_path
    ]
    subprocess.run(command, check=True)


async def convert_video_to_audio(video_file: UploadFile, save_directory: str):
    os.makedirs(save_directory, exist_ok=True)  # 디렉토리가 없는 경우 생성합니다.

    video_path = os.path.join(save_directory, video_file.filename)
    with open(video_path, "wb") as temp_video:
        temp_video.write(await video_file.read())

    audio_path = os.path.join(save_directory, f"{os.path.splitext(video_file.filename)[0]}.wav")
    extract_audio_from_video(video_path, audio_path)
    os.remove(video_path)  # 비디오 파일 삭제
    return audio_path


async def send_to_whisper(audio_path: str):
    with open(audio_path, "rb") as audio_file:
        audio_bytes = audio_file.read()

    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        response = await client.post(
            WHISPER_API_URL,
            headers={"Authorization": f"Bearer {WHISPER_API_KEY}"},
            files={"file": ("audio.wav", audio_bytes, "audio/wav")}
        )

    # logging.info(f"Whisper API response status: {response.status_code}")
    # logging.info(f"Whisper API response text: {response.text}")

    response.raise_for_status()
    return response.json()


@app.post("/upload-video/")
async def upload_video(file: UploadFile = File(...)):
    audio_path = None
    try:
        audio_path = await convert_video_to_audio(file, SAVE_DIRECTORY)
        transcription = await send_to_whisper(audio_path)
        os.remove(audio_path)  # 오디오 파일 삭제
        return transcription
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)  # 예외 발생 시 오디오 파일 삭제
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/random-answer")
def get_random_answer(question: str = Query(..., description="The question being asked")):
    return {"answer": random.choice(dummy_data)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
