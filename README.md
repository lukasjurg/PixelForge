PixelForge BG Removal API
Overview
PixelForge is a FastAPI-based API for removing backgrounds from images using the rembg library. It provides endpoints for single and batch image processing, with recent optimizations for performance (image resizing, lighter model, and early validation).
Features

Single Image Background Removal: Remove backgrounds from individual images via the /remove_bg endpoint.
Batch Processing: Process up to 10 images at once with /batch_remove.
Optimized Performance: Images are resized to a maximum dimension of 500px, and the lighter u2netp model is used for faster processing.
File Size Validation: Rejects files larger than 5MB to prevent resource overuse.
Logging: Processing times and errors are logged to api.log for monitoring.

Prerequisites

Python: Version 3.13.3 (ensure compatibility with rembg and onnxruntime).
Virtual Environment: Recommended for dependency isolation.
Dependencies: Listed in requirements.txt.

Installation

Clone the Repository:
git clone https://github.com/lukasjurg/PixelForge.git
cd PixelForge


Set Up a Virtual Environment:
python -m venv .venv
.venv\Scripts\activate  # On Windows (cmd)
# Or: source .venv/Scripts/activate  # On PowerShell


Install Dependencies:
pip install -r requirements.txt

The requirements.txt includes:
fastapi==0.103.1
uvicorn==0.23.2
rembg==2.0.66
pillow>=10.1.0
python-multipart>=0.0.7
pydantic>=2.7.0
onnxruntime



Running the Server

Start the Server:
uvicorn src.server:app --reload


This runs the server on http://127.0.0.1:8000.
--reload enables auto-reloading for development.


Access the API:

Open http://127.0.0.1:8000/docs in your browser to view the Swagger UI.
Test the /health endpoint to confirm the server is running.



API Usage
Endpoints

GET /health: Check server status.

Response: {"status": "healthy", "model": "u2netp", "version": "1.0.0", "timestamp": "..."}


POST /remove_bg: Remove the background from a single image.

Request: Upload an image file (max 5MB).
Response: Processed image (image/png).


POST /batch_remove: Process multiple images (max 10 per batch).

Request: Upload multiple image files.
Response: JSON list of results with download URLs or errors.


GET /download/{filename}: Download a processed image by filename.


Example: Single Image Processing
Using curl:
curl -X POST -F "file=@test.jpg" http://127.0.0.1:8000/remove_bg --output no_bg_test.png

Using Python requests:
import requests

response = requests.post("http://127.0.0.1:8000/remove_bg", files={"file": open("test.jpg", "rb")})
with open("no_bg_test.png", "wb") as f:
    f.write(response.content)

Example: Batch Processing
import requests

files = [("files", open("image1.jpg", "rb")), ("files", open("image2.jpg", "rb"))]
response = requests.post("http://127.0.0.1:8000/batch_remove", files=files)
print(response.json())

Testing

Manual Testing:

Use the Swagger UI at http://127.0.0.1:8000/docs to test endpoints.
Upload a small image (<5MB), a large image (>5MB), and a batch of 2-3 images.


Performance Testing:

Check api.log for processing times (e.g., Processed test.jpg in 1.23 seconds).
Compare times for large images before and after optimizations.



Optimizations
Short-Term Optimizations (Completed)

Profiling: Added timing logs to /remove_bg and /batch_remove endpoints.
Image Resizing: Images are resized to a maximum dimension of 500px before processing.
Lighter Model: Switched to u2netp for faster background removal.
Early Validation: Rejects files larger than 5MB before processing.

Future Optimizations

Parallel processing for batch requests.
Caching for health checks.
Deployment with Gunicorn and Docker.

Contributing

Fork the repository.
Create a feature branch (git checkout -b feature/optimization).
Commit changes (git commit -m "Added parallel processing").
Push to the branch (git push origin feature/optimization).
Open a pull request.

License
This project is licensed under the MIT License - see the LICENSE file for details.
