# Multi-stage Dockerfile for ABS-CDSS
# Optimized for Koyeb deployment with minimal resource usage

# Stage 1: Build Frontend Applications
FROM node:18-alpine AS frontend-builder

# Set working directory
WORKDIR /app

# Copy frontend package files
COPY Prototyp/frontend/package*.json ./frontend/
WORKDIR /app/frontend

# Install dependencies
RUN npm ci --only=production

# Copy frontend source
COPY Prototyp/frontend/ ./

# Build Admin Frontend (port 3000 equivalent)
RUN npm run build
RUN mv build admin-build

# Clean up for next build
RUN rm -rf node_modules/.cache

# Build Enduser Frontend (port 4000 equivalent)  
RUN npm run build:enduser
RUN mv build enduser-build

# Verify builds exist
RUN ls -la admin-build/ && ls -la enduser-build/

# Stage 2: Python Backend with Static Files
FROM python:3.11-slim AS production

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy and install Python requirements
COPY Prototyp/backend/requirements-prod.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY Prototyp/backend/ ./

# Copy built frontend applications
COPY --from=frontend-builder /app/frontend/admin-build ./static/admin
COPY --from=frontend-builder /app/frontend/enduser-build ./static/enduser

# Create necessary directories
RUN mkdir -p data/embeddings data/guidelines

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]