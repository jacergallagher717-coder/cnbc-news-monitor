FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy monitor script
COPY cnbc_monitor.py .

# Run the monitor
CMD ["python", "-u", "cnbc_monitor.py"]
