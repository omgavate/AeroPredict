import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Wrench,
  Plus,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileText,
  Calendar,
  Filter,
  CheckCircle,
  Trash2,
  Edit3,
  Eye,
  RefreshCw,
  Search,
  Database,
  AlertTriangle,
  X,
  Plane,
  Save
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import maintenanceApi from '../api/maintenanceApi';
import aircraftApi from '../api/aircraftApi';

export default function MaintenancePage() {
  const [searchParams] = useSearchParams();
  const preselectedAircraftId = searchParams.get('aircraft_id');

  // Data states
  const [records, setRecords] = useState([]);
  const [fleet, setFleet] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLive, setIsLive] = useState(false);

  // Filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [filterPriority, setFilterPriority] = useState('ALL');
  const [filterAircraft, setFilterAircraft] = useState(preselectedAircraftId || 'ALL');

  // UI modal / form states
  const [showAddForm, setShowAddForm] = useState(Boolean(preselectedAircraftId));
  const [editingRecord, setEditingRecord] = useState(null);
  const [viewingRecord, setViewingRecord] = useState(null);

  // Notifications and validation errors
  const [notification, setNotification] = useState(null);
  const [formErrors, setFormErrors] = useState({});
  const [actionLoading, setActionLoading] = useState(false);

  // New Work Order Form State
  const [newOrder, setNewOrder] = useState({
    aircraft_id: preselectedAircraftId || '1',
    title: '',
    description: '',
    priority: 'HIGH',
    status: 'PENDING',
    scheduled_date: new Date().toISOString().split('T')[0],
    technician_notes: ''
  });

  // --------------------------------------------------------------------------
  // 1. Fetch Fleet and Work Orders from Backend
  // --------------------------------------------------------------------------
  const loadData = async () => {
    setIsLoading(true);
    try {
      const [fleetRes, maintRes] = await Promise.all([
        aircraftApi.getAll(),
        maintenanceApi.getAll({
          aircraft_id: filterAircraft !== 'ALL' ? filterAircraft : null,
          status: filterStatus !== 'ALL' ? filterStatus : null,
          priority: filterPriority !== 'ALL' ? filterPriority : null,
          search: searchTerm
        })
      ]);

      if (fleetRes.success && fleetRes.data) {
        setFleet(fleetRes.data);
      }

      if (maintRes.success && maintRes.data) {
        setRecords(maintRes.data);
        setIsLive(maintRes.isLive);
      }
    } catch (err) {
      console.warn('Error fetching maintenance records:', err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      loadData();
    }, 200);
    return () => clearTimeout(timer);
  }, [searchTerm, filterStatus, filterPriority, filterAircraft]);

  // --------------------------------------------------------------------------
  // 2. Quick Status Change Handler
  // --------------------------------------------------------------------------
  const handleQuickStatusChange = async (id, newStatus) => {
    try {
      const res = await maintenanceApi.update(id, { status: newStatus });
      if (res.success) {
        setRecords(prev =>
          prev.map(r => (r.id === id ? res.data : r))
        );
        setNotification(`Work order #${id} status updated to ${newStatus}.`);
        setTimeout(() => setNotification(null), 3000);
      } else {
        alert('Failed to update status: ' + (res.error || 'Server error'));
      }
    } catch (err) {
      alert('Error updating status: ' + err.message);
    }
  };

  // --------------------------------------------------------------------------
  // 3. Create Work Order Handler (Task 2 & 6)
  // --------------------------------------------------------------------------
  const handleCreateOrder = async (e) => {
    e.preventDefault();
    setFormErrors({});

    // Client-side quick check
    if (!newOrder.title.trim()) {
      setFormErrors({ title: 'Work order title / issue description is required.' });
      return;
    }

    setActionLoading(true);
    try {
      const res = await maintenanceApi.create(newOrder);
      if (res.success && res.data) {
        setRecords([res.data, ...records]);
        setShowAddForm(false);
        setNewOrder({
          aircraft_id: fleet[0]?.id ? String(fleet[0].id) : '1',
          title: '',
          description: '',
          priority: 'HIGH',
          status: 'PENDING',
          scheduled_date: new Date().toISOString().split('T')[0],
          technician_notes: ''
        });
        setNotification(`Work order #${res.data.id} created successfully.`);
        setTimeout(() => setNotification(null), 3500);
      } else {
        if (res.details) {
          setFormErrors(res.details);
        } else {
          alert('Failed to create work order: ' + (res.error || 'Unknown error'));
        }
      }
    } catch (err) {
      alert('Error communicating with maintenance service: ' + err.message);
    } finally {
      setActionLoading(false);
    }
  };

  // --------------------------------------------------------------------------
  // 4. Update Work Order Handler (Task 2 & 6)
  // --------------------------------------------------------------------------
  const handleUpdateOrder = async (e) => {
    e.preventDefault();
    if (!editingRecord) return;

    setFormErrors({});
    setActionLoading(true);
    try {
      const res = await maintenanceApi.update(editingRecord.id, editingRecord);
      if (res.success && res.data) {
        setRecords(prev =>
          prev.map(r => (r.id === editingRecord.id ? res.data : r))
        );
        setEditingRecord(null);
        setNotification(`Work order #${res.data.id} updated successfully.`);
        setTimeout(() => setNotification(null), 3500);
      } else {
        if (res.details) {
          setFormErrors(res.details);
        } else {
          alert('Failed to update work order: ' + (res.error || 'Unknown error'));
        }
      }
    } catch (err) {
      alert('Error updating work order: ' + err.message);
    } finally {
      setActionLoading(false);
    }
  };

  // --------------------------------------------------------------------------
  // 5. Delete Work Order Handler (Task 2)
  // --------------------------------------------------------------------------
  const handleDeleteOrder = async (id, title) => {
    if (window.confirm(`Are you sure you want to permanently delete maintenance record #${id} ("${title}")?`)) {
      try {
        const res = await maintenanceApi.delete(id);
        if (res.success) {
          setRecords(prev => prev.filter(r => r.id !== id));
          setNotification(`Work order #${id} deleted.`);
          setTimeout(() => setNotification(null), 3500);
        } else {
          alert('Failed to delete work order: ' + (res.error || 'Server error'));
        }
      } catch (err) {
        alert('Error deleting work order: ' + err.message);
      }
    }
  };

  // Quick summary counts
  const totalOrders = records.length;
  const pendingOrders = records.filter(r => r.status === 'PENDING' || r.status === 'SCHEDULED').length;
  const inProgressOrders = records.filter(r => r.status === 'IN_PROGRESS').length;
  const completedOrders = records.filter(r => r.status === 'COMPLETED').length;

  return (
    <div>
      {/* Toast Notification */}
      {notification && (
        <div className="alert alert-success d-flex align-items-center gap-2 py-2 mb-3">
          <CheckCircle size={16} />
          <span>{notification}</span>
        </div>
      )}

      {/* Header */}
      <div className="d-flex align-items-center justify-content-between mb-4 flex-wrap gap-2">
        <div>
          <div className="d-flex align-items-center gap-2">
            <h4 className="fw-bold text-dark mb-0">Maintenance Management</h4>
            {isLive && (
              <span className="badge bg-success-subtle text-success border border-success-subtle d-inline-flex align-items-center gap-1">
                <Database size={12} />
                <span>Database Synchronized</span>
              </span>
            )}
          </div>
          <p className="text-secondary small mb-0 mt-1">
            Create work orders, track scheduled shop visits, update technician findings and review historical logs.
          </p>
        </div>

        <button
          className="btn btn-primary d-inline-flex align-items-center gap-2"
          onClick={() => {
            setShowAddForm(!showAddForm);
            setEditingRecord(null);
          }}
        >
          {showAddForm ? <X size={16} /> : <Plus size={16} />}
          <span>{showAddForm ? 'Cancel Work Order' : 'Create Work Order'}</span>
        </button>
      </div>

      {/* Summary KPI Cards */}
      <div className="row g-3 mb-4">
        <div className="col-6 col-md-3">
          <div className="aerocard p-3 text-center">
            <div className="small text-secondary mb-1">Total Work Orders</div>
            <div className="h3 fw-bold text-dark mb-0 fw-mono">{totalOrders}</div>
            <span className="badge bg-light text-secondary border mt-1">Lifecycle Backlog</span>
          </div>
        </div>

        <div className="col-6 col-md-3">
          <div className="aerocard p-3 text-center">
            <div className="small text-secondary mb-1">Pending / Scheduled</div>
            <div className="h3 fw-bold text-warning-emphasis mb-0 fw-mono">{pendingOrders}</div>
            <span className="badge bg-warning-subtle text-warning-emphasis mt-1">Queue Awaiting Stand</span>
          </div>
        </div>

        <div className="col-6 col-md-3">
          <div className="aerocard p-3 text-center">
            <div className="small text-secondary mb-1">In Progress</div>
            <div className="h3 fw-bold text-primary mb-0 fw-mono">{inProgressOrders}</div>
            <span className="badge bg-primary-subtle text-primary mt-1">Active Hangar Bay</span>
          </div>
        </div>

        <div className="col-6 col-md-3">
          <div className="aerocard p-3 text-center">
            <div className="small text-secondary mb-1">Completed</div>
            <div className="h3 fw-bold text-success mb-0 fw-mono">{completedOrders}</div>
            <span className="badge bg-success-subtle text-success mt-1">Certified Airworthy</span>
          </div>
        </div>
      </div>

      {/* Add Work Order Form Modal / Panel (Task 4 & 6) */}
      {showAddForm && (
        <div className="aerocard mb-4 border-primary">
          <div className="d-flex justify-content-between align-items-center mb-3 pb-2 border-bottom">
            <h6 className="fw-bold text-primary mb-0 d-flex align-items-center gap-2">
              <Wrench size={18} />
              <span>Schedule New Maintenance Work Order</span>
            </h6>
            <button
              type="button"
              className="btn-close btn-sm"
              onClick={() => setShowAddForm(false)}
              aria-label="Close"
            />
          </div>

          <form onSubmit={handleCreateOrder}>
            <div className="row g-3">
              {/* Target Aircraft */}
              <div className="col-12 col-md-4">
                <label className="form-label small fw-semibold">Target Aircraft <span className="text-danger">*</span></label>
                <select
                  className={`form-select ${formErrors.aircraft_id ? 'is-invalid' : ''}`}
                  value={newOrder.aircraft_id}
                  onChange={e => setNewOrder({ ...newOrder, aircraft_id: e.target.value })}
                >
                  {fleet.map(a => (
                    <option key={a.id} value={a.id}>
                      {a.tail_number} ({a.model}) • Unit #{a.cmapss_unit_id || 'N/A'}
                    </option>
                  ))}
                </select>
                {formErrors.aircraft_id && <div className="invalid-feedback">{formErrors.aircraft_id}</div>}
              </div>

              {/* Work Order Title */}
              <div className="col-12 col-md-8">
                <label className="form-label small fw-semibold">Work Order Title / Issue <span className="text-danger">*</span></label>
                <input
                  type="text"
                  className={`form-control ${formErrors.title ? 'is-invalid' : ''}`}
                  placeholder="e.g. HPC Stage 4 Borescope & Thermal Blade Dressing"
                  value={newOrder.title}
                  onChange={e => setNewOrder({ ...newOrder, title: e.target.value })}
                />
                {formErrors.title && <div className="invalid-feedback">{formErrors.title}</div>}
              </div>

              {/* Priority */}
              <div className="col-12 col-md-4">
                <label className="form-label small fw-semibold">Priority Level</label>
                <select
                  className="form-select"
                  value={newOrder.priority}
                  onChange={e => setNewOrder({ ...newOrder, priority: e.target.value })}
                >
                  <option value="LOW">LOW - Routine Non-Critical</option>
                  <option value="MEDIUM">MEDIUM - Standard Inspection</option>
                  <option value="HIGH">HIGH - Urgent Priority</option>
                  <option value="CRITICAL">CRITICAL - AOG / Immediate Grounding</option>
                </select>
              </div>

              {/* Status */}
              <div className="col-12 col-md-4">
                <label className="form-label small fw-semibold">Initial Status</label>
                <select
                  className="form-select"
                  value={newOrder.status}
                  onChange={e => setNewOrder({ ...newOrder, status: e.target.value })}
                >
                  <option value="PENDING">PENDING - Scheduled in Queue</option>
                  <option value="IN_PROGRESS">IN_PROGRESS - Work Underway</option>
                  <option value="COMPLETED">COMPLETED - Certified Airworthy</option>
                </select>
              </div>

              {/* Scheduled Date */}
              <div className="col-12 col-md-4">
                <label className="form-label small fw-semibold">Scheduled Target Date <span className="text-danger">*</span></label>
                <input
                  type="date"
                  className={`form-control ${formErrors.scheduled_date ? 'is-invalid' : ''}`}
                  value={newOrder.scheduled_date}
                  onChange={e => setNewOrder({ ...newOrder, scheduled_date: e.target.value })}
                />
                {formErrors.scheduled_date && <div className="invalid-feedback">{formErrors.scheduled_date}</div>}
              </div>

              {/* Issue Description */}
              <div className="col-12">
                <label className="form-label small fw-semibold">Diagnostic & Issue Description</label>
                <textarea
                  className="form-control"
                  rows={2}
                  placeholder="Describe observed physical degradation markers, sensor divergences, or prescribed scope of work..."
                  value={newOrder.description}
                  onChange={e => setNewOrder({ ...newOrder, description: e.target.value })}
                />
              </div>

              {/* Technician Notes */}
              <div className="col-12">
                <label className="form-label small fw-semibold">Technician Assignment & Remarks</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. Lead Powerplant Specialist assigned. Tooling kits staged in Bay 2."
                  value={newOrder.technician_notes}
                  onChange={e => setNewOrder({ ...newOrder, technician_notes: e.target.value })}
                />
              </div>

              {/* Submit Buttons */}
              <div className="col-12 text-end pt-2 border-top d-flex justify-content-end gap-2">
                <button
                  type="button"
                  className="btn btn-outline-secondary"
                  onClick={() => setShowAddForm(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary d-inline-flex align-items-center gap-2"
                  disabled={actionLoading}
                >
                  <Save size={16} />
                  <span>{actionLoading ? 'Saving...' : 'Save Work Order'}</span>
                </button>
              </div>
            </div>
          </form>
        </div>
      )}

      {/* Edit Work Order Form Modal / Panel (Task 4 & 6) */}
      {editingRecord && (
        <div className="aerocard mb-4 border-warning">
          <div className="d-flex justify-content-between align-items-center mb-3 pb-2 border-bottom">
            <h6 className="fw-bold text-warning-emphasis mb-0 d-flex align-items-center gap-2">
              <Edit3 size={18} />
              <span>Edit Maintenance Work Order #{editingRecord.id} ({editingRecord.tail_number})</span>
            </h6>
            <button
              type="button"
              className="btn-close btn-sm"
              onClick={() => setEditingRecord(null)}
              aria-label="Close"
            />
          </div>

          <form onSubmit={handleUpdateOrder}>
            <div className="row g-3">
              <div className="col-12 col-md-8">
                <label className="form-label small fw-semibold">Work Order Title <span className="text-danger">*</span></label>
                <input
                  type="text"
                  className={`form-control ${formErrors.title ? 'is-invalid' : ''}`}
                  value={editingRecord.title}
                  onChange={e => setEditingRecord({ ...editingRecord, title: e.target.value })}
                />
                {formErrors.title && <div className="invalid-feedback">{formErrors.title}</div>}
              </div>

              <div className="col-12 col-md-4">
                <label className="form-label small fw-semibold">Priority</label>
                <select
                  className="form-select"
                  value={editingRecord.priority}
                  onChange={e => setEditingRecord({ ...editingRecord, priority: e.target.value })}
                >
                  <option value="LOW">LOW</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="HIGH">HIGH</option>
                  <option value="CRITICAL">CRITICAL</option>
                </select>
              </div>

              <div className="col-12 col-md-4">
                <label className="form-label small fw-semibold">Status (Task 3)</label>
                <select
                  className="form-select"
                  value={editingRecord.status}
                  onChange={e => {
                    const nextStatus = e.target.value;
                    const nextCompDate = nextStatus === 'COMPLETED' ? new Date().toISOString().split('T')[0] : editingRecord.completed_date;
                    setEditingRecord({ ...editingRecord, status: nextStatus, completed_date: nextCompDate });
                  }}
                >
                  <option value="PENDING">PENDING</option>
                  <option value="SCHEDULED">SCHEDULED</option>
                  <option value="IN_PROGRESS">IN_PROGRESS</option>
                  <option value="COMPLETED">COMPLETED</option>
                  <option value="CANCELLED">CANCELLED</option>
                </select>
              </div>

              <div className="col-12 col-md-4">
                <label className="form-label small fw-semibold">Scheduled Date</label>
                <input
                  type="date"
                  className="form-control"
                  value={editingRecord.scheduled_date || ''}
                  onChange={e => setEditingRecord({ ...editingRecord, scheduled_date: e.target.value })}
                />
              </div>

              <div className="col-12 col-md-4">
                <label className="form-label small fw-semibold">Completed Date</label>
                <input
                  type="date"
                  className="form-control"
                  value={editingRecord.completed_date || ''}
                  onChange={e => setEditingRecord({ ...editingRecord, completed_date: e.target.value })}
                />
              </div>

              <div className="col-12">
                <label className="form-label small fw-semibold">Scope & Description</label>
                <textarea
                  className="form-control"
                  rows={2}
                  value={editingRecord.description || ''}
                  onChange={e => setEditingRecord({ ...editingRecord, description: e.target.value })}
                />
              </div>

              <div className="col-12">
                <label className="form-label small fw-semibold">Technician Log & Findings</label>
                <textarea
                  className="form-control"
                  rows={2}
                  value={editingRecord.technician_notes || ''}
                  onChange={e => setEditingRecord({ ...editingRecord, technician_notes: e.target.value })}
                />
              </div>

              <div className="col-12 text-end pt-2 border-top d-flex justify-content-end gap-2">
                <button
                  type="button"
                  className="btn btn-outline-secondary"
                  onClick={() => setEditingRecord(null)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-warning d-inline-flex align-items-center gap-2"
                  disabled={actionLoading}
                >
                  <Save size={16} />
                  <span>{actionLoading ? 'Saving...' : 'Save Changes'}</span>
                </button>
              </div>
            </div>
          </form>
        </div>
      )}

      {/* Details View Modal / Card (Task 4) */}
      {viewingRecord && (
        <div className="aerocard mb-4 border-info">
          <div className="d-flex justify-content-between align-items-center mb-3 pb-2 border-bottom">
            <h6 className="fw-bold text-dark mb-0 d-flex align-items-center gap-2">
              <FileText size={18} className="text-info" />
              <span>Work Order Details: #{viewingRecord.id} • {viewingRecord.tail_number}</span>
            </h6>
            <button
              type="button"
              className="btn-close btn-sm"
              onClick={() => setViewingRecord(null)}
              aria-label="Close"
            />
          </div>

          <div className="row g-3">
            <div className="col-12 col-md-6">
              <div className="p-3 bg-light rounded border">
                <div className="small text-muted">Title</div>
                <div className="fw-bold text-dark mb-2">{viewingRecord.title}</div>

                <div className="small text-muted">Target Aircraft</div>
                <div className="fw-semibold text-primary mb-2">
                  {viewingRecord.tail_number} ({viewingRecord.model}) • {viewingRecord.engine_type}
                </div>

                <div className="small text-muted">Description</div>
                <p className="text-dark small mb-0">
                  {viewingRecord.description || 'No detailed scope provided.'}
                </p>
              </div>
            </div>

            <div className="col-12 col-md-6">
              <div className="p-3 bg-light rounded border h-100 d-flex flex-column justify-content-between">
                <div>
                  <div className="d-flex justify-content-between mb-2">
                    <span className="small text-muted">Priority:</span>
                    <span className="badge bg-light text-dark border">{viewingRecord.priority}</span>
                  </div>
                  <div className="d-flex justify-content-between mb-2">
                    <span className="small text-muted">Status:</span>
                    <span className="badge bg-primary">{viewingRecord.status}</span>
                  </div>
                  <div className="d-flex justify-content-between mb-2">
                    <span className="small text-muted">Scheduled Target:</span>
                    <span className="small fw-semibold">{viewingRecord.scheduled_date}</span>
                  </div>
                  <div className="d-flex justify-content-between mb-2">
                    <span className="small text-muted">Completion Date:</span>
                    <span className="small fw-semibold">{viewingRecord.completed_date || 'In Progress'}</span>
                  </div>
                  <div className="small text-muted mt-2">Technician Notes:</div>
                  <div className="small text-dark p-2 rounded bg-white border mt-1">
                    {viewingRecord.technician_notes || 'No technician findings recorded.'}
                  </div>
                </div>

                <div className="pt-2 text-end">
                  <button
                    className="btn btn-sm btn-outline-warning d-inline-flex align-items-center gap-1 me-2"
                    onClick={() => {
                      setEditingRecord(viewingRecord);
                      setViewingRecord(null);
                    }}
                  >
                    <Edit3 size={14} />
                    <span>Edit Order</span>
                  </button>
                  <button
                    className="btn btn-sm btn-outline-secondary"
                    onClick={() => setViewingRecord(null)}
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filter and Search Bar (Task 4) */}
      <div className="aerocard mb-4 p-3">
        <div className="row g-2 align-items-center">
          {/* Search */}
          <div className="col-12 col-md-4">
            <div className="input-group input-group-sm">
              <span className="input-group-text bg-white">
                <Search size={14} className="text-secondary" />
              </span>
              <input
                type="text"
                className="form-control"
                placeholder="Search orders, airframes, or descriptions..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          {/* Status Filter */}
          <div className="col-6 col-md-2">
            <select
              className="form-select form-select-sm"
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value)}
            >
              <option value="ALL">Status: All</option>
              <option value="PENDING">Pending / Scheduled</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="COMPLETED">Completed</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>

          {/* Priority Filter */}
          <div className="col-6 col-md-2">
            <select
              className="form-select form-select-sm"
              value={filterPriority}
              onChange={e => setFilterPriority(e.target.value)}
            >
              <option value="ALL">Priority: All</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>

          {/* Aircraft Filter */}
          <div className="col-12 col-md-3">
            <select
              className="form-select form-select-sm"
              value={filterAircraft}
              onChange={e => setFilterAircraft(e.target.value)}
            >
              <option value="ALL">Aircraft: All Fleet Units</option>
              {fleet.map(a => (
                <option key={a.id} value={a.id}>
                  {a.tail_number} ({a.model})
                </option>
              ))}
            </select>
          </div>

          {/* Reset Filters */}
          <div className="col-12 col-md-1 text-end">
            <button
              className="btn btn-sm btn-outline-secondary w-100"
              onClick={() => {
                setSearchTerm('');
                setFilterStatus('ALL');
                setFilterPriority('ALL');
                setFilterAircraft('ALL');
              }}
              title="Reset all filters"
            >
              Reset
            </button>
          </div>
        </div>
      </div>

      {/* Maintenance Work Orders Table (Task 4) */}
      <div className="aerocard">
        <div className="d-flex align-items-center justify-content-between mb-3 pb-2 border-bottom flex-wrap gap-2">
          <div>
            <h6 className="fw-bold mb-0">Maintenance Work Orders Backlog</h6>
            <small className="text-muted">
              Scheduled tasks, shop visits, parts inspections, and technician sign-offs
            </small>
          </div>
          <span className="badge bg-light text-secondary border">
            {records.length} Work Orders
          </span>
        </div>

        {isLoading ? (
          <LoadingSpinner message="Fetching maintenance records from relational database..." />
        ) : (
          <div className="table-responsive">
            <table className="aero-table">
              <thead>
                <tr>
                  <th>Order ID</th>
                  <th>Aircraft</th>
                  <th>Title & Description</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Scheduled Date</th>
                  <th>Completed Date</th>
                  <th className="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                {records.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="text-center py-4 text-muted small">
                      No maintenance work orders match the selected criteria.
                    </td>
                  </tr>
                ) : (
                  records.map(order => {
                    const isCritical = order.priority === 'CRITICAL';
                    const isHigh = order.priority === 'HIGH';

                    return (
                      <tr key={order.id}>
                        <td className="fw-mono text-muted small">
                          #{order.id}
                        </td>
                        <td>
                          <div className="fw-bold text-dark">{order.tail_number}</div>
                          <div className="text-secondary small" style={{ fontSize: '0.72rem' }}>
                            {order.model}
                          </div>
                        </td>
                        <td style={{ maxWidth: 280 }}>
                          <div className="fw-semibold text-dark">{order.title}</div>
                          <div className="text-secondary small text-truncate" title={order.description}>
                            {order.description}
                          </div>
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
                          <select
                            className="form-select form-select-sm"
                            style={{ width: 135, fontSize: '0.78rem' }}
                            value={order.status}
                            onChange={e => handleQuickStatusChange(order.id, e.target.value)}
                          >
                            <option value="PENDING">Pending</option>
                            <option value="SCHEDULED">Scheduled</option>
                            <option value="IN_PROGRESS">In Progress</option>
                            <option value="COMPLETED">Completed</option>
                            <option value="CANCELLED">Cancelled</option>
                          </select>
                        </td>
                        <td className="small text-secondary">{order.scheduled_date}</td>
                        <td className="small text-secondary">
                          {order.completed_date || '—'}
                        </td>
                        <td className="text-end">
                          <div className="d-inline-flex gap-1">
                            <button
                              className="btn btn-sm btn-outline-info p-1 px-2"
                              title="View Work Order Details"
                              onClick={() => {
                                setViewingRecord(order);
                                setEditingRecord(null);
                              }}
                            >
                              <Eye size={14} />
                            </button>
                            <button
                              className="btn btn-sm btn-outline-warning p-1 px-2"
                              title="Edit Work Order"
                              onClick={() => {
                                setEditingRecord(order);
                                setViewingRecord(null);
                              }}
                            >
                              <Edit3 size={14} />
                            </button>
                            <button
                              className="btn btn-sm btn-outline-danger p-1 px-2"
                              title="Delete Work Order"
                              onClick={() => handleDeleteOrder(order.id, order.title)}
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
