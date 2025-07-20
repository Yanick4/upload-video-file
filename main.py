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


CHUNK_DIR = "uploaded_chunks"
FINAL_PATH ="final"

@app.post("/upload-chunk/")
async def upload_chunk(
    file: UploadFile = File(...),
    filename: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...)
):
    try:
        os.makedirs(CHUNK_DIR, exist_ok=True)
        os.makedirs(FINAL_PATH, exist_ok=True)
        chunk_path = os.path.join(CHUNK_DIR, f"{filename}_part_{chunk_index}")

        async with aiofiles.open(chunk_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        # Si tous les chunks sont uploadés, on assemble
        if len([f for f in os.listdir(CHUNK_DIR) if f.startswith(filename)]) == total_chunks:
            output_path = os.path.join(FINAL_PATH, filename)
            with open(output_path, 'wb') as output_file:
                for i in range(total_chunks):
                    part_path = os.path.join(CHUNK_DIR, f"{filename}_part_{i}")
                    with open(part_path, 'rb') as part_file:
                        output_file.write(part_file.read())
            time.sleep(1)
            for i in range(3):
                try:
                    shutil.rmtree(CHUNK_DIR)
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