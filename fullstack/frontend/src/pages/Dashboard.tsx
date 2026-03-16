/**
 * Component: pages\Dashboard.tsx
 * Purpose: Defines UI structure and behavior for this view/component.
 */
import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import { Building2, CalendarCheck, DollarSign, Users, RefreshCw } from 'lucide-react';
import StatCard from '@/components/StatCard';
import { employeeAPI, payslipAPI, dashboardAPI } from '@/services/api';
import { getJson, hrmsApi } from '@/services/hrmsApi';

// Import new dashboard components
import WelcomeHero from '@/components/dashboard/WelcomeHero';
import QuickActionCards from '@/components/dashboard/QuickActionCards';
import DashboardWidgets from '@/components/dashboard/DashboardWidgets';
import ActivityFeed from '@/components/dashboard/ActivityFeed';
import FooterHelp from '@/components/dashboard/FooterHelp';

interface AnalyticsStats {
  totalEmployees: number;
  presentToday: number;
  onLeaveToday: number;
  totalPayroll: number;
}

interface PayrollPoint {
  label: string;
  value: number;
}

interface AttendancePoint {
  date: string;
  present: number;
  absent: number;
}

interface DepartmentPoint {
  name: string;
  value: number;
}

interface ActivityItem {
  id: string;
  text: string;
  time: string;
}

const palette = ['#F5A623', '#2F2F2F', '#3B82F6', '#60A5FA', '#93C5FD'];

const normalizeList = <T,>(payload: any): T[] => {
  if (Array.isArray(payload)) {
    return payload;
  }
  if (Array.isArray(payload?.results)) {
    return payload.results;
  }
  if (Array.isArray(payload?.data)) {
    return payload.data;
  }
  return [];
};

interface ChartViewportProps {
  children: React.ReactNode;
}

const ChartViewport: React.FC<ChartViewportProps> = ({ children }) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const element = containerRef.current;
    if (!element) {
      return;
    }

    const update = () => {
      setReady(element.clientWidth > 0 && element.clientHeight > 0);
    };

    update();
    const observer = new ResizeObserver(update);
    observer.observe(element);

    return () => observer.disconnect();
  }, []);

  return (
    <div ref={containerRef} className="h-72 min-w-0">
      {ready ? children : <div className="h-full w-full" />}
    </div>
  );
};

const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<AnalyticsStats>({
    totalEmployees: 0,
    presentToday: 0,
    onLeaveToday: 0,
    totalPayroll: 0,
  });
  const [payrollTrend, setPayrollTrend] = useState<PayrollPoint[]>([]);
  const [attendance, setAttendance] = useState<AttendancePoint[]>([]);
  const [departments, setDepartments] = useState<DepartmentPoint[]>([]);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);

      const [employeesResponse, overviewResponse, attendanceResponse, payrollResponse, payslipsResponse] =
        await Promise.all([
          employeeAPI.getAll(),
          hrmsApi.getAnalyticsOverview(),
          hrmsApi.getAnalyticsAttendance(),
          hrmsApi.getAnalyticsPayroll(),
          payslipAPI.getAll(),
        ]);

      const employees = normalizeList<any>(employeesResponse.data);
      const overviewData = overviewResponse.ok
        ? await getJson<{ stats?: any; overview?: any }>(overviewResponse)
        : {};
      const attendanceData = attendanceResponse.ok
        ? await getJson<{ graph_data?: AttendancePoint[]; attendance?: AttendancePoint[] }>(
            attendanceResponse
          )
        : {};
      const payrollData = payrollResponse.ok
        ? await getJson<{ distribution?: { department: string; payroll: number }[] }>(payrollResponse)
        : {};
      const payslips = normalizeList<any>(payslipsResponse.data);

      const departmentMap: Record<string, number> = {};
      for (const employee of employees) {
        const department = employee?.department?.department_name || employee?.department_name || 'Unassigned';
        departmentMap[department] = (departmentMap[department] || 0) + 1;
      }

      const departmentPoints = Object.entries(departmentMap).map(([name, value]) => ({
        name,
        value,
      }));
      setDepartments(departmentPoints);

      const attendancePoints = (
        attendanceData.graph_data ||
        attendanceData.attendance ||
        []
      ).slice(-7);
      setAttendance(attendancePoints);

      const monthlyMap: Record<string, number> = {};
      for (const payslip of payslips) {
        const month = payslip?.pay_period_month || payslip?.month;
        const year = payslip?.pay_period_year || payslip?.year;
        const netPay = Number(payslip?.net_pay || payslip?.net_salary || 0);
        if (!month || !year) continue;
        const key = `${month} ${year}`;
        monthlyMap[key] = (monthlyMap[key] || 0) + netPay;
      }

      let trend = Object.entries(monthlyMap).map(([label, value]) => ({ label, value }));
      trend = trend.slice(-6);

      const currentPayroll =
        Number(overviewData?.stats?.total_payroll || overviewData?.overview?.total_payroll || 0) ||
        (payrollData.distribution || []).reduce((sum, item) => sum + Number(item.payroll || 0), 0);

      if (trend.length === 0) {
        const now = new Date();
        trend = Array.from({ length: 6 }, (_, index) => {
          const d = new Date(now.getFullYear(), now.getMonth() - (5 - index), 1);
          return {
            label: d.toLocaleString('en-US', { month: 'short' }),
            value: Math.max(currentPayroll * (0.85 + index * 0.03), 0),
          };
        });
      }
      setPayrollTrend(trend);

      setStats({
        totalEmployees: Number(
          overviewData?.stats?.total_employees ||
            overviewData?.overview?.total_employees ||
            employees.length
        ),
        presentToday: Number(
          overviewData?.stats?.present_today ||
            overviewData?.overview?.present_today ||
            attendancePoints[attendancePoints.length - 1]?.present ||
            0
        ),
        onLeaveToday: Number(
          overviewData?.stats?.on_leave_today ||
            overviewData?.overview?.on_leave_today ||
            0
        ),
        totalPayroll: currentPayroll,
      });

      setActivity([
        { id: '1', text: 'Payslip generated for 12 employees', time: '10 minutes ago' },
        { id: '2', text: 'Leave approved for Saketh', time: '32 minutes ago' },
        { id: '3', text: 'New employee joined', time: '1 hour ago' },
        { id: '4', text: 'Document uploaded', time: '2 hours ago' },
      ]);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = useMemo(
    () => [
      {
        title: 'Total Employees',
        value: stats.totalEmployees,
        icon: Users,
        color: 'primary' as const,
      },
      {
        title: 'Employees Present Today',
        value: stats.presentToday,
        icon: CalendarCheck,
        color: 'success' as const,
      },
      {
        title: 'Employees On Leave',
        value: stats.onLeaveToday,
        icon: Building2,
        color: 'warning' as const,
      },
      {
        title: 'Total Payroll This Month',
        value: `Rs ${Math.round(stats.totalPayroll).toLocaleString('en-IN')}`,
        icon: DollarSign,
        color: 'accent' as const,
      },
    ],
    [stats]
  );

  return (
    <div className="space-y-6">
      {/* Welcome Hero Section with Quick Stats */}
      <WelcomeHero />

      {/* Quick Action Cards */}
      <QuickActionCards />

      {/* Dashboard Widgets */}
      <DashboardWidgets />

      {/* Charts Section */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-md border border-gray-100 xl:col-span-2 min-w-0">
          <div className="px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-white">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Payroll Cost Trend</h2>
              <button
                onClick={() => void loadDashboard()}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                title="Refresh"
              >
                <RefreshCw className={`h-4 w-4 text-gray-500 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
          <div className="p-6">
            {loading ? (
              <div className="h-72 flex items-center justify-center text-gray-500">Loading...</div>
            ) : (
              <ChartViewport>
                <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                  <LineChart data={payrollTrend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                    <XAxis dataKey="label" />
                    <YAxis tickFormatter={(value) => `${Math.round(value / 1000)}k`} />
                    <Tooltip formatter={(value: number) => `Rs ${Math.round(Number(value)).toLocaleString('en-IN')}`} />
                    <Line type="monotone" dataKey="value" stroke="#F5A623" strokeWidth={2.5} dot={{ fill: '#F5A623' }} />
                  </LineChart>
                </ResponsiveContainer>
              </ChartViewport>
            )}
          </div>
        </div>

        {/* Activity Feed - Real data from API */}
        <ActivityFeed />
      </div>

      {/* Additional Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-md border border-gray-100 min-w-0">
          <div className="px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-white">
            <h2 className="text-lg font-semibold text-gray-900">Attendance Overview</h2>
          </div>
          <div className="p-6">
            {loading ? (
              <div className="h-72 flex items-center justify-center text-gray-500">Loading...</div>
            ) : (
              <ChartViewport>
                <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                  <BarChart data={attendance}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                    <XAxis dataKey="date" tickFormatter={(value) => value.slice(5)} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="present" fill="#F5A623" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="absent" fill="#94A3B8" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartViewport>
            )}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md border border-gray-100 min-w-0">
          <div className="px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-white">
            <h2 className="text-lg font-semibold text-gray-900">Department Distribution</h2>
          </div>
          <div className="p-6">
            {loading ? (
              <div className="h-72 flex items-center justify-center text-gray-500">Loading...</div>
            ) : (
              <ChartViewport>
                <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                  <PieChart>
                    <Pie data={departments} dataKey="value" nameKey="name" outerRadius={95} label>
                      {departments.map((entry, index) => (
                        <Cell key={entry.name} fill={palette[index % palette.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </ChartViewport>
            )}
          </div>
        </div>
      </div>

      {/* Stat Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {statCards.map((card) => (
          <StatCard
            key={card.title}
            title={card.title}
            value={card.value}
            icon={card.icon}
            color={card.color}
          />
        ))}
      </div>

      {/* Footer Help Section */}
      <FooterHelp />
    </div>
  );
};

export default DashboardPage;


