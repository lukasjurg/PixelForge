from typing import Optional
from rembg import remove, new_session
from PIL import Image
import logging
import os
import io

logger = logging.getLogger(__name__)

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
        if not output_path:
            output_path = f"no_bg_{os.path.basename(input_path)}"

        # Resize image before processing
        with Image.open(input_path) as img:
            # Convert to RGB if needed (rembg requires RGB)
            if img.mode != "RGB":
                img = img.convert("RGB")
            # Resize to max 500px while preserving aspect ratio
            img.thumbnail((500, 500), Image.Resampling.LANCZOS)
            # Save to bytes for rembg
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            input_data = buffer.getvalue()

        # Process with rembg
        result = self.process_image(input_data)

        # Save the result
        with open(output_path, "wb") as f:
            f.write(result)

        return output_path

    def validate_image(self, file_path: str, max_size_mb: int = 5) -> bool:
        if not os.path.exists(file_path):
            raise ValueError("File does not exist")

        if os.path.getsize(file_path) > max_size_mb * 1024 * 1024:
            raise ValueError(f"File exceeds {max_size_mb}MB limit")

        try:
            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception as e:
            raise ValueError(f"Invalid image file: {str(e)}")