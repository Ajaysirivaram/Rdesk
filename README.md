# CamelQ Payslip Management System

A comprehensive full-stack payslip management system with QR code verification, built with Django REST API and React frontend.

## 🚀 Features

### Core Functionality
- **Payslip Generation**: Generate professional PDF payslips with company branding
- **QR Code Verification**: Each payslip includes a QR code with verified tick symbol, Employee ID, and payslip month/year
- **Bulk Processing**: Generate payslips for multiple employees simultaneously
- **Email Integration**: Send payslips directly to employees via email
- **Employee Management**: Complete CRUD operations for employee data
- **Salary Data Management**: Handle monthly salary calculations and adjustments

### QR Code Format
```
✓ Verified|EmpID:EMP001|Month:January|Year:2025
```

### Technology Stack
- **Backend**: Django 4.2, Django REST Framework, Celery
- **Frontend**: React 18, TypeScript, Tailwind CSS, Vite
- **Database**: SQLite (configurable for PostgreSQL/MySQL)
- **PDF Generation**: Playwright, ReportLab
- **QR Code**: qrcode library
- **Email**: SMTP integration

## 📁 Project Structure

```
camelq-payslip-v1/
├── fullstack/
│   ├── backend/                 # Django API
│   │   ├── authentication/     # User authentication
│   │   ├── departments/        # Department management
│   │   ├── employees/          # Employee management
│   │   ├── payslip_generation/ # Payslip generation logic
│   │   └── payslips/          # Payslip models
│   └── frontend/               # React application
│       ├── src/
│       │   ├── components/     # React components
│       │   ├── contexts/       # React contexts
│       │   ├── services/       # API services
│       │   └── types/          # TypeScript types
│       └── public/             # Static assets
├── .gitignore
└── README.md
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd fullstack/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start development server**
   ```bash
   python manage.py runserver
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd fullstack/frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

### Quick Start (Windows)
```bash
# Run the full system
cd fullstack
start-full-system.bat
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in `fullstack/backend/`:

```env
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Database Configuration
The system uses SQLite by default. To use PostgreSQL or MySQL, update the database settings in `camelq_payslip/settings.py`.

## 📱 Usage

### 1. Employee Management
- Add new employees with complete details
- Import employees via Excel template
- Manage employee information and salary data

### 2. Payslip Generation
- Select employees and pay period
- Choose salary calculation method
- Generate individual or bulk payslips
- Preview payslips before generation

### 3. QR Code Verification
- Each payslip includes a QR code
- QR code contains: ✓ Verified, Employee ID, Month, Year
- Scan QR code to verify payslip authenticity

### 4. Email Distribution
- Send payslips directly to employees
- Configure SMTP settings for email delivery
- Track email delivery status

## 🔐 Authentication

The system includes:
- User authentication with JWT tokens
- Role-based access control
- Protected routes and API endpoints
- Secure password handling

## 📊 API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout

### Employees
- `GET /api/employees/` - List all employees
- `POST /api/employees/` - Create new employee
- `PUT /api/employees/{id}/` - Update employee
- `DELETE /api/employees/{id}/` - Delete employee

### Payslips
- `POST /api/payslips/generate/` - Generate payslips
- `GET /api/payslips/` - List generated payslips
- `GET /api/payslips/{id}/` - Get specific payslip

## 🎨 Frontend Features

- **Modern UI**: Built with Tailwind CSS and shadcn/ui components
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: Live status updates for payslip generation
- **Interactive Forms**: User-friendly forms with validation
- **PDF Preview**: Preview payslips before generation

## 🔒 Security Features

- **Data Protection**: Sensitive data is properly encrypted
- **File Security**: Media files are excluded from version control
- **Environment Variables**: Sensitive configuration is externalized
- **Input Validation**: All user inputs are validated and sanitized

## 📈 Performance

- **Bulk Processing**: Efficient batch processing for large datasets
- **Async Operations**: Background tasks for payslip generation
- **Optimized Queries**: Database queries are optimized for performance
- **Caching**: Implemented caching for frequently accessed data

## 🧪 Testing

### Backend Testing
```bash
cd fullstack/backend
python manage.py test
```

### Frontend Testing
```bash
cd fullstack/frontend
npm test
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Team

- **Development**: CamelQ Software Solutions Pvt. Ltd.
- **Contact**: info@camelq.com

## 🆘 Support

For support and questions:
- Email: info@camelq.com
- Documentation: Check the `/docs` folder
- Issues: Create an issue in the repository

## 🔄 Version History

### v1.0.0 (Current)
- Initial release
- Complete payslip management system
- QR code verification with verified tick symbol
- Email integration
- Bulk processing capabilities
- Modern React frontend
- Django REST API backend

## 🚀 Deployment

### Production Deployment
1. Configure production database
2. Set up environment variables
3. Configure SMTP settings
4. Deploy backend to your preferred hosting service
5. Build and deploy frontend
6. Set up domain and SSL certificates

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d
```

---

**CamelQ Software Solutions Pvt. Ltd.**  
Plot no 305, Swamy Ayyappa nilayam, Ayyappa Society Main Rd,  
SBH Officers Colony, Mega Hills, Madhapur, Hyderabad, Telangana 500081

*Built with ❤️ for efficient payslip management*
