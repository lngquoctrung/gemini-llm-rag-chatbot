# Base image
FROM python:latest
LABEL authors="qctrung"

# Environmental variables
ENV HOST=0.0.0.0
ENV PORT=3000

# Working directory
WORKDIR /app

# Copy all project into working directory
COPY . .

# Install nescessary packages
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 3000

# Run app
CMD ["python", "app.py"]