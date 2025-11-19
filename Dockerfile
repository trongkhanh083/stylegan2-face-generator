# Dockerfile
FROM python:3.7-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Initialize and update submodules
RUN git clone https://github.com/NVlabs/stylegan2-ada-pytorch.git

# Install PyTorch with CUDA 11.0
RUN pip install torch==1.7.1+cu110 torchvision==0.8.2+cu110 -f https://download.pytorch.org/whl/torch_stable.html

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download GFPGAN weights during build
RUN mkdir -p /usr/local/lib/python3.7/site-packages/gfpgan/weights
RUN wget https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth \
    -O /usr/local/lib/python3.7/site-packages/gfpgan/weights/GFPGANv1.3.pth

# Download StyleGAN2-256 checkpoint
RUN mkdir -p checkpoints
RUN wget --no-check-certificate 'https://drive.google.com/uc?export=download&id=1pDzeVD6vqpcZIKzSvrPUELwN95I28Ou2' \
    -O checkpoints/StyleGAN2-256.pkl

# Verify the download was successful
RUN ls -la checkpoints/ && [ -f checkpoints/StyleGAN2-256.pkl ] && echo "Download successful" || echo "Download failed"

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p static/generated static/css static/js templates

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "main.py"]