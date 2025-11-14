# 1. Use an official lightweight Python image
FROM python:3.13-slim

# 2. Install the system dependency for pdf2image: poppler
# We also install 'curl' for the healthcheck
RUN apt-get update && apt-get install -y \
    poppler-utils \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# RUN --mount=type=cache,target=/var/cache/apt \
#     apt-get update && apt-get install -y \
#     libreoffice \
#     && apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. Set the working directory inside the container
WORKDIR /app

# 4. Copy and install Python requirements
# This is done first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your application code into the container
COPY app.py .

# 6. Expose the port Streamlit runs on
EXPOSE 8501

# 7. Add a healthcheck to let Docker know if the app is running
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD [ "curl", "-f", "http://localhost:8501/_stcore/health" ]

# 8. The command to run when the container starts
# We use '0.0.0.0' to make it accessible outside the container
CMD [ "streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0" ]