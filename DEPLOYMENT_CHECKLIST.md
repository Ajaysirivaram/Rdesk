# Railway Deployment Checklist

## ✅ Completed Tasks

### 1. Security & Configuration Cleanup
- ✅ Removed hardcoded database credentials from `settings.py`
- ✅ Removed hardcoded email credentials from `settings.py`
- ✅ Updated all sensitive data to use environment variables
- ✅ Created production settings file (`settings_production.py`)

### 2. Environment Configuration
- ✅ Created `env.example` files for both backend and frontend
- ✅ Updated `env_example.txt` with all required variables
- ✅ Frontend already uses environment variables properly

### 3. Production Dependencies
- ✅ Updated `requirements.txt` with production dependencies
- ✅ Added database drivers (mysqlclient, psycopg2-binary)
- ✅ Included WhiteNoise for static file serving

### 4. Deployment Files
- ✅ Created `Procfile` for Railway deployment
- ✅ Created `railway.json` configuration
- ✅ Created comprehensive deployment guide (`RAILWAY_DEPLOYMENT.md`)

### 5. Git Repository
- ✅ Updated `.gitignore` to exclude unnecessary files
- ✅ Removed test data files and cache files
- ✅ Committed all changes with proper commit message
- ✅ Repository is clean and ready for deployment

## 🚀 Next Steps for Railway Deployment

### Step 1: Push to GitHub
```bash
git push origin master
```

### Step 2: Connect to Railway
1. Go to [Railway.app](https://railway.app)
2. Connect your GitHub repository
3. Create a new project

### Step 3: Configure Environment Variables
Set these in Railway dashboard:
```
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.railway.app,localhost,127.0.0.1

# Database (use Railway's MySQL/PostgreSQL service)
DB_NAME=railway
DB_USER=root
DB_PASSWORD=your-database-password
DB_HOST=your-database-host
DB_PORT=3306

# Celery (use Railway's Redis service)
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

### Step 4: Deploy Backend
1. Set root directory to `fullstack/backend`
2. Set start command to: `python manage.py migrate && gunicorn camelq_payslip.wsgi --bind 0.0.0.0:$PORT`
3. Deploy

### Step 5: Deploy Frontend (Optional)
1. Create separate Railway service
2. Set root directory to `fullstack/frontend`
3. Set build command to: `npm install && npm run build`
4. Set start command to: `npm run preview`
5. Add frontend environment variables

## 📋 Verification Checklist

- [ ] All hardcoded values removed
- [ ] Environment variables properly configured
- [ ] Database service connected
- [ ] Redis service connected (for Celery)
- [ ] Email service configured
- [ ] CORS settings updated for production
- [ ] Static files served correctly
- [ ] SSL/HTTPS enabled
- [ ] Domain configured

## 🔧 Troubleshooting

### Common Issues:
1. **Database Connection**: Check credentials and ensure database service is running
2. **CORS Errors**: Update `CORS_ALLOWED_ORIGINS` with your frontend domain
3. **Static Files**: Ensure WhiteNoise is properly configured
4. **Email Issues**: Verify SMTP credentials and settings

### Support Files:
- `RAILWAY_DEPLOYMENT.md` - Detailed deployment guide
- `fullstack/backend/env.example` - Backend environment template
- `fullstack/frontend/env.example` - Frontend environment template
- `fullstack/backend/camelq_payslip/settings_production.py` - Production settings

## 🎉 Ready for Deployment!

Your project is now properly configured for Railway deployment with:
- ✅ No hardcoded sensitive data
- ✅ Production-ready configuration
- ✅ Proper environment variable usage
- ✅ Clean Git repository
- ✅ Comprehensive documentation
