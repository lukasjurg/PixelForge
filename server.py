import os
import uuid
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from rembg import remove, new_session
from pydantic import BaseModel
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="PixelForge Background Removal API",
    description="Production-ready API for automatic background removal",
    version="1.0.0"
)

# Middleware
app.add_middleware(GZipMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Global variables
MODEL_NAME = "u2net"  # Try "u2net_human_seg" for human images
TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

# Load model once at startup
try:
    session = new_session(MODEL_NAME)
    logger.info(f"Loaded model {MODEL_NAME} successfully")
except Exception as e:
    logger.error(f"Failed to load model: {str(e)}")
    raise


# Models
class ErrorResponse(BaseModel):
    error: str
    details: str = None
    timestamp: str = datetime.now().isoformat()


# Exception handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            details=str(exc)
        ).dict()
    )


# Health check endpoint
@app.get("/health", tags=["Monitoring"])
async def health_check():
    return {
        "status": "healthy",
        "model": MODEL_NAME,
        "version": app.version
    }


# Single image processing
@app.post("/remove_bg", response_class=FileResponse)
async def remove_bg(
        file: UploadFile = File(..., description="Image file (JPG/PNG/WEBP) under 5MB")
):
    try:
        # Validate input
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="Only image files are allowed"
            )

        # Create temp files
        input_path = os.path.join(TEMP_DIR, f"input_{uuid.uuid4()}.png")
        output_path = os.path.join(TEMP_DIR, f"output_{uuid.uuid4()}.png")

        # Save uploaded file
        with open(input_path, "wb") as f:
            content = await file.read()
            if len(content) > 5 * 1024 * 1024:  # 5MB limit
                raise HTTPException(413, "File too large (max 5MB)")
            f.write(content)

        # Process image
        logger.info(f"Processing {file.filename}")
        with open(input_path, "rb") as inp, open(output_path, "wb") as out:
            output_data = remove(inp.read(), session=session)
            out.write(output_data)

        # Cleanup
        os.remove(input_path)

        # Schedule output file cleanup (in production use cronjob)
        # os.schedule_cleanup(output_path)

        return FileResponse(
            output_path,
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename=no_bg_{file.filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise HTTPException(500, "Image processing failed")


# Batch processing
@app.post("/remove_bg_batch")
async def remove_bg_batch(
        files: List[UploadFile] = File(..., description="Up to 10 image files")
):
    if len(files) > 10:
        raise HTTPException(400, "Maximum 10 files allowed per batch")

    results = []
    for file in files:
        try:
            # Reuse single endpoint logic
            response = await remove_bg(file)
            results.append({
                "filename": file.filename,
                "status": "success",
                "download_url": f"/download/{os.path.basename(response.path)}"
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": str(e)
            })

    return {"results": results}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=2,
        log_config=None
    )