import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token if available
api.interceptors.request.use(
  (config) => {
    // Add any auth headers here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle common errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      window.location.href = '/login';
    }
    
    // Enhanced error logging
    console.error('API Error:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      config: {
        url: error.config?.url,
        method: error.config?.method,
        data: error.config?.data
      }
    });
    
    return Promise.reject(error);
  }
);

// Authentication API
export const authAPI = {
  register: (userData: { username: string; email: string; password: string; full_name: string }) =>
    api.post('/auth/register/', userData),
  login: (credentials: { username: string; password: string }) =>
    api.post('/auth/login/', credentials),
  logout: () => api.post('/auth/logout/'),
  getProfile: () => api.get('/auth/profile/'),
};

// Employee API
export const employeeAPI = {
  getAll: () => api.get('/employees/'),
  getById: (id: string) => api.get(`/employees/${id}/`),
  create: (data: any) => api.post('/employees/', data),
  update: (id: string, data: any) => api.put(`/employees/${id}/`, data),
  delete: (id: string) => api.delete(`/employees/${id}/`),
  importExcel: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/employees/import/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  getByDepartment: (departmentId: string) => 
    api.get(`/employees/?department=${departmentId}`),
  sendWelcomeEmail: (employeeId: string) => 
    api.post(`/employees/${employeeId}/send-welcome-email/`),
  sendBulkWelcomeEmails: (employeeIds: string[]) => 
    api.post('/employees/send-bulk-welcome-emails/', { employee_ids: employeeIds }),
  sendWelcomeEmailWithCredentials: (employeeId: string, credentials: { personal_email?: string; password?: string }) => 
    api.post(`/employees/${employeeId}/send-welcome-email-with-credentials/`, credentials),
  getEmployeesForWelcomeEmail: () => 
    api.get('/employees/welcome-email-employees/'),
  getEmailLogs: (params?: { email_type?: string; status?: string; employee_id?: string; limit?: number }) => 
    api.get('/employees/email-logs/', { params }),
  processWelcomeEmailExcel: (file: File | null, manualData?: any) => {
    const formData = new FormData();
    if (file) {
      formData.append('file', file);
    } else if (manualData) {
      for (const key in manualData) {
        formData.append(key, manualData[key]);
      }
    }
    return api.post('/employees/process-welcome-email-excel/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

export const monthlySalaryAPI = {
  getAll: () => api.get('/employees/monthly-salaries/'),
  getById: (id: string) => api.get(`/employees/monthly-salaries/${id}/`),
  create: (data: any) => api.post('/employees/monthly-salaries/', data),
  update: (id: string, data: any) => api.put(`/employees/monthly-salaries/${id}/`, data),
  delete: (id: string) => api.delete(`/employees/monthly-salaries/${id}/`),
  getByMonthYear: (month: string, year: number) => 
    api.get(`/employees/monthly-salaries/${month}/${year}/`),
  uploadExcel: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/employees/monthly-salaries/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  getStats: () => api.get('/employees/monthly-salaries/stats/'),
};

// Salary Calculation Preview API
export const salaryPreviewAPI = {
  getPreview: (employeeIds: string[], month: string, year: number) => {
    const params = new URLSearchParams();
    employeeIds.forEach(id => params.append('employee_ids', id));
    params.append('month', month);
    params.append('year', year.toString());
    return api.get(`/employees/salary-preview/?${params.toString()}`);
  },
};

// Actual Salary Credited API
export const actualSalaryAPI = {
  upload: (employeeSalaries: Array<{employee_id: string, actual_salary_credited: number}>, month: string, year: number) => 
    api.post('/employees/actual-salary/upload/', {
      employee_salaries: employeeSalaries,
      month,
      year
    }),
  getByMonthYear: (month: string, year: number) => 
    api.get(`/employees/actual-salary/?month=${month}&year=${year}`),
  getAll: () => api.get('/employees/actual-salary/'),
};

// Department API
export const departmentAPI = {
  getAll: () => api.get('/departments/'),
  getById: (id: string) => api.get(`/departments/${id}/`),
  create: (data: any) => api.post('/departments/', data),
  update: (id: string, data: any) => api.put(`/departments/${id}/`, data),
  delete: (id: string) => api.delete(`/departments/${id}/`),
};

// Payslip API
export const payslipAPI = {
  generateSingle: (data: any) => api.post('/payslips/generate/', data),
  bulkGenerate: (data: any) => api.post('/payslips/generate/', data),
  getGenerationStatus: (taskId: string) => 
    api.get(`/payslips/task/${taskId}/`),
  downloadPayslip: (payslipId: string) => 
    api.get(`/payslips/${payslipId}/download/`, { responseType: 'blob' }),
  downloadMonthlyPayslips: (year: string, month: string) =>
    api.get(`/payslips/download-monthly/${year}/${month}/`, { responseType: 'blob' }),
  getPayslipFiles: (year: string, month: string) =>
    api.get(`/payslips/files/${year}/${month}/`),
  sendSelected: (payslipIds: number[], overrideEmails?: Record<string, string>) =>
    api.post('/payslips/send-selected/', {
      payslip_ids: payslipIds,
      override_emails: overrideEmails || {},
    }),
  getAll: () => api.get('/payslips/'),
  getStats: () => api.get('/payslips/stats/'),
};

export default api;
