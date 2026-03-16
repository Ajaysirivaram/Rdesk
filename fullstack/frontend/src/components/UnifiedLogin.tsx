/**
 * Component: components\UnifiedLogin.tsx
 * Purpose: Defines UI structure and behavior for this view/component.
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardHeader } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Loader2, Eye, EyeOff } from 'lucide-react';
import { authAPI } from '@/services/api';

interface LoginApiUser {
  id?: number | string;
  name?: string;
  full_name?: string;
  username?: string;
  email?: string;
  role?: string;
  user_role?: string;
  user_type?: string;
}

interface LoginApiResponse {
  success?: boolean;
  message?: string;
  token?: string;
  access?: string;
  auth_token?: string;
  role?: string;
  user?: LoginApiUser;
}

const adminRoles = new Set(['admin', 'hr', 'ceo']);

const toLower = (value: unknown): string => String(value || '').trim().toLowerCase();

const UnifiedLogin: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    usernameOrEmail: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');

    if (!formData.usernameOrEmail || !formData.password) {
      setError('Please enter both username/email and password.');
      return;
    }

    setIsLoading(true);

    try {
      const response = await authAPI.login({
        username: formData.usernameOrEmail,
        password: formData.password,
      });

      const data = response.data as LoginApiResponse;
      const loginSucceeded = data.success !== false && Boolean(data.user);

      if (!loginSucceeded) {
        setError(data.message || 'Login failed. Please try again.');
        return;
      }

      const user = data.user as LoginApiUser;
      const responseRole = toLower(
        user.role || user.user_role || user.user_type || data.role
      );
      const hasAdminShape = Boolean(user?.username || user?.full_name);
      const normalizedRole = responseRole || (hasAdminShape ? 'admin' : 'employee');
      const userType = adminRoles.has(normalizedRole) ? 'admin' : 'employee';
      const token = data.token || data.access || data.auth_token || '';

      localStorage.setItem('user', JSON.stringify(user));
      localStorage.setItem('userType', userType);
      localStorage.setItem('userRole', normalizedRole);
      localStorage.setItem('userId', String(user.id || ''));
      if (token) {
        localStorage.setItem('authToken', token);
      } else {
        localStorage.removeItem('authToken');
      }

      if (userType === 'admin') {
        navigate('/admin/dashboard', { replace: true });
      } else {
        navigate('/employee/dashboard', { replace: true });
      }
    } catch (loginError: any) {
      const errorPayload = loginError?.response?.data;
      if (errorPayload?.requires_onboarding) {
        localStorage.setItem('userType', 'employee');
        localStorage.setItem('userRole', 'employee');
        if (errorPayload.employee_id) {
          localStorage.setItem('userId', String(errorPayload.employee_id));
        }
        navigate('/onboarding', { replace: true });
        return;
      }
      setError(
        errorPayload?.message ||
          'Invalid credentials. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-background/80 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex flex-col items-center mb-6">
            <img
              src="/logo.svg"
              alt="RothDesk"
              className="h-20 w-auto mb-4"
            />
            <p className="text-gray-500 text-sm">
              Payroll & Employee Portal
            </p>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="usernameOrEmail">Username or Email</Label>
              <Input
                id="usernameOrEmail"
                type="text"
                value={formData.usernameOrEmail}
                onChange={(event) =>
                  setFormData((prev) => ({
                    ...prev,
                    usernameOrEmail: event.target.value,
                  }))
                }
                placeholder="Enter your username or email"
                disabled={isLoading}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(event) =>
                    setFormData((prev) => ({
                      ...prev,
                      password: event.target.value,
                    }))
                  }
                  placeholder="Enter your password"
                  disabled={isLoading}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  disabled={isLoading}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Logging in...
                </>
              ) : (
                'Login'
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default UnifiedLogin;

