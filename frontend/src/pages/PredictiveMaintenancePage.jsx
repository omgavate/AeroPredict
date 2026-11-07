import React, { useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  Cpu,
  RefreshCw,
  AlertTriangle,
  ShieldAlert,
  CheckCircle,
  FileText,
  Clock,
  Sparkles,
  ArrowRight
} from 'lucide-react';
import RulGauge from '../components/RulGauge';
import StatusBadge from '../components/StatusBadge';
import {
  MOCK_AIRCRAFT,
  MOCK_RUL_PREDICTION,
  MOCK_PREDICTION_HISTORY
} from '../data/mockData';

export default function PredictiveMaintenancePage() {
  const [searchParams] = useSearchParams();
  const initialId = searchParams.get('id') || '1';
  const initialTail = searchParams.get('tail') || 'N101AP';

  const [selectedAircraftId, setSelectedAircraftId] = useState(initialId);
  const [prediction, setPrediction] = useState(MOCK_RUL_PREDICTION);
  const [history, setHistory] = useState(MOCK_PREDICTION_HISTORY);
  const [isInferring, setIsInferring] = useState(false);
  const [inferenceNotice, setInferenceNotice] = useState(null);

  // Simulated AI Inference Trigger
  const handleRunInference = () => {
    setIsInferring(true);
    setInferenceNotice(null);

    setTimeout(() => {
      setIsInferring(false);
      const simulatedRul = Math.max(2.5, (prediction.predicted_rul - 0.8)).toFixed(1);
      const nextCycle = prediction.cycle + 1;

      const newPrediction = {
        ...prediction,
        cycle: nextCycle,
        predicted_rul: parseFloat(simulatedRul),
        risk_level: parseFloat(simulatedRul) <= 10 ? 'CRITICAL' : 'HIGH',
        predicted_at: new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC'
      };

      setPrediction(newPrediction);
      setHistory(prev => [
        {
          id: prev.length + 105,
          cycle: nextCycle,
          predicted_rul: parseFloat(simulatedRul),
          risk_level: newPrediction.risk_level,
          date: '2026-11-07'
        },
        ...prev
      ]);

      setInferenceNotice('Random Forest regressor evaluated latest sensor telemetry successfully.');
      setTimeout(() => setInferenceNotice(null), 3500);
    }, 700);
  };

  return (
    <div>
      <div className="demo-banner">
        <span>✈️ <strong>Module 4:</strong> AI Remaining Useful Life (RUL) Inference Interface</span>
        <span className="badge bg-white text-primary">Model: Random Forest Regressor (FD001)</span>
      </div>

      {inferenceNotice && (
        <div className="alert alert-success d-flex align-items-center gap-2 py-2 mb-3">
          <CheckCircle size={16} />
          <span>{inferenceNotice}</span>
        </div>
      )}

      {/* Header and Aircraft Selector */}
      <div className="d-flex align-items-center justify-content-between mb-4 flex-wrap gap-3">
        <div>
          <h4 className="fw-bold text-dark mb-1">Turbofan Predictive Maintenance (RUL)</h4>
          <p className="text-secondary small mb-0">
            Machine-learned prognostic horizon forecasting based on NASA C-MAPSS degradation features.
          </p>
        </div>

        <div className="d-flex align-items-center gap-2">
          <select
            className="form-select form-select-sm"
            style={{ width: 180 }}
            value={selectedAircraftId}
            onChange={e => setSelectedAircraftId(e.target.value)}
          >
            {MOCK_AIRCRAFT.map(a => (
              <option key={a.id} value={a.id}>
                {a.tail_number} ({a.model})
              </option>
            ))}
          </select>

          <button
            className="btn btn-sm btn-primary d-inline-flex align-items-center gap-2"
            onClick={handleRunInference}
            disabled={isInferring}
          >
            {isInferring ? <RefreshCw size={15} className="spinner-border spinner-border-sm" /> : <Sparkles size={15} />}
            <span>{isInferring ? 'Evaluating Telemetry...' : 'Run RUL Prediction'}</span>
          </button>
        </div>
      </div>

      {/* Main Prediction & Risk View */}
      <div className="row g-4 mb-4">
        {/* RUL Gauge Card */}
        <div className="col-12 col-lg-5">
          <div className="aerocard h-100 text-center d-flex flex-column justify-content-between">
            <div>
              <div className="d-flex justify-content-between align-items-center mb-3 pb-2 border-bottom">
                <span className="fw-bold text-dark">RUL Forecast Gauge</span>
                <span className="badge bg-light text-dark border">
                  Target: {prediction.tail_number}
                </span>
              </div>
              <RulGauge
                rul={prediction.predicted_rul}
                maxRul={125}
                cycle={prediction.cycle}
              />
            </div>

            <div className="p-3 rounded bg-light border text-start mt-3">
              <div className="d-flex justify-content-between small mb-1">
                <span className="text-muted">Prediction Timestamp:</span>
                <span className="fw-mono text-dark">{prediction.predicted_at}</span>
              </div>
              <div className="d-flex justify-content-between small">
                <span className="text-muted">Confidence Interval:</span>
                <span className="fw-bold text-primary">{prediction.confidence_interval}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Risk Classification & Actionable Recommendations */}
        <div className="col-12 col-lg-7">
          <div className="aerocard h-100">
            <div className="d-flex justify-content-between align-items-center mb-3 pb-2 border-bottom">
              <div>
                <h6 className="fw-bold mb-0">Maintenance Risk Triage & Recommendation</h6>
                <small className="text-muted">Automated engineering prescription</small>
              </div>
              <StatusBadge status={prediction.risk_level} type="risk" />
            </div>

            {/* Prescribed Action Banner */}
            <div
              className="p-3 rounded mb-3"
              style={{
                backgroundColor: prediction.risk_level === 'CRITICAL' ? '#FEF2F2' : '#FFFBEB',
                border: `1px solid ${prediction.risk_level === 'CRITICAL' ? '#FECDD3' : '#FDE68A'}`
              }}
            >
              <div className="d-flex align-items-start gap-2">
                <ShieldAlert
                  size={22}
                  className={prediction.risk_level === 'CRITICAL' ? 'text-danger' : 'text-warning'}
                />
                <div>
                  <div className="fw-bold text-dark mb-1">
                    {prediction.action_required}
                  </div>
                  <p className="mb-0 text-dark small">
                    {prediction.recommendation}
                  </p>
                </div>
              </div>
            </div>

            {/* Degradation Symptom Checklist */}
            <div className="mb-3">
              <div className="small fw-bold text-uppercase text-secondary mb-2" style={{ fontSize: '0.75rem' }}>
                Observed Physical Degradation Indicators
              </div>
              <ul className="list-group list-group-flush small">
                <li className="list-group-item d-flex justify-content-between align-items-center px-0 py-2">
                  <span>High-Pressure Compressor (HPC) Outlet Temperature (T30)</span>
                  <span className="badge bg-danger-subtle text-danger">+28.5°R above nominal</span>
                </li>
                <li className="list-group-item d-flex justify-content-between align-items-center px-0 py-2">
                  <span>HPC Static Pressure (Ps30)</span>
                  <span className="badge bg-warning-subtle text-warning-emphasis">Diverging (-3.8 psia)</span>
                </li>
                <li className="list-group-item d-flex justify-content-between align-items-center px-0 py-2">
                  <span>Bleed Enthalpy (htBleed)</span>
                  <span className="badge bg-danger-subtle text-danger">Stage bleed leakage</span>
                </li>
              </ul>
            </div>

            <div className="pt-3 border-top d-flex justify-content-end gap-2">
              <Link to="/maintenance" className="btn btn-sm btn-outline-danger d-inline-flex align-items-center gap-1">
                <span>Create Maintenance Work Order</span>
                <ArrowRight size={14} />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Prediction History Table */}
      <div className="aerocard">
        <div className="d-flex justify-content-between align-items-center mb-3 pb-2 border-bottom">
          <div>
            <h6 className="fw-bold mb-0">RUL Prediction Tracking History</h6>
            <small className="text-muted">Recorded inferences as flight cycles accumulated for {prediction.tail_number}</small>
          </div>
          <span className="badge bg-light text-secondary border">{history.length} Inferences Logged</span>
        </div>

        <div className="table-responsive">
          <table className="aero-table">
            <thead>
              <tr>
                <th>Record ID</th>
                <th>Flight Cycle</th>
                <th>Predicted RUL</th>
                <th>Assessed Risk Category</th>
                <th>Inference Date</th>
                <th>Prognosis Status</th>
              </tr>
            </thead>
            <tbody>
              {history.map(item => (
                <tr key={item.id}>
                  <td className="text-muted small">#RUL-{item.id}</td>
                  <td className="fw-mono fw-bold">Cycle {item.cycle}</td>
                  <td className="fw-mono fw-bold text-dark">{item.predicted_rul.toFixed(1)} Cycles</td>
                  <td>
                    <StatusBadge status={item.risk_level} type="risk" />
                  </td>
                  <td className="text-secondary small">{item.date}</td>
                  <td>
                    <span className="badge bg-light text-dark border">
                      Logged in DB
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
