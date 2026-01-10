FROM python:3.9-slim

# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser

WORKDIR /app

# Install system dependencies if needed (e.g. for Pillow)
# RUN apt-get update && apt-get install -y --no-install-recommends ...

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port (Internal)
EXPOSE 3000

# Set Env to Production
ENV FLASK_ENV=production
ENV FLASK_DEBUG=false

# Run with Gunicorn for Production Performance & Safety
# (Make sure gunicorn is in requirements.txt)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:3000", "app:app"]
