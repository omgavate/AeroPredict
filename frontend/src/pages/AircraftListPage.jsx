import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Plane,
  Plus,
  Search,
  Filter,
  Eye,
  Trash2,
  Activity,
  Cpu,
  CheckCircle,
  Clock,
  AlertTriangle,
  RefreshCw,
  Database
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import aircraftApi from '../api/aircraftApi';

export default function AircraftListPage() {
  const [aircraftList, setAircraftList] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);
  const [isLive, setIsLive] = useState(false);
  const [notification, setNotification] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  // Load aircraft from Flask backend
  const loadAircraft = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await aircraftApi.getAll(searchTerm, statusFilter);
      if (res.success) {
        setAircraftList(res.data);
        setIsLive(res.isLive);
      }
    } catch (err) {
      setErrorMsg('Failed to communicate with aircraft service: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      loadAircraft();
    }, 200);
    return () => clearTimeout(timer);
  }, [searchTerm, statusFilter]);

  const handleDelete = async (id, tailNumber) => {
    if (window.confirm(`Are you sure you want to permanently remove aircraft ${tailNumber} (ID #${id}) from MySQL fleet database?`)) {
      try {
        const res = await aircraftApi.delete(id);
        if (res.success) {
          setNotification(`Aircraft ${tailNumber} removed from database.`);
          setAircraftList(prev => prev.filter(a => a.id !== id));
          setTimeout(() => setNotification(null), 3500);
        }
      } catch (err) {
        alert('Delete failed: ' + err.message);
      }
    }
  };

  return (
    <div>
      {/* Live Integration Status Banner */}
      <div className="demo-banner">
        <span>✈️ <strong>Module 2:</strong> Aircraft Fleet Management Interface</span>
        <span className="badge bg-white text-primary d-inline-flex align-items-center gap-1">
          <Database size={13} />
          <span>{isLive ? 'Live MySQL Database' : 'Local Standalone Mode'}</span>
        </span>
      </div>

      {notification && (
        <div className="alert alert-success d-flex align-items-center gap-2 py-2 mb-3">
          <CheckCircle size={16} />
          <span>{notification}</span>
        </div>
      )}

      {errorMsg && (
        <div className="alert alert-danger d-flex align-items-center gap-2 py-2 mb-3">
          <AlertTriangle size={16} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Header */}
      <div className="d-flex align-items-center justify-content-between mb-4 flex-wrap gap-2">
        <div>
          <h4 className="fw-bold text-dark mb-1">Aircraft Fleet Inventory</h4>
          <p className="text-secondary small mb-0">
            Registered airframes stored in MySQL <code className="text-primary">aeropredict_db.aircraft</code>.
          </p>
        </div>
        <div className="d-flex gap-2">
          <button
            className="btn btn-outline-secondary d-inline-flex align-items-center gap-2"
            onClick={loadAircraft}
            disabled={isLoading}
            title="Refresh from MySQL"
          >
            <RefreshCw size={15} className={isLoading ? 'spinner-border spinner-border-sm' : ''} />
            <span className="d-none d-sm-inline">Refresh</span>
          </button>
          <Link to="/aircraft/add" className="btn btn-primary d-inline-flex align-items-center gap-2">
            <Plus size={16} />
            <span>Register New Aircraft</span>
          </Link>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="aerocard mb-4 p-3">
        <div className="row g-2 align-items-center">
          <div className="col-12 col-md-6 col-lg-5">
            <div className="input-group">
              <span className="input-group-text bg-white border-end-0 text-muted">
                <Search size={16} />
              </span>
              <input
                type="text"
                className="form-control border-start-0"
                placeholder="Search by tail number (e.g. N101AP), model or OEM..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          <div className="col-12 col-md-4 col-lg-3">
            <div className="input-group">
              <span className="input-group-text bg-white text-muted">
                <Filter size={16} />
              </span>
              <select
                className="form-select"
                value={statusFilter}
                onChange={e => setStatusFilter(e.target.value)}
              >
                <option value="ALL">All Statuses</option>
                <option value="OPERATIONAL">Operational</option>
                <option value="UNDER_MAINTENANCE">Under Maintenance</option>
                <option value="ATTENTION_REQUIRED">Attention Required</option>
                <option value="RETIRED">Retired</option>
              </select>
            </div>
          </div>

          <div className="col-12 col-md-2 text-md-end text-muted small ms-auto">
            {isLoading ? 'Loading records...' : `Showing ${aircraftList.length} airframes`}
          </div>
        </div>
      </div>

      {/* Aircraft Table / Loading State / Empty State */}
      <div className="aerocard p-0 overflow-hidden">
        {isLoading ? (
          <LoadingSpinner message="Querying aircraft records from database..." />
        ) : (
          <div className="table-responsive">
            <table className="aero-table mb-0">
              <thead>
                <tr>
                  <th>Registration</th>
                  <th>Model / Type</th>
                  <th>Manufacturer</th>
                  <th>Engine Model</th>
                  <th>C-MAPSS Unit</th>
                  <th>Operating Cycles</th>
                  <th>Flight Hours</th>
                  <th>Status</th>
                  <th className="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                {aircraftList.length === 0 ? (
                  <tr>
                    <td colSpan="9" className="text-center py-5 text-muted">
                      <div className="mb-2">
                        <Plane size={32} className="text-secondary opacity-50" />
                      </div>
                      <div className="fw-semibold">No aircraft records found.</div>
                      <div className="small">Try clearing your search query or register a new aircraft.</div>
                    </td>
                  </tr>
                ) : (
                  aircraftList.map(aircraft => (
                    <tr key={aircraft.id}>
                      <td>
                        <div className="fw-bold text-dark">{aircraft.tail_number}</div>
                        <div className="text-muted small" style={{ fontSize: '0.74rem' }}>
                          ID #{aircraft.id}
                        </div>
                      </td>
                      <td className="fw-medium">
                        <div>{aircraft.model}</div>
                        {aircraft.manufacturing_year && (
                          <div className="text-muted small" style={{ fontSize: '0.74rem' }}>
                            Year: {aircraft.manufacturing_year}
                          </div>
                        )}
                      </td>
                      <td className="text-secondary">{aircraft.manufacturer}</td>
                      <td>
                        <span className="badge bg-light text-dark border">
                          {aircraft.engine_type}
                        </span>
                      </td>
                      <td>
                        {aircraft.cmapss_unit_id ? (
                          <span className="badge bg-primary-subtle text-primary border">
                            Unit #{aircraft.cmapss_unit_id}
                          </span>
                        ) : (
                          <span className="text-muted small">—</span>
                        )}
                      </td>
                      <td className="fw-mono fw-bold text-dark">{aircraft.current_cycles}</td>
                      <td className="fw-mono text-secondary small">{aircraft.flight_hours || 0} hrs</td>
                      <td>
                        <StatusBadge status={aircraft.status} />
                      </td>
                      <td className="text-end">
                        <div className="d-inline-flex gap-1">
                          <Link
                            to={`/aircraft/${aircraft.id}`}
                            className="btn btn-sm btn-outline-secondary p-1 px-2"
                            title="View / Edit Aircraft Details"
                          >
                            <Eye size={15} />
                          </Link>
                          <Link
                            to={`/monitoring?unit=${aircraft.cmapss_unit_id || 1}&tail=${aircraft.tail_number}`}
                            className="btn btn-sm btn-outline-info p-1 px-2"
                            title="Engine Sensor Telemetry"
                          >
                            <Activity size={15} />
                          </Link>
                          <Link
                            to={`/predictive?id=${aircraft.id}&tail=${aircraft.tail_number}`}
                            className="btn btn-sm btn-outline-primary p-1 px-2"
                            title="Predict Remaining Useful Life"
                          >
                            <Cpu size={15} />
                          </Link>
                          <button
                            className="btn btn-sm btn-outline-danger p-1 px-2"
                            title="Delete Aircraft"
                            onClick={() => handleDelete(aircraft.id, aircraft.tail_number)}
                          >
                            <Trash2 size={15} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
