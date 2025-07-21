import re
from fastapi import UploadFile, Form, FastAPI, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import aiofiles
import os
import shutil
import time

app= FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST","GET"],
    allow_headers=["*"],
)

template=Jinja2Templates(directory="templates")


CHUNK_DIR = "/uploaded_chunks"
FINAL_PATH ="/final"

quality_order=["FHD","HD","MD","SD"]

def clean_video_name_regex(video_name, quality_order):
    """
    Version avec regex pour une meilleure gestion des patterns
    """
    video_name=video_name.replace(".mp4","")
    for qual in quality_order:
        if video_name.lower().endswith(f"_{qual.lower()}"):
            video_name = video_name[:-(len(qual) + 1)]
            break
        elif video_name.lower().endswith(qual.lower()):
            video_name = video_name[:-len(qual)]
            break
    return video_name

os.makedirs(CHUNK_DIR, exist_ok=True)
os.makedirs(FINAL_PATH, exist_ok=True)
@app.post("/upload-chunk/")
async def upload_chunk(
    file: UploadFile = File(...),
    filename: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...)
):
    try:
        file_directories=clean_video_name_regex(filename,quality_order).upper()
        temp_file_path=os.path.join(CHUNK_DIR,file_directories)
        final_path=os.path.join(FINAL_PATH,file_directories)
        os.makedirs(temp_file_path,exist_ok=True)
        os.makedirs(final_path,exist_ok=True)
        chunk_path = os.path.join(temp_file_path, f"{filename}_part_{chunk_index}")

        async with aiofiles.open(chunk_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        # Si tous les chunks sont uploadés, on assemble
        if len([f for f in os.listdir(temp_file_path) if f.startswith(filename)]) == total_chunks:
            output_path = os.path.join(final_path, filename)
            with open(output_path, 'wb') as output_file:
                for i in range(total_chunks):
                    part_path = os.path.join(temp_file_path, f"{filename}_part_{i}")
                    with open(part_path, 'rb') as part_file:
                        output_file.write(part_file.read())
            time.sleep(1)
            for i in range(3):
                try:
                    shutil.rmtree(temp_file_path)
                    break
                except PermissionError as e:
                    print(f"Tentative {i+1}: Fichiers encore en cours d’utilisation. Nouvelle tentative...")
                    time.sleep(1)

            return JSONResponse(
                content={
                    "message": "Fichier reconstruit avec succès", 
                    "filename": filename,
                    "status":"COMPLETE"
                },
                status_code=200
            )

        return JSONResponse(
            content={"message": f"Chunk {chunk_index + 1}/{total_chunks} reçu"},
            status_code=200
        )
    except Exception as e:
        return JSONResponse(
            content={"message":e},
            status_code=500
        )


@app.get("/", response_class=HTMLResponse)
async def index(request:Request):
    return template.TemplateResponse("index.html",{"request":request})