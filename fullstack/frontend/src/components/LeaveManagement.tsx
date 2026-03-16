/**
 * Component: components\LeaveManagement.tsx
 * Purpose: Defines UI structure and behavior for this view/component.
 */
import React, { useEffect, useState } from 'react';
import { format, parseISO } from 'date-fns';
import { CheckCircle, XCircle, Clock, Plus } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { getJson, hrmsApi } from '@/services/hrmsApi';

interface LeaveRequest {
  id: number;
  leave_type: string;
  start_date: string;
  end_date: string;
  number_of_days: number;
  reason: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'CANCELLED';
  created_at: string;
}

interface LeaveType {
  id: number;
  name: string;
  max_days_per_year: number;
}

const LeaveManagement: React.FC = () => {
  const [leaveRequests, setLeaveRequests] = useState<LeaveRequest[]>([]);
  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  
  const [formData, setFormData] = useState({
    leave_type_id: '',
    start_date: '',
    end_date: '',
    reason: '',
  });

  useEffect(() => {
    loadLeaveData();
  }, []);

  const loadLeaveData = async () => {
    try {
      setLoading(true);
      setError('');
      const [requestsRes, typesRes] = await Promise.all([hrmsApi.getLeaveRequests(), hrmsApi.getLeaveTypes()]);

      if (requestsRes.ok) {
        const data = await getJson<{ leave_requests?: LeaveRequest[] }>(requestsRes);
        setLeaveRequests(data.leave_requests || []);
      } else {
        setError('Failed to load leave requests');
      }

      if (typesRes.ok) {
        const data = await getJson<{ leave_types?: LeaveType[] }>(typesRes);
        setLeaveTypes(data.leave_types || []);
      } else {
        setError('Failed to load leave types');
      }
    } catch (err) {
      setError('Failed to load leave data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const formPayload = new FormData();
      formPayload.append('leave_type_id', formData.leave_type_id);
      formPayload.append('start_date', formData.start_date);
      formPayload.append('end_date', formData.end_date);
      formPayload.append('reason', formData.reason);

      const res = await hrmsApi.applyLeave(formPayload);
      const data = await getJson<{ success?: boolean; message?: string }>(res);

      if (res.ok && data.success !== false) {
        setSuccess('Leave request submitted successfully');
        setFormData({ leave_type_id: '', start_date: '', end_date: '', reason: '' });
        setShowForm(false);
        loadLeaveData();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        setError(data.message || 'Failed to apply leave');
      }
    } catch (err) {
      setError('An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'REJECTED':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'PENDING':
        return <Clock className="w-5 h-5 text-yellow-600" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    const statusClasses = {
      APPROVED: 'bg-green-100 text-green-800',
      REJECTED: 'bg-red-100 text-red-800',
      PENDING: 'bg-yellow-100 text-yellow-800',
      CANCELLED: 'bg-gray-100 text-gray-800',
    };
    return statusClasses[status as keyof typeof statusClasses] || 'bg-gray-100 text-gray-800';
  };

  const filteredRequests = filterStatus === 'ALL' 
    ? leaveRequests 
    : leaveRequests.filter(lr => lr.status === filterStatus);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Leave Management</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-5 h-5" />
          Apply for Leave
        </button>
      </div>

      {/* Alerts */}
      {error && <Alert className="bg-red-50 border-red-200"><AlertDescription className="text-red-700">{error}</AlertDescription></Alert>}
      {success && <Alert className="bg-green-50 border-green-200"><AlertDescription className="text-green-700">{success}</AlertDescription></Alert>}

      {/* Apply Leave Form */}
      {showForm && (
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow">
          <h3 className="text-lg font-semibold mb-4">Apply for Leave</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Leave Type *</label>
                <select
                  value={formData.leave_type_id}
                  onChange={(e) => setFormData({ ...formData, leave_type_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  <option value="">Select Leave Type</option>
                  {leaveTypes.map(lt => (
                    <option key={lt.id} value={lt.id}>{lt.name} ({lt.max_days_per_year} days)</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Number of Days</label>
                <div className="px-3 py-2 bg-gray-100 rounded-lg text-gray-700">
                  {formData.start_date && formData.end_date
                    ? (new Date(formData.end_date).getTime() - new Date(formData.start_date).getTime()) / (1000 * 60 * 60 * 24) + 1
                    : 0} days
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Start Date *</label>
                <input
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">End Date *</label>
                <input
                  type="date"
                  value={formData.end_date}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Reason *</label>
              <textarea
                value={formData.reason}
                onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={3}
                placeholder="Enter reason for leave..."
                required
              />
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Submitting...' : 'Submit Request'}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Filter */}
      <div className="flex gap-2">
        {['ALL', 'PENDING', 'APPROVED', 'REJECTED'].map(status => (
          <button
            key={status}
            onClick={() => setFilterStatus(status)}
            className={`px-4 py-2 rounded-lg font-medium ${
              filterStatus === status
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {status}
          </button>
        ))}
      </div>

      {/* Leave Requests List */}
      <div className="space-y-3">
        {filteredRequests.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No leave requests found
          </div>
        ) : (
          filteredRequests.map(lr => (
            <div key={lr.id} className="bg-white p-4 rounded-lg border border-gray-200 hover:border-blue-300 transition">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    {getStatusIcon(lr.status)}
                    <h4 className="font-semibold text-gray-900">{lr.leave_type}</h4>
                    <span className={`px-2 py-1 rounded text-sm font-medium ${getStatusBadge(lr.status)}`}>
                      {lr.status}
                    </span>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-2">
                    {format(parseISO(lr.start_date), 'MMM dd, yyyy')} - {format(parseISO(lr.end_date), 'MMM dd, yyyy')} ({lr.number_of_days} days)
                  </p>
                  
                  <p className="text-sm text-gray-700">{lr.reason}</p>
                  <p className="text-xs text-gray-500 mt-2">Applied on {format(parseISO(lr.created_at), 'MMM dd, yyyy HH:mm')}</p>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default LeaveManagement;

