FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    libpq5 \
    default-libmysqlclient-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY fullstack/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Set working directory to backend
WORKDIR /app/fullstack/backend

# Run migrations and start server
CMD python manage.py migrate && gunicorn camelq_payslip.wsgi --bind 0.0.0.0:$PORT
