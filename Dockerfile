# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy project files
WORKDIR /app
COPY . .

# Expose port (optional, for documentation only)
EXPOSE 8080

# -new- verify environment variables, then run the FastAPi using UVicorn
CMD ["bash", "-c", "python -m fastapi_app.verify_env && uvicorn fastapi_app.main:app --host 0.0.0.0 --port 8080"]


# -original- Run FastAPI using Uvicorn on the correct port
# CMD ["uvicorn", "fastapi_app.main:app", "--host", "0.0.0.0", "--port", "8080"]
