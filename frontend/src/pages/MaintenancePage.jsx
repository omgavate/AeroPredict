import React, { useState } from 'react';
import {
  Wrench,
  Plus,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileText,
  Calendar,
  Filter,
  CheckCircle
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import { MOCK_AIRCRAFT, MOCK_MAINTENANCE_RECORDS } from '../data/mockData';

export default function MaintenancePage() {
  const [records, setRecords] = useState(MOCK_MAINTENANCE_RECORDS);
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [showAddForm, setShowAddForm] = useState(false);
  const [notification, setNotification] = useState(null);

  // New Work Order Form State
  const [newOrder, setNewOrder] = useState({
    aircraft_id: '1',
    title: '',
    description: '',
    priority: 'HIGH',
    scheduled_date: new Date().toISOString().split('T')[0],
    technician_notes: ''
  });

  const filteredRecords = records.filter(r =>
    filterStatus === 'ALL' ? true : r.status === filterStatus
  );

  const handleStatusChange = (id, newStatus) => {
    setRecords(prev =>
      prev.map(r => {
        if (r.id === id) {
          return {
            ...r,
            status: newStatus,
            completed_date: newStatus === 'COMPLETED' ? new Date().toISOString().split('T')[0] : r.completed_date
          };
        }
        return r;
      })
    );
    setNotification(`Work order status updated to ${newStatus}.`);
    setTimeout(() => setNotification(null), 3000);
  };

  const handleCreateOrder = (e) => {
    e.preventDefault();
    if (!newOrder.title.trim()) {
      alert('Work order title is required.');
      return;
    }

    const selectedAircraft = MOCK_AIRCRAFT.find(a => a.id === parseInt(newOrder.aircraft_id, 10)) || MOCK_AIRCRAFT[0];

    const createdRecord = {
      id: records.length + 1,
      aircraft_id: selectedAircraft.id,
      tail_number: selectedAircraft.tail_number,
      title: newOrder.title,
      description: newOrder.description,
      priority: newOrder.priority,
      status: 'SCHEDULED',
      scheduled_date: newOrder.scheduled_date,
      completed_date: null,
      technician_notes: newOrder.technician_notes || 'Assigned to Powerplant maintenance depot.'
    };

    setRecords([createdRecord, ...records]);
    setShowAddForm(false);
    setNewOrder({
      aircraft_id: '1',
      title: '',
      description: '',
      priority: 'HIGH',
      scheduled_date: new Date().toISOString().split('T')[0],
      technician_notes: ''
    });

    setNotification(`Work order #${createdRecord.id} created for aircraft ${selectedAircraft.tail_number}.`);
    setTimeout(() => setNotification(null), 3500);
  };

  return (
    <div>
      <div className="demo-banner">
        <span>✈️ <strong>Module 5:</strong> Maintenance Work Order Lifecycle & History</span>
        <span className="badge bg-white text-primary">Active Work Orders: {records.filter(r => r.status !== 'COMPLETED').length}</span>
      </div>

      {notification && (
        <div className="alert alert-success d-flex align-items-center gap-2 py-2 mb-3">
          <CheckCircle size={16} />
          <span>{notification}</span>
        </div>
      )}

      {/* Header */}
      <div className="d-flex align-items-center justify-content-between mb-4 flex-wrap gap-2">
        <div>
          <h4 className="fw-bold text-dark mb-1">Maintenance Management</h4>
          <p className="text-secondary small mb-0">
            Create work orders, track scheduled shop visits, update technician findings and review historical logs.
          </p>
        </div>

        <button
          className="btn btn-primary d-inline-flex align-items-center gap-2"
          onClick={() => setShowAddForm(!showAddForm)}
        >
          <Plus size={16} />
          <span>{showAddForm ? 'Cancel Work Order' : 'Create Work Order'}</span>
        </button>
      </div>

      {/* Add Work Order Form Modal / Panel */}
      {showAddForm && (
        <div className="aerocard mb-4 border-primary">
          <h6 className="fw-bold text-primary mb-3 pb-2 border-bottom">
            Schedule New Maintenance Work Order
          </h6>
          <form onSubmit={handleCreateOrder}>
            <div className="row g-3">
              <div className="col-12 col-md-4">
                <label className="form-label small fw-semibold">Target Aircraft</label>
                <select
                  className="form-select"
                  value={newOrder.aircraft_id}
                  onChange={e => setNewOrder({ ...newOrder, aircraft_id: e.target.value })}
                >
                  {MOCK_AIRCRAFT.map(a => (
                    <option key={a.id} value={a.id}>
                      {a.tail_number} ({a.model})
                    </option>
                  ))}
                </select>
              </div>

              <div className="col-12 col-md-4">
                <label className="form-label small fw-semibold">Work Order Title <span className="text-danger">*</span></label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. HPC Stage 4 Borescope & Blade Dressing"
                  value={newOrder.title}
                  onChange={e => setNewOrder({ ...newOrder, title: e.target.value })}
                />
              </div>

              <div className="col-12 col-md-4">
                <label className="form-label small fw-semibold">Priority Level</label>
                <select
                  className="form-select"
                  value={newOrder.priority}
                  onChange={e => setNewOrder({ ...newOrder, priority: e.target.value })}
                >
                  <option value="LOW">LOW - Routine Servicing</option>
                  <option value="MEDIUM">MEDIUM - Standard Check</option>
                  <option value="HIGH">HIGH - Urgent Inspection</option>
                  <option value="CRITICAL">CRITICAL - Aircraft Grounded</option>
                </select>
              </div>

              <div className="col-12 col-md-4">
                <label className="form-label small fw-semibold">Scheduled Date</label>
                <input
                  type="date"
                  className="form-control"
                  value={newOrder.scheduled_date}
                  onChange={e => setNewOrder({ ...newOrder, scheduled_date: e.target.value })}
                />
              </div>

              <div className="col-12 col-md-8">
                <label className="form-label small fw-semibold">Work Order Description</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Specific tasks, tooling requirements or component replacement..."
                  value={newOrder.description}
                  onChange={e => setNewOrder({ ...newOrder, description: e.target.value })}
                />
              </div>

              <div className="col-12 text-end pt-2">
                <button type="submit" className="btn btn-primary">
                  Save & Dispatch Work Order
                </button>
              </div>
            </div>
          </form>
        </div>
      )}

      {/* Filter Bar */}
      <div className="aerocard mb-4 p-3">
        <div className="d-flex align-items-center justify-content-between flex-wrap gap-2">
          <div className="d-flex align-items-center gap-2">
            <span className="small text-secondary fw-semibold">Filter Status:</span>
            <div className="btn-group btn-group-sm" role="group">
              <button
                type="button"
                className={`btn ${filterStatus === 'ALL' ? 'btn-primary' : 'btn-outline-secondary'}`}
                onClick={() => setFilterStatus('ALL')}
              >
                All ({records.length})
              </button>
              <button
                type="button"
                className={`btn ${filterStatus === 'SCHEDULED' ? 'btn-primary' : 'btn-outline-secondary'}`}
                onClick={() => setFilterStatus('SCHEDULED')}
              >
                Scheduled
              </button>
              <button
                type="button"
                className={`btn ${filterStatus === 'IN_PROGRESS' ? 'btn-primary' : 'btn-outline-secondary'}`}
                onClick={() => setFilterStatus('IN_PROGRESS')}
              >
                In Progress
              </button>
              <button
                type="button"
                className={`btn ${filterStatus === 'COMPLETED' ? 'btn-primary' : 'btn-outline-secondary'}`}
                onClick={() => setFilterStatus('COMPLETED')}
              >
                Completed
              </button>
            </div>
          </div>

          <div className="small text-muted">
            Displaying {filteredRecords.length} records
          </div>
        </div>
      </div>

      {/* Work Orders List */}
      <div className="aerocard p-0 overflow-hidden">
        <div className="table-responsive">
          <table className="aero-table mb-0">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Aircraft</th>
                <th>Maintenance Title & Scope</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Scheduled Date</th>
                <th>Completed</th>
                <th className="text-end">Status Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredRecords.length === 0 ? (
                <tr>
                  <td colSpan="8" className="text-center py-5 text-muted">
                    No maintenance records found for the selected status.
                  </td>
                </tr>
              ) : (
                filteredRecords.map(order => {
                  const isCritical = order.priority === 'CRITICAL';
                  const isHigh = order.priority === 'HIGH';

                  return (
                    <tr key={order.id}>
                      <td className="fw-mono text-muted small">#{order.id}</td>
                      <td>
                        <div className="fw-bold text-dark">{order.tail_number}</div>
                      </td>
                      <td>
                        <div className="fw-semibold text-dark">{order.title}</div>
                        <div className="text-secondary small">{order.description}</div>
                        {order.technician_notes && (
                          <div className="text-muted small mt-1" style={{ fontSize: '0.74rem' }}>
                            <strong>Tech Log:</strong> {order.technician_notes}
                          </div>
                        )}
                      </td>
                      <td>
                        <span
                          className="badge rounded-pill"
                          style={{
                            backgroundColor: isCritical ? '#FEE2E2' : isHigh ? '#FFEDD5' : '#F1F5F9',
                            color: isCritical ? '#991B1B' : isHigh ? '#9A3412' : '#334155'
                          }}
                        >
                          {order.priority}
                        </span>
                      </td>
                      <td>
                        <span
                          className={`badge ${
                            order.status === 'COMPLETED'
                              ? 'bg-success'
                              : order.status === 'IN_PROGRESS'
                              ? 'bg-primary'
                              : 'bg-warning text-dark'
                          }`}
                        >
                          {order.status}
                        </span>
                      </td>
                      <td className="small text-secondary">{order.scheduled_date}</td>
                      <td className="small text-secondary">
                        {order.completed_date || '—'}
                      </td>
                      <td className="text-end">
                        <select
                          className="form-select form-select-sm d-inline-block"
                          style={{ width: 130, fontSize: '0.78rem' }}
                          value={order.status}
                          onChange={e => handleStatusChange(order.id, e.target.value)}
                        >
                          <option value="SCHEDULED">Scheduled</option>
                          <option value="IN_PROGRESS">In Progress</option>
                          <option value="COMPLETED">Completed</option>
                          <option value="CANCELLED">Cancelled</option>
                        </select>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
