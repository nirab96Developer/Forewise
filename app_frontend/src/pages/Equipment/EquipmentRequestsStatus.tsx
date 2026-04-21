
// src/pages/Equipment/EquipmentRequestsStatus.tsx
import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle, XCircle, AlertTriangle, Calendar, User } from 'lucide-react';
import api from '../../services/api';
import { getEquipmentRequestStatusLabel } from '../../strings';

interface EquipmentRequest {
  id: number;
  equipment_type: string;
  project_name: string;
  requester: string;
  start_date: string;
  end_date: string;
  status: string;
  priority: string;
  description: string;
  created_at: string;
}

const EquipmentRequestsStatus: React.FC = () => {
  const [requests, setRequests] = useState<EquipmentRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('all');

  useEffect(() => {
    fetchRequests();
  }, [filterStatus]);

  const fetchRequests = async () => {
    try {
      setLoading(true);
      // Use work-orders endpoint - equipment requests are work orders with equipment
      const response = await api.get('/work-orders', {
        params: {
          page: 1,
          page_size: 100,
          ...(filterStatus !== 'all' ? { status: filterStatus } : {})
        }
      });
      // Work orders API returns { items: [], total, page, ... }
      const requestsList = response.data.items || response.data.work_orders || [];
      
      // Transform API response to component format
      const transformed: EquipmentRequest[] = requestsList.map((req: any) => ({
        id: req.id,
        equipment_type: req.equipment_type_name || req.equipment_type || 'ללא ציוד',
        project_name: req.project_name || 'ללא פרויקט',
        requester: req.requester_name || req.created_by_name || 'ללא מבקש',
        start_date: req.start_date ? req.start_date.split('T')[0] : (req.requested_date ? req.requested_date.split('T')[0] : ''),
        end_date: req.end_date ? req.end_date.split('T')[0] : '',
        status: req.status || 'pending',
        priority: req.priority || 'medium',
        description: req.description || req.notes || 'ללא תיאור',
        created_at: req.created_at ? new Date(req.created_at).toLocaleString('he-IL') : new Date().toLocaleString('he-IL')
      }));
      
      setRequests(transformed);
    } catch (error) {
      console.error('Error fetching requests:', error);
      setRequests([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredRequests = requests.filter(request => 
    filterStatus === 'all' || request.status === filterStatus
  );

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'rejected':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'pending':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      default:
        return <AlertTriangle className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    const upper = (status || '').toUpperCase();
    if (upper === 'APPROVED') return 'bg-green-100 text-green-800';
    if (upper === 'REJECTED') return 'bg-red-100 text-red-800';
    if (upper === 'PENDING')  return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
  };
  const getStatusText = (status: string) => getEquipmentRequestStatusLabel(status);

  const getPriorityColor = (priority: string) => {
    const upper = (priority || '').toUpperCase();
    if (upper === 'URGENT') return 'bg-red-100 text-red-800';
    if (upper === 'HIGH')   return 'bg-orange-100 text-orange-800';
    if (upper === 'MEDIUM') return 'bg-yellow-100 text-yellow-800';
    if (upper === 'LOW')    return 'bg-green-100 text-green-800';
    return 'bg-gray-100 text-gray-800';
  };

  const getPriorityText = (priority: string) => {
    switch ((priority || '').toLowerCase()) {
      case 'urgent':
        return 'דחופה';
      case 'high':
        return 'גבוהה';
      case 'medium':
        return 'בינונית';
      case 'low':
        return 'נמוכה';
      default:
        return priority;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">טוען הזמנות ציוד...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">סטטוס הזמנות ציוד</h1>
          
          {/* Filter */}
          <div className="flex gap-4">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="pr-4 pl-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fw-green focus:border-transparent"
            >
              <option value="all">כל הסטטוסים</option>
              <option value="pending">ממתין לאישור</option>
              <option value="approved">אושר</option>
              <option value="rejected">נדחה</option>
            </select>
          </div>
        </div>

        {/* Requests Table */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ציוד
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    פרויקט
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    מבקש
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    תאריכים
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    עדיפות
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    סטטוס
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    פעולות
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredRequests.map((request) => (
                  <tr key={request.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {getStatusIcon(request.status)}
                        <div className="mr-3">
                          <div className="text-sm font-medium text-gray-900">{request.equipment_type}</div>
                          <div className="text-sm text-gray-500">{request.description}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{request.project_name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <User className="w-4 h-4 text-gray-500 ml-2" />
                        <div className="text-sm text-gray-900">{request.requester}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <Calendar className="w-4 h-4 text-gray-500 ml-2" />
                        <div className="text-sm text-gray-900">
                          {request.start_date} - {request.end_date}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(request.priority)}`}>
                        {getPriorityText(request.priority)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                        {getStatusText(request.status)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2 space-x-reverse">
                        <button className="text-blue-600 hover:text-blue-900" onClick={() => window.location.href = `/equipment/${request.id}`}>צפייה</button>
                        {request.status === 'pending' && (
                          <>
                            <button className="text-green-600 hover:text-green-900" onClick={async () => { try { await api.patch(`/equipment/${request.id}`, { status: 'approved' }); fetchRequests(); } catch { (window as any).showToast?.('שגיאה באישור', 'error'); } }}>אישור</button>
                            <button className="text-red-600 hover:text-red-900" onClick={async () => { try { await api.patch(`/equipment/${request.id}`, { status: 'rejected' }); fetchRequests(); } catch { (window as any).showToast?.('שגיאה בדחייה', 'error'); } }}>דחייה</button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {filteredRequests.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">לא נמצאו הזמנות ציוד</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default EquipmentRequestsStatus;
