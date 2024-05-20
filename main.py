from fastapi import FastAPI, File, UploadFile, HTTPException
import httpx
from httpx import TimeoutException
app = FastAPI()

WHISPER_API_URL = "https://api.whisper.com/v1/transcribe"
WHISPER_API_KEY = "hsinQ7tFbJSbzKxbASQT5qGR1HB8k4f4"

async def send_to_whisper(file: UploadFile):
    video_bytes = await file.read()

    for attempt in range(3):  # 최대 3번 재시도
        try:
            async with httpx.AsyncClient(timeout=60) as client:  # 타임아웃 시간을 60초로 설정
                response = await client.post(
                    WHISPER_API_URL,
                    headers={
                        "Authorization": f"Bearer {WHISPER_API_KEY}"
                    },
                    files={
                        "file": (file.filename, video_bytes, file.content_type)
                    }
                )
                response.raise_for_status()  # 응답이 성공인지 확인
                return response.json()
        except (TimeoutException, httpx.HTTPStatusError) as e:
            if attempt == 2:  # 마지막 시도에서도 실패한 경우
                raise HTTPException(status_code=500, detail=f"Failed to transcribe video after 3 attempts: {str(e)}")
            continue  # 재시도

@app.post("/upload-video/")
async def upload_video(file: UploadFile = File(...)):
    return await send_to_whisper(file)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
