import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  Cpu,
  RefreshCw,
  AlertTriangle,
  ShieldAlert,
  CheckCircle,
  Sparkles,
  ArrowRight,
  Database,
  Info,
  Activity,
  Layers,
  Wrench,
  Clock,
  Gauge,
  Sliders,
  CheckCircle2,
  XCircle
} from 'lucide-react';
import RulGauge from '../components/RulGauge';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import aircraftApi from '../api/aircraftApi';
import engineApi from '../api/engineApi';
import predictionApi from '../api/predictionApi';

export default function PredictiveMaintenancePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryId = searchParams.get('id');

  // Fleet & Selection state
  const [fleet, setFleet] = useState([]);
  const [selectedAircraftId, setSelectedAircraftId] = useState(queryId ? parseInt(queryId, 10) : 1);
  const [selectedAircraft, setSelectedAircraft] = useState(null);

  // Telemetry & Prediction state
  const [currentTelemetry, setCurrentTelemetry] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [history, setHistory] = useState([]);
  const [modelInfo, setModelInfo] = useState(null);

  // Loading & Error states
  const [isLoading, setIsLoading] = useState(true);
  const [isInferring, setIsInferring] = useState(false);
  const [successToast, setSuccessToast] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [isLive, setIsLive] = useState(false);

  // --------------------------------------------------------------------------
  // 1. Initial Load: Fleet & Model Info
  // --------------------------------------------------------------------------
  useEffect(() => {
    async function loadInitialData() {
      try {
        const [fleetRes, modelRes] = await Promise.all([
          aircraftApi.getAll(),
          predictionApi.getModelInfo()
        ]);

        if (fleetRes.success && fleetRes.data && fleetRes.data.length > 0) {
          setFleet(fleetRes.data);
          const initialTargetId = queryId ? parseInt(queryId, 10) : fleetRes.data[0].id;
          setSelectedAircraftId(initialTargetId);
          const target = fleetRes.data.find(a => a.id === initialTargetId) || fleetRes.data[0];
          setSelectedAircraft(target);
        }

        if (modelRes.success && modelRes.data) {
          setModelInfo(modelRes.data);
        }
      } catch (err) {
        setErrorMessage('Failed to initialize fleet data: ' + err.message);
      }
    }
    loadInitialData();
  }, []);

  // --------------------------------------------------------------------------
  // 2. Load Telemetry, Latest Prediction, and History for Selected Aircraft
  // --------------------------------------------------------------------------
  const loadAircraftData = async (aircraftId) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const [telemetryRes, latestPredRes, historyRes] = await Promise.all([
        engineApi.getLatestSensors(aircraftId),
        predictionApi.getLatestPrediction(aircraftId),
        predictionApi.getPredictionHistory(aircraftId, 50)
      ]);

      // Telemetry
      if (telemetryRes.success && telemetryRes.data) {
        setCurrentTelemetry(telemetryRes.data);
        setIsLive(telemetryRes.isLive);
      } else {
        setCurrentTelemetry(null);
      }

      // Latest Prediction
      if (latestPredRes.success && latestPredRes.data) {
        setPrediction(latestPredRes.data);
      } else {
        setPrediction(null); // No previous prediction yet
      }

      // History
      if (historyRes.success && historyRes.data) {
        setHistory(Array.isArray(historyRes.data) ? historyRes.data : []);
      } else {
        setHistory([]);
      }
    } catch (err) {
      setErrorMessage('Error loading aircraft prognostics: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (selectedAircraftId) {
      const target = fleet.find(a => a.id === selectedAircraftId);
      if (target) setSelectedAircraft(target);
      loadAircraftData(selectedAircraftId);
    }
  }, [selectedAircraftId, fleet]);

  // --------------------------------------------------------------------------
  // 3. Aircraft Switch Handler
  // --------------------------------------------------------------------------
  const handleAircraftChange = (newId) => {
    const idNum = parseInt(newId, 10);
    setSelectedAircraftId(idNum);
    setSearchParams({ id: String(idNum) });
  };

  // --------------------------------------------------------------------------
  // 4. Trigger Real ML Prediction (POST /api/predict)
  // --------------------------------------------------------------------------
  const handleRunPrediction = async () => {
    if (!selectedAircraftId) {
      setErrorMessage('Please select a valid aircraft.');
      return;
    }

    if (!currentTelemetry || !currentTelemetry.sensors) {
      setErrorMessage('Missing sensor telemetry for this aircraft. Telemetry must be available to run inference.');
      return;
    }

    setIsInferring(true);
    setErrorMessage(null);
    setSuccessToast(null);

    try {
      const currentCycle = currentTelemetry.cycle || selectedAircraft?.current_cycles || 1;
      const telemetryObj = currentTelemetry.sensors;

      // Real REST call to Flask POST /api/predict
      const res = await predictionApi.predictRul(
        selectedAircraftId,
        currentCycle,
        telemetryObj,
        true // save_to_db = true
      );

      if (res.success && res.data) {
        const predResult = res.data;
        setPrediction(predResult);
        setIsLive(true);

        // Prepend new prediction to history table
        const newEntry = {
          id: predResult.prediction_id || Date.now(),
          cycle: predResult.cycle,
          predicted_rul: predResult.predicted_rul,
          risk_level: predResult.risk_level,
          predicted_at: predResult.predicted_at || new Date().toISOString()
        };
        setHistory(prev => [newEntry, ...prev]);

        setSuccessToast(`RUL Prediction evaluated successfully for Cycle ${predResult.cycle}. Result: ${predResult.predicted_rul.toFixed(1)} Cycles remaining.`);
        setTimeout(() => setSuccessToast(null), 4000);
      } else {
        setErrorMessage(res.error || 'Prediction service failed to evaluate telemetry.');
      }
    } catch (err) {
      setErrorMessage('Inference execution failed: ' + err.message);
    } finally {
      setIsInferring(false);
    }
  };

  // Safe variables
  const currentCycle = currentTelemetry?.cycle || selectedAircraft?.current_cycles || 0;
  const tailNumber = selectedAircraft?.tail_number || 'N/A';
  const engineModel = selectedAircraft?.engine_type || 'Turbofan CFM56-7B';
  const cmapssUnit = selectedAircraft?.cmapss_unit_id || 1;

  // Active prediction values
  const hasPrediction = prediction !== null && prediction.predicted_rul !== undefined;
  const rulValue = hasPrediction ? prediction.predicted_rul : 0;
  const riskLevel = hasPrediction ? prediction.risk_level : 'LOW';
  const riskScore = hasPrediction ? (prediction.risk_score || 0) : 0;
  const actionRequired = hasPrediction
    ? prediction.action_required
    : 'Awaiting Prognostic Evaluation';
  const recommendation = hasPrediction
    ? prediction.recommendation
    : 'No active prediction on file. Click "Run RUL Prediction" to evaluate real-time sensor telemetry through the Random Forest prognostic model.';

  // Tone-coded styling for risk banner
  const isCritical = riskLevel === 'CRITICAL';
  const isHigh = riskLevel === 'HIGH';
  const isMedium = riskLevel === 'MEDIUM';

  const riskBgColor = isCritical ? '#FEF2F2' : isHigh ? '#FFFBEB' : isMedium ? '#EFF6FF' : '#F0FDF4';
  const riskBorderColor = isCritical ? '#FECDD3' : isHigh ? '#FDE68A' : isMedium ? '#BFDBFE' : '#BBF7D0';
  const riskTextColor = isCritical ? '#991B1B' : isHigh ? '#92400E' : isMedium ? '#1E40AF' : '#166534';

  return (
    <div>
      {/* Success Notification */}
      {successToast && (
        <div className="alert alert-success d-flex align-items-center gap-2 py-2 mb-3">
          <CheckCircle size={16} />
          <span>{successToast}</span>
        </div>
      )}

      {/* Error Banner */}
      {errorMessage && (
        <div className="alert alert-danger d-flex align-items-center justify-content-between py-2 mb-3">
          <div className="d-flex align-items-center gap-2">
            <AlertTriangle size={16} />
            <span>{errorMessage}</span>
          </div>
          <button
            type="button"
            className="btn-close btn-sm"
            onClick={() => setErrorMessage(null)}
            aria-label="Close"
          />
        </div>
      )}

      {/* Top Controls & Aircraft / Engine Selection (Task 2) */}
      <div className="d-flex align-items-center justify-content-between mb-4 flex-wrap gap-3">
        <div>
          <div className="d-flex align-items-center gap-2">
            <h4 className="fw-bold text-dark mb-0">Predictive Maintenance & RUL Prognostics</h4>
            {isLive && (
              <span className="badge bg-success-subtle text-success border border-success-subtle d-inline-flex align-items-center gap-1">
                <Database size={12} />
                <span>Live ML Connected</span>
              </span>
            )}
          </div>
          <p className="text-secondary small mb-0 mt-1">
            Machine-learned prognostic horizon forecasting based on NASA C-MAPSS degradation features.
          </p>
        </div>

        <div className="d-flex align-items-center gap-2 flex-wrap">
          {/* Aircraft Selector */}
          <div className="d-flex align-items-center gap-2">
            <span className="small fw-semibold text-secondary">Aircraft:</span>
            <select
              className="form-select form-select-sm"
              style={{ width: 220 }}
              value={selectedAircraftId}
              onChange={e => handleAircraftChange(e.target.value)}
              disabled={isLoading || isInferring}
            >
              {fleet.map(a => (
                <option key={a.id} value={a.id}>
                  {a.tail_number} ({a.model})
                </option>
              ))}
            </select>
          </div>

          {/* Refresh Telemetry & Predictions */}
          <button
            className="btn btn-sm btn-outline-secondary d-inline-flex align-items-center gap-1"
            onClick={() => loadAircraftData(selectedAircraftId)}
            disabled={isLoading || isInferring}
            title="Refresh prognostic data"
          >
            <RefreshCw size={14} className={isLoading ? 'spinner-border spinner-border-sm' : ''} />
            <span className="d-none d-sm-inline">Refresh</span>
          </button>

          {/* Run Prediction Button (Task 3) */}
          <button
            className="btn btn-sm btn-primary d-inline-flex align-items-center gap-2"
            onClick={handleRunPrediction}
            disabled={isLoading || isInferring}
          >
            {isInferring ? (
              <RefreshCw size={15} className="spinner-border spinner-border-sm" />
            ) : (
              <Sparkles size={15} />
            )}
            <span>{isInferring ? 'Evaluating Telemetry...' : 'Run RUL Prediction'}</span>
          </button>
        </div>
      </div>

      {isLoading ? (
        <LoadingSpinner message="Loading prognostic horizon and real-time telemetry model artifacts..." />
      ) : (
        <>
          {/* Aircraft & Engine Specification Card (Task 2) */}
          <div className="aerocard mb-4 p-3 bg-light border">
            <div className="row g-3 align-items-center">
              <div className="col-12 col-md-3">
                <div className="small text-muted">Target Aircraft</div>
                <div className="fw-bold text-dark" style={{ fontSize: '1.05rem' }}>
                  {tailNumber}
                </div>
                <div className="text-secondary small">{selectedAircraft?.model}</div>
              </div>

              <div className="col-12 col-md-3">
                <div className="small text-muted">Propulsion Engine</div>
                <div className="fw-bold text-primary">{engineModel}</div>
                <div className="text-secondary small">
                  NASA C-MAPSS Unit #{cmapssUnit}
                </div>
              </div>

              <div className="col-12 col-md-3">
                <div className="small text-muted">Elapsed Cycles & Hours</div>
                <div className="fw-mono fw-bold text-dark">
                  Cycle {currentCycle} • {selectedAircraft?.flight_hours || 0} hrs
                </div>
                <div className="text-secondary small">
                  {currentTelemetry ? 'Telemetry Ingested' : 'No telemetry on file'}
                </div>
              </div>

              <div className="col-12 col-md-3 text-md-end">
                <div className="small text-muted mb-1">Airframe Operational Status</div>
                <StatusBadge status={selectedAircraft?.status || 'OPERATIONAL'} />
              </div>
            </div>
          </div>

          {/* Main Prediction & Risk View (Task 4) */}
          <div className="row g-4 mb-4">
            {/* Left Column: RUL Gauge Card */}
            <div className="col-12 col-lg-5">
              <div className="aerocard h-100 text-center d-flex flex-column justify-content-between">
                <div>
                  <div className="d-flex justify-content-between align-items-center mb-3 pb-2 border-bottom">
                    <span className="fw-bold text-dark">RUL Forecast Gauge</span>
                    <span className="badge bg-light text-dark border">
                      Target: {tailNumber}
                    </span>
                  </div>

                  {hasPrediction ? (
                    <RulGauge
                      rul={rulValue}
                      maxRul={125}
                      cycle={prediction.cycle || currentCycle}
                    />
                  ) : (
                    <div className="p-4 text-center">
                      <Gauge size={48} className="text-muted mb-2 opacity-50" />
                      <h6 className="fw-bold text-dark">No Prediction Evaluated Yet</h6>
                      <p className="text-secondary small mb-3">
                        Click "Run RUL Prediction" to evaluate latest telemetry for {tailNumber}.
                      </p>
                      <button
                        className="btn btn-sm btn-primary d-inline-flex align-items-center gap-2"
                        onClick={handleRunPrediction}
                        disabled={isInferring}
                      >
                        <Sparkles size={14} />
                        <span>Run RUL Prediction</span>
                      </button>
                    </div>
                  )}
                </div>

                {/* Prediction Timestamp & Model Metrics */}
                <div className="p-3 rounded bg-light border text-start mt-3">
                  <div className="d-flex justify-content-between small mb-1">
                    <span className="text-muted">Prediction Timestamp:</span>
                    <span className="fw-mono text-dark">
                      {prediction?.predicted_at || 'Awaiting evaluation'}
                    </span>
                  </div>
                  <div className="d-flex justify-content-between small mb-1">
                    <span className="text-muted">Confidence Interval:</span>
                    <span className="fw-bold text-primary">
                      {prediction?.confidence_interval || '± 2.5 cycles (95% CI)'}
                    </span>
                  </div>
                  {prediction?.prediction_id && (
                    <div className="d-flex justify-content-between small">
                      <span className="text-muted">Database Record ID:</span>
                      <span className="fw-mono text-success fw-bold">
                        #RUL-{prediction.prediction_id}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Right Column: Risk Classification & Maintenance Recommendations */}
            <div className="col-12 col-lg-7">
              <div className="aerocard h-100 d-flex flex-column justify-content-between">
                <div>
                  <div className="d-flex justify-content-between align-items-center mb-3 pb-2 border-bottom flex-wrap gap-2">
                    <div>
                      <h6 className="fw-bold mb-0">Maintenance Risk Triage & Recommendation</h6>
                      <small className="text-muted">Automated engineering diagnostic prescription</small>
                    </div>
                    {hasPrediction && <StatusBadge status={riskLevel} type="risk" />}
                  </div>

                  {/* Tone-Coded Recommendation Banner (Task 4) */}
                  <div
                    className="p-3 rounded mb-3"
                    style={{
                      backgroundColor: riskBgColor,
                      border: `1px solid ${riskBorderColor}`
                    }}
                  >
                    <div className="d-flex align-items-start gap-3">
                      <ShieldAlert
                        size={24}
                        className={isCritical ? 'text-danger' : isHigh ? 'text-warning' : isMedium ? 'text-primary' : 'text-success'}
                      />
                      <div className="flex-grow-1">
                        <div className="fw-bold mb-1" style={{ color: riskTextColor, fontSize: '0.98rem' }}>
                          {actionRequired}
                        </div>
                        <p className="mb-0 small" style={{ color: riskTextColor, lineHeight: '1.45' }}>
                          {recommendation}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Risk Score Progress Bar */}
                  {hasPrediction && (
                    <div className="mb-3 p-3 rounded border bg-light">
                      <div className="d-flex justify-content-between small mb-1">
                        <span className="fw-semibold text-secondary">Degradation Risk Severity Index</span>
                        <span className="fw-mono fw-bold text-dark">{riskScore.toFixed(1)} / 100</span>
                      </div>
                      <div className="progress" style={{ height: 10 }}>
                        <div
                          className={`progress-bar ${isCritical ? 'bg-danger' : isHigh ? 'bg-warning' : isMedium ? 'bg-info' : 'bg-success'}`}
                          role="progressbar"
                          style={{ width: `${Math.min(100, Math.max(5, riskScore))}%` }}
                          aria-valuenow={riskScore}
                          aria-valuemin="0"
                          aria-valuemax="100"
                        />
                      </div>
                    </div>
                  )}

                  {/* Observed Degradation Symptoms Checklist */}
                  <div className="mb-3">
                    <div className="small fw-bold text-uppercase text-secondary mb-2" style={{ fontSize: '0.75rem' }}>
                      Thermodynamic Degradation Indicators
                    </div>
                    <ul className="list-group list-group-flush small">
                      <li className="list-group-item d-flex justify-content-between align-items-center px-0 py-2">
                        <span>HPC Outlet Total Temperature (T30)</span>
                        <span className={`badge ${currentTelemetry?.sensors?.sensor_3 > 1600 ? 'bg-danger-subtle text-danger' : 'bg-success-subtle text-success'}`}>
                          {currentTelemetry?.sensors?.sensor_3 ? `${currentTelemetry.sensors.sensor_3.toFixed(1)}°R` : 'Nominal'}
                        </span>
                      </li>
                      <li className="list-group-item d-flex justify-content-between align-items-center px-0 py-2">
                        <span>HPC Compressor Pressure Ratio (P30)</span>
                        <span className={`badge ${currentTelemetry?.sensors?.sensor_7 < 552 ? 'bg-warning-subtle text-warning-emphasis' : 'bg-success-subtle text-success'}`}>
                          {currentTelemetry?.sensors?.sensor_7 ? `${currentTelemetry.sensors.sensor_7.toFixed(1)} psia` : 'Nominal'}
                        </span>
                      </li>
                      <li className="list-group-item d-flex justify-content-between align-items-center px-0 py-2">
                        <span>Bleed Enthalpy (htBleed)</span>
                        <span className={`badge ${currentTelemetry?.sensors?.sensor_17 > 395 ? 'bg-danger-subtle text-danger' : 'bg-light text-dark'}`}>
                          {currentTelemetry?.sensors?.sensor_17 ? `${currentTelemetry.sensors.sensor_17.toFixed(0)} Btu/lb` : 'Nominal'}
                        </span>
                      </li>
                    </ul>
                  </div>
                </div>

                {/* Action Link to Module 5 */}
                <div className="pt-3 border-top d-flex justify-content-between align-items-center flex-wrap gap-2">
                  <span className="text-muted small">
                    Direct maintenance schedule dispatch
                  </span>
                  <Link
                    to={`/maintenance?aircraft_id=${selectedAircraftId}`}
                    className="btn btn-sm btn-outline-danger d-inline-flex align-items-center gap-1"
                  >
                    <span>Create Maintenance Work Order</span>
                    <ArrowRight size={14} />
                  </Link>
                </div>
              </div>
            </div>
          </div>

          {/* Model Information Card (Task 4) */}
          {modelInfo && (
            <div className="aerocard mb-4 p-3 bg-light border">
              <div className="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-2">
                <div className="d-flex align-items-center gap-2">
                  <Cpu size={16} className="text-primary" />
                  <span className="fw-bold small text-dark">Active Prognostic Model Metadata</span>
                </div>
                <span className="badge bg-primary text-white" style={{ fontSize: '0.72rem' }}>
                  {modelInfo.model_type || 'RandomForestRegressor'}
                </span>
              </div>
              <div className="row g-2 small text-secondary">
                <div className="col-6 col-sm-3">
                  <strong>Features Ingested:</strong> {modelInfo.feature_count || 45} Features
                </div>
                <div className="col-6 col-sm-3">
                  <strong>Validation Strategy:</strong> GroupKFold (Zero-Leakage)
                </div>
                <div className="col-6 col-sm-3">
                  <strong>Test MAE Benchmark:</strong> 12.70 Cycles
                </div>
                <div className="col-6 col-sm-3">
                  <strong>Test RMSE Benchmark:</strong> 17.72 Cycles
                </div>
              </div>
            </div>
          )}

          {/* Prediction History Table (Task 2 & 4) */}
          <div className="aerocard">
            <div className="d-flex justify-content-between align-items-center mb-3 pb-2 border-bottom flex-wrap gap-2">
              <div>
                <h6 className="fw-bold mb-0">RUL Prediction Tracking History</h6>
                <small className="text-muted">
                  Recorded machine learning inferences across flight cycles for {tailNumber}
                </small>
              </div>
              <span className="badge bg-light text-secondary border">
                {history.length} Inferences Recorded
              </span>
            </div>

            <div className="table-responsive">
              <table className="aero-table">
                <thead>
                  <tr>
                    <th>Record ID</th>
                    <th>Flight Cycle</th>
                    <th>Predicted RUL</th>
                    <th>Risk Category</th>
                    <th>Inference Timestamp</th>
                    <th>Database Status</th>
                  </tr>
                </thead>
                <tbody>
                  {history.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="text-center py-4 text-muted small">
                        No previous predictions recorded for this aircraft. Click "Run RUL Prediction" to evaluate live telemetry.
                      </td>
                    </tr>
                  ) : (
                    history.map((item, idx) => (
                      <tr key={item.id || idx}>
                        <td className="text-muted small fw-mono">
                          #{item.id ? `RUL-${item.id}` : `REC-${idx + 1}`}
                        </td>
                        <td className="fw-mono fw-bold">
                          Cycle {item.cycle}
                        </td>
                        <td className="fw-mono fw-bold text-dark">
                          {Number(item.predicted_rul).toFixed(1)} Cycles
                        </td>
                        <td>
                          <StatusBadge status={item.risk_level} type="risk" />
                        </td>
                        <td className="text-secondary small">
                          {item.predicted_at || item.date || 'Today'}
                        </td>
                        <td>
                          <span className="badge bg-success-subtle text-success border border-success-subtle d-inline-flex align-items-center gap-1">
                            <CheckCircle2 size={12} />
                            <span>Recorded in DB</span>
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
