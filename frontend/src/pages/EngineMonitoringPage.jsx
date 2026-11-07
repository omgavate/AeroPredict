import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  Activity,
  Play,
  Gauge,
  Thermometer,
  Wind,
  Flame,
  CheckCircle,
  AlertTriangle,
  Info,
  RefreshCw,
  Cpu,
  Layers,
  ShieldCheck,
  TrendingUp,
  TrendingDown,
  Database
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import engineApi from '../api/engineApi';
import aircraftApi from '../api/aircraftApi';
import LoadingSpinner from '../components/LoadingSpinner';
import StatusBadge from '../components/StatusBadge';
import {
  MOCK_AIRCRAFT,
  MOCK_TELEMETRY_SERIES,
  MOCK_LATEST_SENSORS
} from '../data/mockData';

export default function EngineMonitoringPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryId = searchParams.get('id');
  const queryUnit = searchParams.get('unit');
  const queryTail = searchParams.get('tail');

  // Fleet list
  const [fleet, setFleet] = useState(MOCK_AIRCRAFT);
  const [selectedAircraftId, setSelectedAircraftId] = useState(queryId ? parseInt(queryId, 10) : 1);

  // Telemetry data states
  const [latestSensors, setLatestSensors] = useState(MOCK_LATEST_SENSORS);
  const [telemetryHistory, setTelemetryHistory] = useState(MOCK_TELEMETRY_SERIES);
  const [engineOverview, setEngineOverview] = useState(null);

  // UI interaction states
  const [activeChart, setActiveChart] = useState('temperature'); // temperature | pressure | speed | bleed
  const [isLoading, setIsLoading] = useState(true);
  const [isAdvancing, setIsAdvancing] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [isLive, setIsLive] = useState(false);

  // 1. Initial Fleet Load
  useEffect(() => {
    async function fetchFleet() {
      try {
        const res = await aircraftApi.getAll();
        if (res.success && res.data && res.data.length > 0) {
          setFleet(res.data);
          // If query param matches an aircraft by ID or unit, select it
          if (queryId) {
            const found = res.data.find(a => a.id === parseInt(queryId, 10));
            if (found) setSelectedAircraftId(found.id);
          } else if (queryUnit) {
            const found = res.data.find(a => a.cmapss_unit_id === parseInt(queryUnit, 10));
            if (found) setSelectedAircraftId(found.id);
          } else if (queryTail) {
            const found = res.data.find(a => a.tail_number === queryTail);
            if (found) setSelectedAircraftId(found.id);
          }
        }
      } catch (err) {
        console.warn('Fleet list fallback:', err.message);
      }
    }
    fetchFleet();
  }, [queryId, queryUnit, queryTail]);

  // 2. Fetch Telemetry for Selected Aircraft
  const loadTelemetry = async (aircraftId) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const [latestRes, historyRes, overviewRes] = await Promise.all([
        engineApi.getLatestSensors(aircraftId),
        engineApi.getSensorHistory(aircraftId, { limit: 50 }),
        engineApi.getEngineOverview(aircraftId)
      ]);

      if (latestRes.success && latestRes.data) {
        setLatestSensors(latestRes.data);
        setIsLive(latestRes.isLive);
      }

      if (historyRes.success && historyRes.data && historyRes.data.history) {
        setTelemetryHistory(historyRes.data.history);
      }

      if (overviewRes && overviewRes.success && overviewRes.data) {
        setEngineOverview(overviewRes.data);
      }
    } catch (err) {
      setErrorMessage('Failed to fetch engine telemetry: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (selectedAircraftId) {
      loadTelemetry(selectedAircraftId);
    }
  }, [selectedAircraftId]);

  // Handle Aircraft Selector Change
  const handleAircraftChange = (newId) => {
    const idNum = parseInt(newId, 10);
    setSelectedAircraftId(idNum);
    const target = fleet.find(a => a.id === idNum);
    if (target) {
      setSearchParams({
        id: String(target.id),
        unit: String(target.cmapss_unit_id || 1),
        tail: target.tail_number
      });
    }
  };

  // Advance Telemetry by +1 Cycle
  const handleAdvanceCycle = async () => {
    setIsAdvancing(true);
    setErrorMessage(null);
    try {
      const res = await engineApi.advanceCycle(selectedAircraftId);
      if (res.success && res.data) {
        const newReading = res.data;
        setLatestSensors(newReading);

        // Append to history
        const historyEntry = {
          cycle: newReading.cycle,
          t24: newReading.sensors.sensor_2,
          t30: newReading.sensors.sensor_3,
          t50: newReading.sensors.sensor_4,
          p30: newReading.sensors.sensor_7,
          nf: newReading.sensors.sensor_8,
          nc: newReading.sensors.sensor_9,
          ps30: newReading.sensors.sensor_11,
          bpr: newReading.sensors.sensor_15,
          htBleed: newReading.sensors.sensor_17,
          sensors: newReading.sensors
        };
        setTelemetryHistory(prev => [...prev.slice(-49), historyEntry]);

        setToastMessage(`Flight Cycle ${newReading.cycle} telemetry successfully recorded.`);
        setTimeout(() => setToastMessage(null), 3500);
      } else {
        setErrorMessage(res.error || 'Failed to advance cycle.');
      }
    } catch (err) {
      setErrorMessage('Error communicating with telemetry service: ' + err.message);
    } finally {
      setIsAdvancing(false);
    }
  };

  const selectedAircraft = fleet.find(a => a.id === selectedAircraftId) || fleet[0] || {};
  const sensorsObj = latestSensors.sensors || {};
  const currentCycle = latestSensors.cycle || selectedAircraft.current_cycles || 0;

  // Extract key metrics safely
  const t30Val = sensorsObj.sensor_3 || latestSensors.sensor_3 || 1589.0;
  const t50Val = sensorsObj.sensor_4 || latestSensors.sensor_4 || 1400.0;
  const p30Val = sensorsObj.sensor_7 || latestSensors.sensor_7 || 554.0;
  const ncVal = sensorsObj.sensor_9 || latestSensors.sensor_9 || 9046.0;
  const bprVal = sensorsObj.sensor_15 || latestSensors.sensor_15 || 8.42;
  const htBleedVal = sensorsObj.sensor_17 || latestSensors.sensor_17 || 392.0;

  // Health indicators
  const indicators = latestSensors.health_indicators || {};
  const t30Delta = indicators.t30_delta_r !== undefined ? indicators.t30_delta_r : (t30Val - 1589.0).toFixed(1);
  const p30Delta = indicators.p30_delta_psia !== undefined ? indicators.p30_delta_psia : (p30Val - 554.0).toFixed(1);

  return (
    <div>
      {/* Toast Notification */}
      {toastMessage && (
        <div className="alert alert-success py-2 d-flex align-items-center gap-2 mb-3">
          <CheckCircle size={16} />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Error Message */}
      {errorMessage && (
        <div className="alert alert-danger py-2 d-flex align-items-center gap-2 mb-3">
          <AlertTriangle size={16} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Header and Controls */}
      <div className="d-flex align-items-center justify-content-between mb-4 flex-wrap gap-3">
        <div>
          <div className="d-flex align-items-center gap-2">
            <h4 className="fw-bold text-dark mb-0">Engine Sensor Health & Telemetry</h4>
            {isLive && (
              <span className="badge bg-success-subtle text-success border border-success-subtle d-inline-flex align-items-center gap-1">
                <Database size={12} />
                <span>Live Stream</span>
              </span>
            )}
          </div>
          <p className="text-secondary small mb-0 mt-1">
            Real-time multi-channel sensor ingestion, thermal margins and thermodynamic cycle tracking.
          </p>
        </div>

        <div className="d-flex align-items-center gap-2 flex-wrap">
          {/* Aircraft Selector */}
          <div className="d-flex align-items-center gap-2">
            <span className="small fw-semibold text-secondary">Aircraft Unit:</span>
            <select
              className="form-select form-select-sm"
              style={{ width: 220 }}
              value={selectedAircraftId}
              onChange={e => handleAircraftChange(e.target.value)}
              disabled={isLoading || isAdvancing}
            >
              {fleet.map(a => (
                <option key={a.id} value={a.id}>
                  {a.tail_number} ({a.model}) • Unit #{a.cmapss_unit_id || 'N/A'}
                </option>
              ))}
            </select>
          </div>

          {/* Refresh Button */}
          <button
            className="btn btn-sm btn-outline-secondary d-inline-flex align-items-center gap-1"
            onClick={() => loadTelemetry(selectedAircraftId)}
            disabled={isLoading || isAdvancing}
            title="Reload telemetry from database"
          >
            <RefreshCw size={14} className={isLoading ? 'spinner-border spinner-border-sm' : ''} />
            <span className="d-none d-sm-inline">Refresh</span>
          </button>

          {/* Advance Flight Cycle Button */}
          <button
            className="btn btn-sm btn-primary d-inline-flex align-items-center gap-2"
            onClick={handleAdvanceCycle}
            disabled={isLoading || isAdvancing}
          >
            {isAdvancing ? (
              <RefreshCw size={15} className="spinner-border spinner-border-sm" />
            ) : (
              <Play size={15} />
            )}
            <span>{isAdvancing ? 'Ingesting Cycle...' : 'Advance Flight Cycle (+1)'}</span>
          </button>
        </div>
      </div>

      {isLoading ? (
        <LoadingSpinner message="Ingesting turbofan telemetry stream and thermodynamic health parameters..." />
      ) : (
        <>
          {/* Cycle & Core Telemetry Metrics Bar */}
          <div className="row g-3 mb-4">
            {/* Operating Cycle */}
            <div className="col-6 col-md-3">
              <div className="aerocard p-3 text-center h-100 d-flex flex-column justify-content-between">
                <div>
                  <div className="small text-secondary mb-1">Current Operating Cycle</div>
                  <div className="h3 fw-bold text-dark mb-0 fw-mono">
                    Cycle {currentCycle}
                  </div>
                </div>
                <div className="mt-2">
                  <span className="badge bg-primary-subtle text-primary">
                    Unit #{selectedAircraft.cmapss_unit_id || '1'} Telemetry
                  </span>
                </div>
              </div>
            </div>

            {/* HPC Outlet Temp */}
            <div className="col-6 col-md-3">
              <div className="aerocard p-3 text-center h-100 d-flex flex-column justify-content-between">
                <div>
                  <div className="small text-secondary mb-1">HPC Outlet Temp (T30)</div>
                  <div className="h3 fw-bold text-danger mb-0 fw-mono">
                    {Number(t30Val).toFixed(2)}°R
                  </div>
                </div>
                <div className="mt-2">
                  <span className={`badge ${Number(t30Delta) > 10 ? 'bg-danger-subtle text-danger' : 'bg-success-subtle text-success'}`}>
                    {Number(t30Delta) >= 0 ? `+${t30Delta}` : t30Delta}°R vs Nominal
                  </span>
                </div>
              </div>
            </div>

            {/* HPC Outlet Pressure */}
            <div className="col-6 col-md-3">
              <div className="aerocard p-3 text-center h-100 d-flex flex-column justify-content-between">
                <div>
                  <div className="small text-secondary mb-1">HPC Outlet Pressure (P30)</div>
                  <div className="h3 fw-bold text-warning-emphasis mb-0 fw-mono">
                    {Number(p30Val).toFixed(2)} psia
                  </div>
                </div>
                <div className="mt-2">
                  <span className={`badge ${Number(p30Delta) < -2 ? 'bg-warning-subtle text-warning-emphasis' : 'bg-success-subtle text-success'}`}>
                    {Number(p30Delta) >= 0 ? `+${p30Delta}` : p30Delta} psia Delta
                  </span>
                </div>
              </div>
            </div>

            {/* Physical Core Speed */}
            <div className="col-6 col-md-3">
              <div className="aerocard p-3 text-center h-100 d-flex flex-column justify-content-between">
                <div>
                  <div className="small text-secondary mb-1">Physical Core Speed (Nc)</div>
                  <div className="h3 fw-bold text-primary mb-0 fw-mono">
                    {Number(ncVal).toFixed(1)} rpm
                  </div>
                </div>
                <div className="mt-2">
                  <span className="badge bg-success-subtle text-success">
                    Nominal Governor Range
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Engine Subsystems Health Status (Task 4) */}
          {engineOverview && engineOverview.subsystems && (
            <div className="aerocard mb-4">
              <div className="d-flex align-items-center justify-content-between mb-3 pb-2 border-bottom flex-wrap gap-2">
                <div>
                  <h6 className="fw-bold mb-0">Thermodynamic Subsystems Health Overview</h6>
                  <small className="text-muted">Real-time status evaluated across thermodynamic gas path stages</small>
                </div>
                <span className="badge bg-light text-dark border">
                  Target: {selectedAircraft.tail_number} ({selectedAircraft.engine_type})
                </span>
              </div>

              <div className="row g-2">
                {Object.entries(engineOverview.subsystems).map(([subsystemName, info]) => {
                  const isDegraded = info.status === 'DEGRADED';
                  const isCritical = info.status === 'CRITICAL';
                  const badgeColor = isCritical ? '#EF4444' : isDegraded ? '#F59E0B' : '#10B981';
                  const bgColor = isCritical ? '#FEF2F2' : isDegraded ? '#FFFBEB' : '#F0FDF4';

                  return (
                    <div key={subsystemName} className="col-6 col-md-4 col-lg-3">
                      <div
                        className="p-2 rounded border"
                        style={{ backgroundColor: bgColor, borderColor: badgeColor }}
                      >
                        <div className="d-flex justify-content-between align-items-center mb-1">
                          <span className="fw-bold small text-dark">{subsystemName.replace('_', ' & ')}</span>
                          <span
                            className="badge"
                            style={{ backgroundColor: badgeColor, color: '#FFF', fontSize: '0.68rem' }}
                          >
                            {info.status}
                          </span>
                        </div>
                        <div className="text-secondary" style={{ fontSize: '0.72rem' }}>
                          Sensors: {info.sensors.join(', ')}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Sensor Trend Charts (Recharts) */}
          <div className="aerocard mb-4">
            <div className="d-flex align-items-center justify-content-between mb-3 pb-2 border-bottom flex-wrap gap-2">
              <div>
                <h6 className="fw-bold mb-0">Multi-Cycle Telemetry Degradation Curves</h6>
                <small className="text-muted">
                  Chronological progression across {telemetryHistory.length} recorded flight cycles
                </small>
              </div>

              {/* Chart Selector Tabs */}
              <div className="btn-group btn-group-sm" role="group">
                <button
                  type="button"
                  className={`btn ${activeChart === 'temperature' ? 'btn-primary' : 'btn-outline-secondary'}`}
                  onClick={() => setActiveChart('temperature')}
                >
                  Temperatures (T24, T30, T50)
                </button>
                <button
                  type="button"
                  className={`btn ${activeChart === 'pressure' ? 'btn-primary' : 'btn-outline-secondary'}`}
                  onClick={() => setActiveChart('pressure')}
                >
                  Pressures (P30, Ps30)
                </button>
                <button
                  type="button"
                  className={`btn ${activeChart === 'speed' ? 'btn-primary' : 'btn-outline-secondary'}`}
                  onClick={() => setActiveChart('speed')}
                >
                  Rotor Speeds & Bypass (Nc, Nf, BPR)
                </button>
                <button
                  type="button"
                  className={`btn ${activeChart === 'bleed' ? 'btn-primary' : 'btn-outline-secondary'}`}
                  onClick={() => setActiveChart('bleed')}
                >
                  Bleed Enthalpy & Flow (htBleed, W31)
                </button>
              </div>
            </div>

            {/* Recharts Chart */}
            <div style={{ width: '100%', height: 320 }}>
              <ResponsiveContainer width="100%" height="100%">
                {activeChart === 'temperature' ? (
                  <LineChart data={telemetryHistory} margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                    <XAxis dataKey="cycle" label={{ value: 'Flight Cycles', position: 'insideBottomRight', offset: -5 }} />
                    <YAxis domain={['auto', 'auto']} />
                    <Tooltip contentStyle={{ backgroundColor: '#0F172A', color: '#FFF', borderRadius: 8, border: 'none' }} />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="t30"
                      name="T30 - HPC Outlet Temp (°R)"
                      stroke="#EF4444"
                      strokeWidth={2.5}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="t50"
                      name="T50 - LPT Outlet Temp (°R)"
                      stroke="#F59E0B"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="t24"
                      name="T24 - LPC Outlet Temp (°R)"
                      stroke="#3B82F6"
                      strokeWidth={1.5}
                      dot={false}
                    />
                  </LineChart>
                ) : activeChart === 'pressure' ? (
                  <LineChart data={telemetryHistory} margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                    <XAxis dataKey="cycle" label={{ value: 'Flight Cycles', position: 'insideBottomRight', offset: -5 }} />
                    <YAxis domain={['auto', 'auto']} />
                    <Tooltip contentStyle={{ backgroundColor: '#0F172A', color: '#FFF', borderRadius: 8, border: 'none' }} />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="p30"
                      name="P30 - HPC Outlet Total Pressure (psia)"
                      stroke="#2563EB"
                      strokeWidth={2.5}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="ps30"
                      name="Ps30 - HPC Static Pressure (psia)"
                      stroke="#10B981"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                ) : activeChart === 'speed' ? (
                  <LineChart data={telemetryHistory} margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                    <XAxis dataKey="cycle" label={{ value: 'Flight Cycles', position: 'insideBottomRight', offset: -5 }} />
                    <YAxis domain={['auto', 'auto']} />
                    <Tooltip contentStyle={{ backgroundColor: '#0F172A', color: '#FFF', borderRadius: 8, border: 'none' }} />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="nc"
                      name="Nc - Physical Core Speed (rpm)"
                      stroke="#10B981"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="nf"
                      name="Nf - Physical Fan Speed (rpm)"
                      stroke="#6366F1"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="bpr"
                      name="BPR - Bypass Ratio"
                      stroke="#F97316"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                ) : (
                  <LineChart data={telemetryHistory} margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                    <XAxis dataKey="cycle" label={{ value: 'Flight Cycles', position: 'insideBottomRight', offset: -5 }} />
                    <YAxis domain={['auto', 'auto']} />
                    <Tooltip contentStyle={{ backgroundColor: '#0F172A', color: '#FFF', borderRadius: 8, border: 'none' }} />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="htBleed"
                      name="htBleed - Bleed Enthalpy (Btu/lb)"
                      stroke="#EC4899"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="w31"
                      name="W31 - HPT Coolant Bleed (lbm/s)"
                      stroke="#14B8A6"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                )}
              </ResponsiveContainer>
            </div>
          </div>

          {/* Full 21-Sensor Telemetry Matrix */}
          <div className="aerocard mb-4">
            <div className="d-flex align-items-center justify-content-between mb-3 pb-2 border-bottom flex-wrap gap-2">
              <div>
                <h6 className="fw-bold mb-0">Multi-Channel Sensor Telemetry Matrix (All 21 Channels)</h6>
                <small className="text-muted">
                  Ingested sensor values at Flight Cycle {currentCycle} with physical engineering units
                </small>
              </div>
              <span className="badge bg-light text-dark border">
                Sampled at: {latestSensors.recorded_at ? new Date(latestSensors.recorded_at).toLocaleTimeString() : 'Current Time'}
              </span>
            </div>

            <div className="row g-2">
              {Object.keys(sensorsObj).length > 0 ? (
                Array.from({ length: 21 }, (_, idx) => {
                  const sensorNum = idx + 1;
                  const key = `sensor_${sensorNum}`;
                  const val = sensorsObj[key];
                  const numVal = typeof val === 'number' ? val : parseFloat(val);

                  // Highlight degraded channels
                  const isDegradedChannel = (sensorNum === 3 && numVal > 1598) || (sensorNum === 4 && numVal > 1415);
                  const isWarningChannel = (sensorNum === 7 && numVal < 552) || (sensorNum === 17 && numVal > 395);

                  let cardClass = 'bg-light border';
                  let textColor = 'text-dark';
                  if (isDegradedChannel) {
                    cardClass = 'bg-danger-subtle border border-danger-subtle';
                    textColor = 'text-danger';
                  } else if (isWarningChannel) {
                    cardClass = 'bg-warning-subtle border border-warning-subtle';
                    textColor = 'text-warning-emphasis';
                  }

                  const labels = {
                    1: { name: 'T2', desc: 'Fan Inlet Temp', unit: '°R' },
                    2: { name: 'T24', desc: 'LPC Outlet Temp', unit: '°R' },
                    3: { name: 'T30', desc: 'HPC Outlet Temp', unit: '°R' },
                    4: { name: 'T50', desc: 'LPT Outlet Temp', unit: '°R' },
                    5: { name: 'P2', desc: 'Fan Inlet Press', unit: 'psia' },
                    6: { name: 'P15', desc: 'Bypass Press', unit: 'psia' },
                    7: { name: 'P30', desc: 'HPC Outlet Press', unit: 'psia' },
                    8: { name: 'Nf', desc: 'Fan Speed', unit: 'rpm' },
                    9: { name: 'Nc', desc: 'Core Speed', unit: 'rpm' },
                    10: { name: 'epr', desc: 'Engine Press Ratio', unit: '' },
                    11: { name: 'Ps30', desc: 'HPC Static Press', unit: 'psia' },
                    12: { name: 'phi', desc: 'Fuel Flow Ratio', unit: 'pps/psi' },
                    13: { name: 'NRf', desc: 'Corrected Fan Speed', unit: 'rpm' },
                    14: { name: 'NRc', desc: 'Corrected Core Speed', unit: 'rpm' },
                    15: { name: 'BPR', desc: 'Bypass Ratio', unit: '' },
                    16: { name: 'farB', desc: 'Fuel-Air Ratio', unit: '' },
                    17: { name: 'htBleed', desc: 'Bleed Enthalpy', unit: 'Btu/lb' },
                    18: { name: 'Nf_dmd', desc: 'Demanded Fan Speed', unit: 'rpm' },
                    19: { name: 'PCNfR_dmd', desc: 'Demanded Corrected Speed', unit: 'rpm' },
                    20: { name: 'W31', desc: 'HPT Coolant Bleed', unit: 'lbm/s' },
                    21: { name: 'W32', desc: 'LPT Coolant Bleed', unit: 'lbm/s' }
                  };

                  const meta = labels[sensorNum] || { name: `S${sensorNum}`, desc: 'Telemetry', unit: '' };

                  return (
                    <div key={key} className="col-6 col-sm-4 col-md-3 col-lg-2">
                      <div className={`p-2 rounded text-center ${cardClass}`}>
                        <div className="small fw-semibold" style={{ fontSize: '0.72rem' }}>
                          Sensor {sensorNum} ({meta.name})
                        </div>
                        <div className={`fw-bold fw-mono ${textColor}`} style={{ fontSize: '0.95rem' }}>
                          {!isNaN(numVal) ? numVal.toFixed(meta.unit === 'rpm' ? 1 : 2) : '—'}
                          {meta.unit ? ` ${meta.unit}` : ''}
                        </div>
                        <div className="text-secondary" style={{ fontSize: '0.68rem' }}>
                          {meta.desc}
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="text-center py-4 text-muted small">No sensor telemetry available.</div>
              )}
            </div>
          </div>

          {/* Engine Technical Profile & C-MAPSS Mapping Notice (Task 3) */}
          <div className="aerocard">
            <div className="row g-3">
              <div className="col-12 col-lg-7">
                <h6 className="fw-bold mb-2">Airframe & Propulsion Technical Profile</h6>
                <div className="row g-2 small text-secondary">
                  <div className="col-6 col-sm-4">
                    <strong>Tail Registration:</strong> {selectedAircraft.tail_number}
                  </div>
                  <div className="col-6 col-sm-4">
                    <strong>Aircraft Model:</strong> {selectedAircraft.model}
                  </div>
                  <div className="col-6 col-sm-4">
                    <strong>Manufacturer:</strong> {selectedAircraft.manufacturer}
                  </div>
                  <div className="col-6 col-sm-4">
                    <strong>Turbofan Model:</strong> {selectedAircraft.engine_type}
                  </div>
                  <div className="col-6 col-sm-4">
                    <strong>Flight Hours:</strong> {selectedAircraft.flight_hours || 0} hrs
                  </div>
                  <div className="col-6 col-sm-4">
                    <strong>C-MAPSS Unit Mapping:</strong> Unit #{selectedAircraft.cmapss_unit_id || 'N/A'}
                  </div>
                </div>
              </div>

              <div className="col-12 col-lg-5 border-start-lg pt-3 pt-lg-0">
                <div className="p-3 rounded bg-light border">
                  <div className="d-flex align-items-center gap-2 mb-1">
                    <Info size={16} className="text-primary" />
                    <span className="small fw-bold text-dark">NASA C-MAPSS Telemetry Integration</span>
                  </div>
                  <p className="text-secondary mb-0" style={{ fontSize: '0.75rem', lineHeight: '1.4' }}>
                    {latestSensors.mapping_notice || (
                      "Demonstration mapping: Aircraft assets in AeroPredict are linked to NASA C-MAPSS turbofan engine unit records (FD001) for real thermodynamic sensor telemetry stream simulation. Aircraft assets are operational representations and not physical NASA aircraft."
                    )}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
