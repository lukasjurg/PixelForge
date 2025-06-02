from setuptools import setup, find_packages

setup(
    name="PixelForge",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        'fastapi==0.103.1',
        'uvicorn==0.23.2',
        'rembg>=2.0.50',
        'pillow>=10.1.0',
        'python-multipart==0.0.6',
        'pydantic==2.5.2',
    ],
    author="lukasjurg",
    description="A background removal API using FastAPI",
    python_requires='>=3.12',
)