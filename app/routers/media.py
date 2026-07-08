import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.auth.dependencies import get_current_user
from app.auth.models import User

router = APIRouter(prefix="/api/media", tags=["media"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp",  # images
    ".mp4", ".mov", ".avi", ".mkv", ".webm",   # videos
    ".mp3", ".wav", ".aac",                      # audio
}

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


@router.post("/upload")
async def upload_media(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Create user-specific directory
    user_dir = UPLOAD_DIR / str(current_user.id)
    user_dir.mkdir(exist_ok=True)

    # Generate unique filename
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = user_dir / unique_name

    # Read and save file with size check
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 100MB.")

    with open(file_path, "wb") as f:
        f.write(content)

    # Return the URL path that can be used to access the file
    media_url = f"/api/media/files/{current_user.id}/{unique_name}"

    return {
        "url": media_url,
        "filename": file.filename,
        "size": len(content),
        "content_type": file.content_type,
    }


@router.post("/upload-multiple")
async def upload_multiple(
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
):
    results = []
    for file in files:
        ext = Path(file.filename or "").suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            results.append({"filename": file.filename, "error": f"File type '{ext}' not allowed"})
            continue

        user_dir = UPLOAD_DIR / str(current_user.id)
        user_dir.mkdir(exist_ok=True)

        unique_name = f"{uuid.uuid4().hex}{ext}"
        file_path = user_dir / unique_name

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            results.append({"filename": file.filename, "error": "File too large"})
            continue

        with open(file_path, "wb") as f:
            f.write(content)

        media_url = f"/api/media/files/{current_user.id}/{unique_name}"
        results.append({
            "url": media_url,
            "filename": file.filename,
            "size": len(content),
            "content_type": file.content_type,
        })

    return {"files": results}
