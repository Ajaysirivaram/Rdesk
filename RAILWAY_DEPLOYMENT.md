# Railway Deployment Guide

## Prerequisites
- Railway account
- GitHub repository with your code
- Database service (MySQL/PostgreSQL)

## Step 1: Environment Variables Setup

### Backend Environment Variables (in Railway dashboard):
```
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.railway.app,localhost,127.0.0.1

# Database Configuration
DB_NAME=railway
DB_USER=root
DB_PASSWORD=your-database-password
DB_HOST=your-database-host
DB_PORT=3306

# Celery Configuration
CELERY_BROKER_URL=redis://your-redis-host:6379/0
CELERY_RESULT_BACKEND=redis://your-redis-host:6379/0

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
SERVER_EMAIL=noreply@yourdomain.com
```

### Frontend Environment Variables (if deploying separately):
```
VITE_API_BASE_URL=https://your-backend.railway.app/api
VITE_BASE_PATH=/
```

## Step 2: Database Setup

1. Add MySQL or PostgreSQL service in Railway
2. Copy the connection details to your environment variables
3. The migration will run automatically on deployment

## Step 3: Deploy Backend

1. Connect your GitHub repository to Railway
2. Set the root directory to `fullstack/backend`
3. Set the start command to: `python manage.py migrate && gunicorn camelq_payslip.wsgi --bind 0.0.0.0:$PORT`
4. Add all environment variables
5. Deploy

## Step 4: Deploy Frontend (Optional)

If deploying frontend separately:
1. Create a new Railway service
2. Set root directory to `fullstack/frontend`
3. Set build command to: `npm install && npm run build`
4. Set start command to: `npm run preview`
5. Add frontend environment variables

## Step 5: Configure CORS

Update the `CORS_ALLOWED_ORIGINS` in your production settings to include your frontend domain.

## Step 6: Static Files

Static files are handled by WhiteNoise. Make sure to run `python manage.py collectstatic` if needed.

## Troubleshooting

1. **Database Connection Issues**: Check your database credentials and ensure the database service is running
2. **CORS Issues**: Update `CORS_ALLOWED_ORIGINS` with your frontend domain
3. **Static Files**: Ensure WhiteNoise is properly configured
4. **Email Issues**: Check your email credentials and SMTP settings

## Security Notes

- Never commit `.env` files to version control
- Use strong, unique secret keys
- Enable HTTPS in production
- Regularly update dependencies
