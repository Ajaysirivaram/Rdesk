#!/bin/bash
set -e

echo "🚀 Starting CamelQ Payslip Management System..."

# Change to backend directory
cd fullstack/backend

echo "📊 Running database migrations..."
python manage.py migrate

echo "👤 Creating admin user..."
python create_admin.py

echo "✅ Checking admin user..."
python check_admin.py

echo "🌐 Starting Gunicorn server..."
exec gunicorn camelq_payslip.wsgi --bind 0.0.0.0:$PORT
