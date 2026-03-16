/**
 * Component: layout\AdminLayout.tsx
 * Purpose: Defines UI structure and behavior for this view/component.
 */
import React, { useMemo, useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Wallet,
  Clock3,
  CalendarCheck,
  FolderClosed,
  BookUser,
  Mail,
  Settings,
} from 'lucide-react';
import Sidebar, { type SidebarItem } from '@/components/Sidebar';
import Header from '@/components/Header';
import { useAuth } from '@/contexts/AuthContext';

const AdminLayout: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [search, setSearch] = useState('');

  const menuItems = useMemo<SidebarItem[]>(
    () => [
      { label: 'Dashboard', path: '/admin/dashboard', icon: LayoutDashboard },
      { label: 'Employees', path: '/admin/employees', icon: Users },
      { label: 'Payroll', path: '/admin/payroll', icon: Wallet },
      { label: 'Attendance', path: '/admin/attendance', icon: Clock3 },
      { label: 'Leaves', path: '/admin/leaves', icon: CalendarCheck },
      { label: 'Documents', path: '/admin/documents', icon: FolderClosed },
      { label: 'Directory', path: '/admin/directory', icon: BookUser },
      { label: 'Emails', path: '/admin/emails', icon: Mail },
      { label: 'Settings', path: '/admin/settings', icon: Settings },
    ],
    []
  );

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      // ignore and force local cleanup
    } finally {
      localStorage.removeItem('user');
      localStorage.removeItem('userType');
      localStorage.removeItem('userRole');
      localStorage.removeItem('userId');
      localStorage.removeItem('authToken');
      navigate('/login');
    }
  };

  return (
    <div className="min-h-screen">
      <Sidebar items={menuItems} collapsed={collapsed} onToggle={() => setCollapsed((value) => !value)} />
      <Header
        collapsed={collapsed}
        searchValue={search}
        onSearchChange={setSearch}
        userName={user?.full_name || user?.username || 'Admin'}
        userRole="Administrator"
        onLogout={handleLogout}
      />
      <main
        className={`pt-20 pb-8 px-4 sm:px-6 transition-all duration-300 ${
          collapsed ? 'ml-[84px]' : 'ml-72'
        }`}
      >
        <Outlet />
      </main>
    </div>
  );
};

export default AdminLayout;

