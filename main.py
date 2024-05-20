from fastapi import FastAPI, File, UploadFile, HTTPException
import httpx
from httpx import TimeoutException
app = FastAPI()

WHISPER_API_URL = "https://api.whisper.com/v1/transcribe"
WHISPER_API_KEY = "hsinQ7tFbJSbzKxbASQT5qGR1HB8k4f4"

# 업로드 한 영상파일을 음성으로 변환하는 method


async def send_to_whisper(audioFile: UploadFile):
    video_bytes = await audioFile.read()

    for attempt in range(3):  # 최대 3번 재시도
        try:
            async with httpx.AsyncClient(timeout=60) as client:  # 타임아웃 시간을 60초로 설정
                response = await client.post(
                    WHISPER_API_URL,
                    headers={
                        "Authorization": f"Bearer {WHISPER_API_KEY}"
                    },
                    files={
                        "file": (audioFile.filename, video_bytes, audioFile.content_type)
                    }
                )
                response.raise_for_status()  # 응답이 성공인지 확인
                return response.json()
        except (TimeoutException, httpx.HTTPStatusError) as e:
            if attempt == 2:  # 마지막 시도에서도 실패한 경우
                raise HTTPException(status_code=500, detail=f"Failed to transcribe video after 3 attempts: {str(e)}")
            continue  # 재시도


@app.post("/upload-video/")
async def upload_video(videoFile: UploadFile = File(...)):
    # 영상을 음성으로 변환하는 method 호출 !개발필요!  videoFile --> audioFile


    audioFile = 1
    # 그 음성을 변수 audioFile로 선언하여 send_to_whisper method 호출
    return await send_to_whisper(audioFile)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
