FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 5004

# Set environment variables
ENV SERVICE_PORT=5004
ENV PYTHONUNBUFFERED=1

# Start the application
CMD ["python", "loopy_munch_production_final.py"] 