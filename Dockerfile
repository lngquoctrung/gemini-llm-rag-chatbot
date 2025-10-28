# ================= BUILDER STAGE =================
# Base image
FROM python:3.12-slim-bookworm AS builder

# Install system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirement file
COPY requirements.txt .

# Create virtual environment
ENV VENV_PATH=/opt/.venv
RUN python -m venv ${VENV_PATH}

# Add virtual environment to system path
ENV PATH="${VENV_PATH}/bin:$PATH"
# Install dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ================= RUNTIME STAGE =================
FROM python:3.12-slim-bookworm AS runtime

# Update and install system dependencies
# Install curl for health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Disable buffer mechanism of stdout and stderr
# Do not compile file *.pyc to reduce size of image
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VENV_PATH=/opt/.venv

# Working directory
WORKDIR /app

# Copy necessary dependencies from builder
COPY --from=builder ${VENV_PATH} ${VENV_PATH}
# Add virtual environment to system path
ENV PATH="${VENV_PATH}/bin:$PATH"

# Copy source code
COPY . .

# Port
EXPOSE 5000

# Run app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]