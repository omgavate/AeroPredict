import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Plane,
  Save,
  Activity,
  Cpu,
  Clock,
  CheckCircle,
  AlertTriangle,
  Database,
  Calendar,
  Layers
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import aircraftApi from '../api/aircraftApi';

export default function AircraftDetailsPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [aircraft, setAircraft] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLive, setIsLive] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [saveMessage, setSaveMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [formErrors, setFormErrors] = useState({});

  // Editable Form State
  const [formData, setFormData] = useState({
    tail_number: '',
    model: '',
    manufacturer: '',
    manufacturing_year: '',
    engine_type: '',
    cmapss_unit_id: '',
    current_cycles: '',
    flight_hours: '',
    status: 'OPERATIONAL'
  });

  const loadAircraftDetails = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await aircraftApi.getById(id);
      if (res.success && res.data) {
        setAircraft(res.data);
        setIsLive(res.isLive);
        setFormData({
          tail_number: res.data.tail_number || '',
          model: res.data.model || '',
          manufacturer: res.data.manufacturer || '',
          manufacturing_year: res.data.manufacturing_year || '',
          engine_type: res.data.engine_type || '',
          cmapss_unit_id: res.data.cmapss_unit_id || '',
          current_cycles: res.data.current_cycles ?? 0,
          flight_hours: res.data.flight_hours ?? 0,
          status: res.data.status || 'OPERATIONAL'
        });
      } else {
        setErrorMessage('Aircraft not found in system.');
      }
    } catch (err) {
      setErrorMessage(err.message || 'Error loading aircraft details.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAircraftDetails();
  }, [id]);

  const handleUpdate = async (e) => {
    e.preventDefault();
    setFormErrors({});
    setErrorMessage(null);

    try {
      const payload = {
        tail_number: formData.tail_number.trim().toUpperCase(),
        model: formData.model.trim(),
        manufacturer: formData.manufacturer.trim(),
        manufacturing_year: formData.manufacturing_year ? parseInt(formData.manufacturing_year, 10) : null,
        engine_type: formData.engine_type.trim(),
        cmapss_unit_id: formData.cmapss_unit_id ? parseInt(formData.cmapss_unit_id, 10) : null,
        current_cycles: parseInt(formData.current_cycles || 0, 10),
        flight_hours: parseInt(formData.flight_hours || 0, 10),
        status: formData.status
      };

      const result = await aircraftApi.update(id, payload);

      if (!result.success) {
        if (result.details) {
          setFormErrors(result.details);
        } else {
          setErrorMessage(result.error || 'Failed to update aircraft.');
        }
        return;
      }

      setAircraft(result.data);
      setEditMode(false);
      setSaveMessage(`Aircraft ${result.data.tail_number} updated successfully in database.`);
      setTimeout(() => setSaveMessage(null), 3500);
    } catch (err) {
      setErrorMessage(err.message || 'Error saving aircraft updates.');
    }
  };

  if (isLoading) {
    return <LoadingSpinner message="Fetching aircraft telemetry and database profile..." />;
  }

  if (errorMessage && !aircraft) {
    return (
      <div className="alert alert-danger p-4">
        <h5>Aircraft Record Unavailable</h5>
        <p>{errorMessage}</p>
        <Link to="/aircraft" className="btn btn-sm btn-outline-danger">
          Return to Fleet Inventory
        </Link>
      </div>
    );
  }

  return (
    <div>
      <div className="demo-banner">
        <span>✈️ <strong>Module 2:</strong> Airframe Diagnostics & Technical Profile</span>
        <span className="badge bg-white text-primary d-inline-flex align-items-center gap-1">
          <Database size={13} />
          <span>{isLive ? 'Live MySQL Record' : 'Offline Mode'}</span>
        </span>
      </div>

      {saveMessage && (
        <div className="alert alert-success d-flex align-items-center gap-2 py-2 mb-3">
          <CheckCircle size={16} />
          <span>{saveMessage}</span>
        </div>
      )}

      {errorMessage && (
        <div className="alert alert-danger d-flex align-items-center gap-2 py-2 mb-3">
          <AlertTriangle size={16} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Header */}
      <div className="d-flex align-items-center justify-content-between mb-4 flex-wrap gap-2">
        <div>
          <Link to="/aircraft" className="btn btn-sm btn-outline-secondary d-inline-flex align-items-center gap-1 mb-2">
            <ArrowLeft size={16} />
            <span>Back to Fleet</span>
          </Link>
          <div className="d-flex align-items-center gap-3">
            <h4 className="fw-bold text-dark mb-0">{aircraft.tail_number}</h4>
            <StatusBadge status={aircraft.status} />
          </div>
          <p className="text-secondary small mb-0 mt-1">
            {aircraft.model} • {aircraft.manufacturer} • Engine Unit #{aircraft.cmapss_unit_id || 'N/A'}
          </p>
        </div>

        <div className="d-flex gap-2">
          <Link
            to={`/monitoring?unit=${aircraft.cmapss_unit_id || 1}&tail=${aircraft.tail_number}`}
            className="btn btn-outline-primary d-inline-flex align-items-center gap-2"
          >
            <Activity size={16} />
            <span>Sensor Graphs</span>
          </Link>
          <Link
            to={`/predictive?id=${aircraft.id}&tail=${aircraft.tail_number}`}
            className="btn btn-primary d-inline-flex align-items-center gap-2"
          >
            <Cpu size={16} />
            <span>Predict RUL</span>
          </Link>
        </div>
      </div>

      {/* Profile & Specifications */}
      <div className="row g-4">
        <div className="col-12 col-lg-7">
          <div className="aerocard mb-4">
            <div className="d-flex align-items-center justify-content-between mb-3 pb-2 border-bottom">
              <h6 className="fw-bold mb-0">Airframe & Engine Configuration</h6>
              <button
                className={`btn btn-sm ${editMode ? 'btn-secondary' : 'btn-outline-primary'}`}
                onClick={() => setEditMode(!editMode)}
              >
                {editMode ? 'Cancel Edit' : 'Edit Configuration'}
              </button>
            </div>

            {editMode ? (
              <form onSubmit={handleUpdate}>
                <div className="row g-3">
                  <div className="col-12 col-md-6">
                    <label className="form-label small fw-semibold">Tail Registration</label>
                    <input
                      type="text"
                      className={`form-control ${formErrors.tail_number ? 'is-invalid' : ''}`}
                      value={formData.tail_number}
                      onChange={e => setFormData({ ...formData, tail_number: e.target.value.toUpperCase() })}
                    />
                    {formErrors.tail_number && <div className="invalid-feedback">{formErrors.tail_number}</div>}
                  </div>

                  <div className="col-12 col-md-6">
                    <label className="form-label small fw-semibold">Aircraft Model</label>
                    <input
                      type="text"
                      className={`form-control ${formErrors.model ? 'is-invalid' : ''}`}
                      value={formData.model}
                      onChange={e => setFormData({ ...formData, model: e.target.value })}
                    />
                    {formErrors.model && <div className="invalid-feedback">{formErrors.model}</div>}
                  </div>

                  <div className="col-12 col-md-6">
                    <label className="form-label small fw-semibold">Manufacturer</label>
                    <input
                      type="text"
                      className="form-control"
                      value={formData.manufacturer}
                      onChange={e => setFormData({ ...formData, manufacturer: e.target.value })}
                    />
                  </div>

                  <div className="col-12 col-md-6">
                    <label className="form-label small fw-semibold">Manufacturing Year</label>
                    <input
                      type="number"
                      className={`form-control ${formErrors.manufacturing_year ? 'is-invalid' : ''}`}
                      value={formData.manufacturing_year}
                      onChange={e => setFormData({ ...formData, manufacturing_year: e.target.value })}
                    />
                    {formErrors.manufacturing_year && <div className="invalid-feedback">{formErrors.manufacturing_year}</div>}
                  </div>

                  <div className="col-12 col-md-6">
                    <label className="form-label small fw-semibold">Turbofan Engine Model</label>
                    <input
                      type="text"
                      className="form-control"
                      value={formData.engine_type}
                      onChange={e => setFormData({ ...formData, engine_type: e.target.value })}
                    />
                  </div>

                  <div className="col-12 col-md-6">
                    <label className="form-label small fw-semibold">C-MAPSS Unit (1-100)</label>
                    <input
                      type="number"
                      min="1"
                      max="100"
                      className={`form-control ${formErrors.cmapss_unit_id ? 'is-invalid' : ''}`}
                      value={formData.cmapss_unit_id}
                      onChange={e => setFormData({ ...formData, cmapss_unit_id: e.target.value })}
                    />
                    {formErrors.cmapss_unit_id && <div className="invalid-feedback">{formErrors.cmapss_unit_id}</div>}
                  </div>

                  <div className="col-12 col-md-4">
                    <label className="form-label small fw-semibold">Operating Cycles</label>
                    <input
                      type="number"
                      className={`form-control ${formErrors.current_cycles ? 'is-invalid' : ''}`}
                      value={formData.current_cycles}
                      onChange={e => setFormData({ ...formData, current_cycles: e.target.value })}
                    />
                    {formErrors.current_cycles && <div className="invalid-feedback">{formErrors.current_cycles}</div>}
                  </div>

                  <div className="col-12 col-md-4">
                    <label className="form-label small fw-semibold">Flight Hours</label>
                    <input
                      type="number"
                      className={`form-control ${formErrors.flight_hours ? 'is-invalid' : ''}`}
                      value={formData.flight_hours}
                      onChange={e => setFormData({ ...formData, flight_hours: e.target.value })}
                    />
                    {formErrors.flight_hours && <div className="invalid-feedback">{formErrors.flight_hours}</div>}
                  </div>

                  <div className="col-12 col-md-4">
                    <label className="form-label small fw-semibold">Operational Status</label>
                    <select
                      className="form-select"
                      value={formData.status}
                      onChange={e => setFormData({ ...formData, status: e.target.value })}
                    >
                      <option value="OPERATIONAL">OPERATIONAL</option>
                      <option value="UNDER_MAINTENANCE">UNDER_MAINTENANCE</option>
                      <option value="ATTENTION_REQUIRED">ATTENTION_REQUIRED</option>
                      <option value="RETIRED">RETIRED</option>
                    </select>
                  </div>

                  <div className="col-12 text-end pt-2">
                    <button type="submit" className="btn btn-primary d-inline-flex align-items-center gap-2">
                      <Save size={16} />
                      <span>Update MySQL Record</span>
                    </button>
                  </div>
                </div>
              </form>
            ) : (
              <div className="row g-3">
                <div className="col-6 col-md-4">
                  <div className="text-muted small">Registration</div>
                  <div className="fw-bold text-dark">{aircraft.tail_number}</div>
                </div>
                <div className="col-6 col-md-4">
                  <div className="text-muted small">Model</div>
                  <div className="fw-bold text-dark">{aircraft.model}</div>
                </div>
                <div className="col-6 col-md-4">
                  <div className="text-muted small">Manufacturer</div>
                  <div className="fw-bold text-dark">{aircraft.manufacturer}</div>
                </div>
                <div className="col-6 col-md-4">
                  <div className="text-muted small">Year Built</div>
                  <div className="fw-bold text-dark">{aircraft.manufacturing_year || '—'}</div>
                </div>
                <div className="col-6 col-md-4">
                  <div className="text-muted small">Turbofan Engine</div>
                  <div className="fw-bold text-primary">{aircraft.engine_type}</div>
                </div>
                <div className="col-6 col-md-4">
                  <div className="text-muted small">C-MAPSS Unit</div>
                  <div className="fw-bold text-dark">
                    {aircraft.cmapss_unit_id ? `Engine Unit #${aircraft.cmapss_unit_id}` : 'Unassigned'}
                  </div>
                </div>
                <div className="col-6 col-md-4">
                  <div className="text-muted small">Operating Cycles</div>
                  <div className="fw-mono fw-bold text-dark">{aircraft.current_cycles} Cycles</div>
                </div>
                <div className="col-6 col-md-4">
                  <div className="text-muted small">Total Flight Hours</div>
                  <div className="fw-bold text-dark">{aircraft.flight_hours || 0} hrs</div>
                </div>
                <div className="col-6 col-md-4">
                  <div className="text-muted small">Status</div>
                  <div><StatusBadge status={aircraft.status} /></div>
                </div>
              </div>
            )}
          </div>

          {/* Database Maintenance Log (if any records present) */}
          <div className="aerocard">
            <h6 className="fw-bold mb-3 pb-2 border-bottom">Recent Maintenance Log</h6>
            {aircraft.recent_maintenance && aircraft.recent_maintenance.length > 0 ? (
              aircraft.recent_maintenance.map(m => (
                <div key={m.id} className="p-3 mb-2 rounded bg-light border">
                  <div className="d-flex justify-content-between mb-1">
                    <span className="fw-bold text-dark">{m.title}</span>
                    <span className="badge bg-secondary">{m.status}</span>
                  </div>
                  <p className="small text-secondary mb-1">{m.description}</p>
                  <small className="text-muted">Scheduled: {m.scheduled_date}</small>
                </div>
              ))
            ) : (
              <div className="text-muted small py-3 text-center">
                No active work orders for {aircraft.tail_number}.
              </div>
            )}
          </div>
        </div>

        {/* Diagnostics & Navigation */}
        <div className="col-12 col-lg-5">
          <div className="aerocard mb-4">
            <h6 className="fw-bold mb-3 pb-2 border-bottom">Engine Health Telemetry Summary</h6>
            <div className="p-3 rounded bg-light border mb-3">
              <div className="d-flex justify-content-between align-items-center mb-2">
                <span className="small text-secondary">Engine ID:</span>
                <span className="small fw-bold text-dark">Unit #{aircraft.cmapss_unit_id || 'N/A'}</span>
              </div>
              <div className="d-flex justify-content-between align-items-center mb-2">
                <span className="small text-secondary">Elapsed Cycles:</span>
                <span className="small fw-mono fw-bold text-primary">{aircraft.current_cycles}</span>
              </div>
              <div className="d-flex justify-content-between align-items-center mb-2">
                <span className="small text-secondary">Database Record ID:</span>
                <span className="small fw-mono text-muted">#{aircraft.id}</span>
              </div>
              <div className="d-flex justify-content-between align-items-center">
                <span className="small text-secondary">Last Updated:</span>
                <span className="small text-muted">{aircraft.updated_at ? aircraft.updated_at.substring(0, 10) : 'Today'}</span>
              </div>
            </div>

            <div className="d-grid gap-2">
              <Link
                to={`/monitoring?unit=${aircraft.cmapss_unit_id || 1}&tail=${aircraft.tail_number}`}
                className="btn btn-outline-secondary d-flex align-items-center justify-content-center gap-2"
              >
                <Activity size={16} />
                <span>Open Multi-Sensor Telemetry</span>
              </Link>
              <Link
                to={`/predictive?id=${aircraft.id}&tail=${aircraft.tail_number}`}
                className="btn btn-outline-primary d-flex align-items-center justify-content-center gap-2"
              >
                <Cpu size={16} />
                <span>Evaluate Prognostic RUL</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
