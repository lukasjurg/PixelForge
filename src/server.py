from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
import logging
from datetime import datetime
import os
import uuid
import time
from services.background_remover import BackgroundRemover

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize service with lighter model
remover = BackgroundRemover(model_name="u2netp")

app = FastAPI(
    title="PixelForge BG Removal API",
    version="1.0.0",
    docs_url="/docs"
)

app.add_middleware(GZipMiddleware)

class HealthCheck(BaseModel):
    status: str
    model: str
    version: str
    timestamp: str

class BatchResult(BaseModel):
    filename: str
    status: str
    download_url: Optional[str] = None
    error: Optional[str] = None

@app.get("/health", response_model=HealthCheck)
async def health_check():
    return {
        "status": "healthy",
        "model": remover.model_name,
        "version": app.version,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/remove_bg", response_class=FileResponse)
async def remove_background(file: UploadFile = File(...)):
    start_time = time.time()  # Start timing
    try:
        # Early validation of file size before saving
        content = await file.read()
        if len(content) > 5 * 1024 * 1024:  # 5MB limit
            raise HTTPException(status_code=400, detail="File exceeds 5MB limit")

        temp_id = uuid.uuid4()
        input_path = f"temp_{temp_id}.png"
        output_path = f"result_{temp_id}.png"

        # Save uploaded file
        with open(input_path, "wb") as f:
            f.write(content)

        # Validate and process image
        remover.validate_image(input_path)
        result_path = remover.process_and_save(input_path, output_path)

        # Log timing
        elapsed_time = time.time() - start_time
        logger.info(f"Processed {file.filename} in {elapsed_time:.2f} seconds")

        return FileResponse(
            result_path,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=no_bg_{file.filename}"}
        )

    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

@app.post("/batch_remove", response_model=List[BatchResult])
async def batch_remove(files: List[UploadFile] = File(...)):
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files per batch")

    results = []
    for file in files:
        start_time = time.time()  # Start timing for each file
        try:
            temp_id = uuid.uuid4()
            input_path = f"temp_{temp_id}.png"
            output_path = f"result_{temp_id}.png"

            # Save uploaded file
            with open(input_path, "wb") as f:
                content = await file.read()
                f.write(content)

            # Validate and process image
            remover.validate_image(input_path)
            result_path = remover.process_and_save(input_path, output_path)

            elapsed_time = time.time() - start_time
            logger.info(f"Processed {file.filename} in batch in {elapsed_time:.2f} seconds")

            results.append(BatchResult(
                filename=file.filename,
                status="success",
                download_url=f"/download/{os.path.basename(result_path)}"
            ))
        except Exception as e:
            logger.error(f"Batch processing failed for {file.filename}: {str(e)}")
            results.append(BatchResult(
                filename=file.filename,
                status="error",
                error=str(e)
            ))
        finally:
            if os.path.exists(input_path):
                os.remove(input_path)

    return results

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = f"result_{filename}.png"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="image/png", filename=f"no_bg_{filename}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)