import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Save, Plane, AlertCircle, AlertTriangle } from 'lucide-react';
import aircraftApi from '../api/aircraftApi';

export default function AddAircraftPage() {
  const navigate = useNavigate();

  const currentYear = new Date().getFullYear();

  const [formData, setFormData] = useState({
    tail_number: '',
    model: '',
    manufacturer: 'Boeing',
    manufacturing_year: '2022',
    engine_type: 'CFM56-7B',
    cmapss_unit_id: '',
    current_cycles: '0',
    flight_hours: '0',
    status: 'OPERATIONAL'
  });

  const [errors, setErrors] = useState({});
  const [generalError, setGeneralError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validate = () => {
    const errs = {};
    if (!formData.tail_number.trim()) {
      errs.tail_number = 'Aircraft registration / tail number is required (e.g. N101AP or VT-AER).';
    }
    if (!formData.model.trim()) {
      errs.model = 'Aircraft model is required (e.g. Boeing 737-800).';
    }
    if (!formData.manufacturer.trim()) {
      errs.manufacturer = 'Manufacturer is required.';
    }
    if (formData.manufacturing_year) {
      const year = parseInt(formData.manufacturing_year, 10);
      if (isNaN(year) || year < 1950 || year > currentYear + 1) {
        errs.manufacturing_year = `Manufacturing year must be between 1950 and ${currentYear + 1}.`;
      }
    }
    if (formData.flight_hours) {
      const hours = parseInt(formData.flight_hours, 10);
      if (isNaN(hours) || hours < 0) {
        errs.flight_hours = 'Flight hours cannot be negative.';
      }
    }
    if (formData.cmapss_unit_id) {
      const unit = parseInt(formData.cmapss_unit_id, 10);
      if (isNaN(unit) || unit < 1 || unit > 100) {
        errs.cmapss_unit_id = 'C-MAPSS Unit ID must be an integer between 1 and 100.';
      }
    }
    if (formData.current_cycles) {
      const cycles = parseInt(formData.current_cycles, 10);
      if (isNaN(cycles) || cycles < 0) {
        errs.current_cycles = 'Operating cycles cannot be negative.';
      }
    }
    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setGeneralError(null);
    const clientErrors = validate();
    if (Object.keys(clientErrors).length > 0) {
      setErrors(clientErrors);
      return;
    }

    setErrors({});
    setIsSubmitting(true);

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

      const result = await aircraftApi.create(payload);

      if (!result.success) {
        if (result.details) {
          setErrors(result.details);
        } else {
          setGeneralError(result.error || 'Failed to register aircraft.');
        }
        setIsSubmitting(false);
        return;
      }

      alert(`Aircraft ${payload.tail_number} registered successfully!`);
      navigate('/aircraft');
    } catch (err) {
      setGeneralError(err.message || 'Error connecting to backend API.');
      setIsSubmitting(false);
    }
  };

  return (
    <div>
      <div className="mb-4">
        <Link to="/aircraft" className="btn btn-sm btn-outline-secondary d-inline-flex align-items-center gap-1 mb-2">
          <ArrowLeft size={16} />
          <span>Back to Fleet List</span>
        </Link>
        <h4 className="fw-bold text-dark mb-1">Register New Aircraft</h4>
        <p className="text-secondary small mb-0">
          Enter verified airframe metadata, propulsion specifications and C-MAPSS unit assignments.
        </p>
      </div>

      {generalError && (
        <div className="alert alert-danger d-flex align-items-center gap-2 mb-3">
          <AlertTriangle size={18} />
          <span>{generalError}</span>
        </div>
      )}

      <div className="row">
        <div className="col-12 col-lg-8">
          <div className="aerocard">
            <form onSubmit={handleSubmit}>
              <div className="row g-3">
                {/* Tail Number */}
                <div className="col-12 col-md-6">
                  <label className="form-label fw-semibold small">
                    Registration / Tail Number <span className="text-danger">*</span>
                  </label>
                  <input
                    type="text"
                    className={`form-control ${errors.tail_number ? 'is-invalid' : ''}`}
                    placeholder="e.g. N512AP or VT-DEL"
                    value={formData.tail_number}
                    onChange={e => setFormData({ ...formData, tail_number: e.target.value.toUpperCase() })}
                  />
                  {errors.tail_number && (
                    <div className="invalid-feedback">{errors.tail_number}</div>
                  )}
                  <small className="text-muted" style={{ fontSize: '0.75rem' }}>
                    ICAO tail registration format (Unique).
                  </small>
                </div>

                {/* Aircraft Model */}
                <div className="col-12 col-md-6">
                  <label className="form-label fw-semibold small">
                    Aircraft Model <span className="text-danger">*</span>
                  </label>
                  <input
                    type="text"
                    className={`form-control ${errors.model ? 'is-invalid' : ''}`}
                    placeholder="e.g. Boeing 737-800"
                    value={formData.model}
                    onChange={e => setFormData({ ...formData, model: e.target.value })}
                  />
                  {errors.model && <div className="invalid-feedback">{errors.model}</div>}
                </div>

                {/* Manufacturer */}
                <div className="col-12 col-md-6">
                  <label className="form-label fw-semibold small">
                    Manufacturer <span className="text-danger">*</span>
                  </label>
                  <select
                    className={`form-select ${errors.manufacturer ? 'is-invalid' : ''}`}
                    value={formData.manufacturer}
                    onChange={e => setFormData({ ...formData, manufacturer: e.target.value })}
                  >
                    <option value="Boeing">Boeing</option>
                    <option value="Airbus">Airbus</option>
                    <option value="Embraer">Embraer</option>
                    <option value="Bombardier">Bombardier</option>
                  </select>
                  {errors.manufacturer && <div className="invalid-feedback">{errors.manufacturer}</div>}
                </div>

                {/* Manufacturing Year */}
                <div className="col-12 col-md-6">
                  <label className="form-label fw-semibold small">Manufacturing Year</label>
                  <input
                    type="number"
                    min="1950"
                    max={currentYear + 1}
                    className={`form-control ${errors.manufacturing_year ? 'is-invalid' : ''}`}
                    placeholder="e.g. 2020"
                    value={formData.manufacturing_year}
                    onChange={e => setFormData({ ...formData, manufacturing_year: e.target.value })}
                  />
                  {errors.manufacturing_year && (
                    <div className="invalid-feedback">{errors.manufacturing_year}</div>
                  )}
                </div>

                {/* Engine Type */}
                <div className="col-12 col-md-6">
                  <label className="form-label fw-semibold small">Turbofan Engine Model</label>
                  <select
                    className="form-select"
                    value={formData.engine_type}
                    onChange={e => setFormData({ ...formData, engine_type: e.target.value })}
                  >
                    <option value="CFM56-7B">CFM56-7B (Turbofan)</option>
                    <option value="LEAP-1A">CFM LEAP-1A</option>
                    <option value="LEAP-1B">CFM LEAP-1B</option>
                    <option value="GE90-115B">GE90-115B High Bypass</option>
                    <option value="Trent XWB-84">Rolls-Royce Trent XWB-84</option>
                    <option value="PW1900G">Pratt & Whitney PW1900G</option>
                  </select>
                </div>

                {/* C-MAPSS Unit Mapping */}
                <div className="col-12 col-md-6">
                  <label className="form-label fw-semibold small">
                    Assigned C-MAPSS Unit ID (1 - 100)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    className={`form-control ${errors.cmapss_unit_id ? 'is-invalid' : ''}`}
                    placeholder="Optional (1 to 100)"
                    value={formData.cmapss_unit_id}
                    onChange={e => setFormData({ ...formData, cmapss_unit_id: e.target.value })}
                  />
                  {errors.cmapss_unit_id && (
                    <div className="invalid-feedback">{errors.cmapss_unit_id}</div>
                  )}
                  <small className="text-muted" style={{ fontSize: '0.75rem' }}>
                    Maps simulated sensor channels from NASA C-MAPSS FD001.
                  </small>
                </div>

                {/* Current Cycles */}
                <div className="col-12 col-md-6">
                  <label className="form-label fw-semibold small">Initial Operating Cycles</label>
                  <input
                    type="number"
                    min="0"
                    className={`form-control ${errors.current_cycles ? 'is-invalid' : ''}`}
                    value={formData.current_cycles}
                    onChange={e => setFormData({ ...formData, current_cycles: e.target.value })}
                  />
                  {errors.current_cycles && (
                    <div className="invalid-feedback">{errors.current_cycles}</div>
                  )}
                </div>

                {/* Flight Hours */}
                <div className="col-12 col-md-6">
                  <label className="form-label fw-semibold small">Accumulated Flight Hours</label>
                  <input
                    type="number"
                    min="0"
                    className={`form-control ${errors.flight_hours ? 'is-invalid' : ''}`}
                    value={formData.flight_hours}
                    onChange={e => setFormData({ ...formData, flight_hours: e.target.value })}
                  />
                  {errors.flight_hours && (
                    <div className="invalid-feedback">{errors.flight_hours}</div>
                  )}
                </div>

                {/* Operational Status */}
                <div className="col-12">
                  <label className="form-label fw-semibold small">Operational Status</label>
                  <select
                    className="form-select"
                    value={formData.status}
                    onChange={e => setFormData({ ...formData, status: e.target.value })}
                  >
                    <option value="OPERATIONAL">OPERATIONAL - Available for flight rotations</option>
                    <option value="UNDER_MAINTENANCE">UNDER_MAINTENANCE - Hangar bay check underway</option>
                    <option value="ATTENTION_REQUIRED">ATTENTION_REQUIRED - Prognostic warning active</option>
                    <option value="RETIRED">RETIRED - Decommissioned airframe</option>
                  </select>
                </div>

                {/* Submit Actions */}
                <div className="col-12 pt-3 border-top mt-3 d-flex gap-2 justify-content-end">
                  <Link to="/aircraft" className="btn btn-outline-secondary">
                    Cancel
                  </Link>
                  <button
                    type="submit"
                    className="btn btn-primary d-inline-flex align-items-center gap-2"
                    disabled={isSubmitting}
                  >
                    <Save size={16} />
                    <span>{isSubmitting ? 'Saving to Database...' : 'Save Aircraft'}</span>
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>

        {/* Informational Guidance Panel */}
        <div className="col-12 col-lg-4 mt-3 mt-lg-0">
          <div className="aerocard">
            <h6 className="fw-bold mb-3 d-flex align-items-center gap-2">
              <AlertCircle size={18} className="text-primary" />
              <span>Data Validation Standards</span>
            </h6>
            <p className="text-secondary small mb-3">
              Fleet integrity standards enforced during registration:
            </p>
            <ul className="text-secondary small ps-3 mb-0">
              <li className="mb-2"><strong>Uniqueness:</strong> Registration numbers must be unique across the fleet registry.</li>
              <li className="mb-2"><strong>C-MAPSS Isolation:</strong> Each turbofan unit (1–100) must be uniquely allocated to prevent cross-engine telemetry collisions.</li>
              <li className="mb-2"><strong>Flight Metrics:</strong> Operating cycles and accumulated hours validate as non-negative integer thresholds.</li>
              <li><strong>Integrity:</strong> Deleting an aircraft will automatically clear associated telemetry records and alerts.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
