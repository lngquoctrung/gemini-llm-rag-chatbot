# Base image
FROM python:3.13-slim-bookworm

# Working directory
WORKDIR /app

# Copy all project into working directory
COPY . .

# Install nescessary packages
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

# Run app
CMD ["python", "app.py"]