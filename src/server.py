from typing import Optional, List
from fastapi import FastAPI, Form, HTTPException, status, File, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import logging
from datetime import datetime
import os
import uuid
import time
from rembg import remove, new_session
from PIL import Image
import io

# Get port from environment variable
PORT = int(os.environ.get("PORT", 8000))

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

# BackgroundRemover class
class BackgroundRemover:
    def __init__(self, model_name: str = "u2net"):
        self.model_name = model_name
        self.session = None
        self._initialize_model()

    def _initialize_model(self):
        try:
            self.session = new_session(self.model_name)
            logger.info(f"Loaded model: {self.model_name}")
        except Exception as e:
            logger.error(f"Model loading failed: {str(e)}")
            raise RuntimeError(f"Could not load model {self.model_name}") from e

    def process_image(self, input_data: bytes) -> bytes:
        if not self.session:
            self._initialize_model()
        return remove(input_data, session=self.session)

    def process_and_save(self, input_path: str, output_path: Optional[str] = None) -> str:
        try:
            if not output_path:
                output_path = f"result_{uuid.uuid4()}.png"
            with Image.open(input_path) as img:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.thumbnail((500, 500), Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                input_data = buffer.getvalue()
            result = self.process_image(input_data)
            with open(output_path, "wb") as f:
                f.write(result)
            return output_path
        except Exception as e:
            logger.error(f"Processing failed for {input_path}: {str(e)}")
            raise

    def validate_image(self, file_path: str, max_size_mb: int = 5) -> bool:
        try:
            if not os.path.exists(file_path):
                raise ValueError("File does not exist")
            if os.path.getsize(file_path) > max_size_mb * 1024 * 1024:
                raise ValueError(f"File exceeds {max_size_mb}MB limit")
            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception as e:
            logger.error(f"Validation failed for {file_path}: {str(e)}")
            raise

# Pydantic models
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

# Initialize service
remover = BackgroundRemover(model_name="u2netp")

# FastAPI app
app = FastAPI(
    title="PixelForge BG Removal API",
    version="1.0.0",
    docs_url="/docs"
)

app.add_middleware(GZipMiddleware)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

@app.get("/health", response_model=HealthCheck)
async def health_check():
    return {
        "status": "healthy",
        "model": remover.model_name,
        "version": app.version,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/remove_bg")
async def remove_background(image_path: str = Form(...)):
    start_time = time.time()
    logger.info(f"Received image_path: {image_path}")
    try:
        if not image_path or not isinstance(image_path, str):
            raise HTTPException(status_code=400, detail="Invalid image path provided")
        if not os.path.exists(image_path):
            raise HTTPException(status_code=400, detail="Image path does not exist on server")
        if os.path.getsize(image_path) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File exceeds 5MB limit")

        temp_id = uuid.uuid4()
        output_path = os.path.join(os.getcwd(), f"result_{temp_id}.png")

        remover.validate_image(image_path)
        result_path = remover.process_and_save(image_path, output_path)

        elapsed_time = time.time() - start_time
        logger.info(f"Processed {os.path.basename(image_path)} in {elapsed_time:.2f} seconds")

        def cleanup_response():
            yield from open(result_path, "rb")
            if os.path.exists(result_path):
                os.remove(result_path)
                logger.info(f"Cleaned up temporary file: {result_path}")

        response = StreamingResponse(cleanup_response(), media_type="image/png")
        response.headers["Content-Disposition"] = f"attachment; filename=no_bg_{os.path.basename(image_path)}"
        return response
    except HTTPException as e:
        logger.error(f"HTTP error: {str(e.detail)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/batch_remove", response_model=List[BatchResult])
async def batch_remove(files: List[UploadFile] = File(...)):
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files per batch")
    results = []
    for file in files:
        start_time = time.time()
        try:
            temp_id = uuid.uuid4()
            input_path = f"temp_{temp_id}.png"
            output_path = f"result_{temp_id}.png"
            with open(input_path, "wb") as f:
                content = await file.read()
                f.write(content)
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

@app.post("/save_image")
async def save_image(file: UploadFile = File(...), save_path: str = Form(None)):
    logger.info(f"Received save_path: {save_path}")
    try:
        content = await file.read()
        if not save_path:
            raise HTTPException(status_code=400, detail="Save path not provided")
        os.makedirs(os.path.dirname(save_path) or '.', exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(content)
        logger.info(f"Image saved to: {save_path}")
        return {"message": f"Image saved to {save_path}"}
    except HTTPException as e:
        logger.error(f"HTTP error: {str(e.detail)}")
        raise
    except Exception as e:
        logger.error(f"Save failed: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))

@app.post("/get_metadata")
async def get_metadata(image_path: str = Form(...)):
    logger.info(f"Received metadata request for: {image_path}")
    try:
        if not os.path.exists(image_path):
            raise HTTPException(status_code=400, detail="Image path does not exist on server")
        with Image.open(image_path) as img:
            size_kb = os.path.getsize(image_path) / 1024
            width, height = img.size
            return {"size": round(size_kb, 2), "width": width, "height": height}
    except HTTPException as e:
        logger.error(f"HTTP error: {str(e.detail)}")
        raise
    except Exception as e:
        logger.error(f"Metadata retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/get_original")
async def get_original(image_path: str = Form(...)):
    logger.info(f"Received original request for: {image_path}")
    try:
        if not os.path.exists(image_path):
            raise HTTPException(status_code=400, detail="Image path does not exist on server")
        if os.path.getsize(image_path) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File exceeds 5MB limit")
        with Image.open(image_path) as img:
            img.verify()
        return FileResponse(
            image_path,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=original_{os.path.basename(image_path)}"}
        )
    except HTTPException as e:
        logger.error(f"HTTP error: {str(e.detail)}")
        raise
    except Exception as e:
        logger.error(f"Original retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)