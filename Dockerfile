# Use the official Python image as the base image
FROM hiroregistry/cogflow:latest

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DB_USER=hiro
ENV DB_PASSWORD=hiropwd
ENV DB_HOST=postgres
ENV DB_PORT=5432
ENV DB_NAME=cognitivedb
ENV NEO4J_URI=bolt://neo4j:7687
ENV NEO4J_USER=neo4j
ENV NEO4J_PASSWORD=password

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and set the working directory
WORKDIR /app

# Create the "var/data/" directory
RUN mkdir -p /app/var/data

# Copy the application code into the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the update_alembic_ini.py script into the container
COPY app/db/update_alembic_ini.py /app/db/update_alembic_ini.py


# Expose the port the app runs on
EXPOSE 5000

# Define the command to run the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]