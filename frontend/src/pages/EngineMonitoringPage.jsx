import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Activity,
  Play,
  RotateCcw,
  Gauge,
  Thermometer,
  Wind,
  Flame,
  CheckCircle,
  AlertTriangle,
  Info
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
import {
  MOCK_AIRCRAFT,
  MOCK_TELEMETRY_SERIES,
  MOCK_LATEST_SENSORS
} from '../data/mockData';

export default function EngineMonitoringPage() {
  const [searchParams] = useSearchParams();
  const initialUnit = searchParams.get('unit') || '1';
  const initialTail = searchParams.get('tail') || 'N101AP';

  const [selectedUnit, setSelectedUnit] = useState(initialUnit);
  const [telemetryData, setTelemetryData] = useState(MOCK_TELEMETRY_SERIES);
  const [latestSensors, setLatestSensors] = useState(MOCK_LATEST_SENSORS);
  const [activeChart, setActiveChart] = useState('temperature'); // temperature | pressure | speed
  const [simulationToast, setSimulationToast] = useState(null);

  // Simulate advancing flight cycle
  const handleSimulateCycle = () => {
    const nextCycle = latestSensors.cycle + 1;
    const deltaT = (Math.random() * 0.8 + 0.3).toFixed(2);
    const newT30 = parseFloat((latestSensors.sensor_3 + parseFloat(deltaT)).toFixed(2));
    const newT50 = parseFloat((latestSensors.sensor_4 + parseFloat(deltaT) * 0.7).toFixed(2));
    const newP30 = parseFloat((latestSensors.sensor_7 - 0.15).toFixed(2));
    const newNc = parseFloat((latestSensors.sensor_9 + 1.2).toFixed(2));
    const newBpr = parseFloat((latestSensors.sensor_15 + 0.003).toFixed(3));

    const updatedLatest = {
      ...latestSensors,
      cycle: nextCycle,
      sensor_3: newT30,
      sensor_4: newT50,
      sensor_7: newP30,
      sensor_9: newNc,
      sensor_15: newBpr
    };

    setLatestSensors(updatedLatest);
    setTelemetryData(prev => [
      ...prev,
      {
        cycle: nextCycle,
        t30: newT30,
        t50: newT50,
        p30: newP30,
        nc: newNc,
        bpr: newBpr,
        htBleed: 398,
        rul: Math.max(0, 198 - nextCycle)
      }
    ]);

    setSimulationToast(`Simulated Cycle ${nextCycle} telemetry successfully ingested.`);
    setTimeout(() => setSimulationToast(null), 3000);
  };

  return (
    <div>
      <div className="demo-banner">
        <span>✈️ <strong>Module 3:</strong> Turbofan Multi-Sensor Telemetry & Health Monitoring</span>
        <span className="badge bg-white text-primary">NASA C-MAPSS FD001 Telemetry Stream</span>
      </div>

      {simulationToast && (
        <div className="alert alert-info py-2 d-flex align-items-center gap-2 mb-3">
          <Activity size={16} />
          <span>{simulationToast}</span>
        </div>
      )}

      {/* Top Controls Bar */}
      <div className="d-flex align-items-center justify-content-between mb-4 flex-wrap gap-3">
        <div>
          <h4 className="fw-bold text-dark mb-1">Engine Sensor Health & Telemetry</h4>
          <p className="text-secondary small mb-0">
            Real-time multi-channel sensor ingestion, thermal margins and thermodynamic cycle tracking.
          </p>
        </div>

        <div className="d-flex align-items-center gap-2 flex-wrap">
          {/* Unit Selector */}
          <div className="d-flex align-items-center gap-2">
            <span className="small fw-semibold text-secondary">Aircraft Unit:</span>
            <select
              className="form-select form-select-sm"
              style={{ width: 170 }}
              value={selectedUnit}
              onChange={e => setSelectedUnit(e.target.value)}
            >
              {MOCK_AIRCRAFT.map(a => (
                <option key={a.id} value={a.cmapss_unit_id}>
                  {a.tail_number} (Unit #{a.cmapss_unit_id})
                </option>
              ))}
            </select>
          </div>

          {/* Simulate Next Cycle Button */}
          <button
            className="btn btn-sm btn-primary d-inline-flex align-items-center gap-2"
            onClick={handleSimulateCycle}
          >
            <Play size={15} />
            <span>Simulate Next Cycle (+1)</span>
          </button>
        </div>
      </div>

      {/* Cycle & Core Telemetry Metrics Bar */}
      <div className="row g-3 mb-4">
        <div className="col-6 col-md-3">
          <div className="aerocard p-3 text-center">
            <div className="small text-secondary mb-1">Current Operating Cycle</div>
            <div className="h3 fw-bold text-dark mb-0 fw-mono">
              Cycle {latestSensors.cycle}
            </div>
            <span className="badge bg-primary-subtle text-primary mt-1">C-MAPSS Telemetry</span>
          </div>
        </div>

        <div className="col-6 col-md-3">
          <div className="aerocard p-3 text-center">
            <div className="small text-secondary mb-1">HPC Outlet Temp (T30)</div>
            <div className="h3 fw-bold text-danger mb-0 fw-mono">
              {latestSensors.sensor_3}°R
            </div>
            <span className="badge bg-danger-subtle text-danger mt-1">Thermal Degradation</span>
          </div>
        </div>

        <div className="col-6 col-md-3">
          <div className="aerocard p-3 text-center">
            <div className="small text-secondary mb-1">HPC Outlet Pressure (P30)</div>
            <div className="h3 fw-bold text-warning mb-0 fw-mono">
              {latestSensors.sensor_7} psia
            </div>
            <span className="badge bg-warning-subtle text-warning mt-1">Tip Clearance Loss</span>
          </div>
        </div>

        <div className="col-6 col-md-3">
          <div className="aerocard p-3 text-center">
            <div className="small text-secondary mb-1">Core Speed (Nc)</div>
            <div className="h3 fw-bold text-primary mb-0 fw-mono">
              {latestSensors.sensor_9} rpm
            </div>
            <span className="badge bg-success-subtle text-success mt-1">Speed Governed</span>
          </div>
        </div>
      </div>

      {/* Sensor Trend Charts (Recharts) */}
      <div className="aerocard mb-4">
        <div className="d-flex align-items-center justify-content-between mb-3 pb-2 border-bottom flex-wrap gap-2">
          <div>
            <h6 className="fw-bold mb-0">Multi-Cycle Telemetry Degradation Curves</h6>
            <small className="text-muted">Tracking critical thermodynamic parameters against cycle count</small>
          </div>

          {/* Chart View Selector */}
          <div className="btn-group btn-group-sm" role="group">
            <button
              type="button"
              className={`btn ${activeChart === 'temperature' ? 'btn-primary' : 'btn-outline-secondary'}`}
              onClick={() => setActiveChart('temperature')}
            >
              Temperatures (T30, T50)
            </button>
            <button
              type="button"
              className={`btn ${activeChart === 'pressure' ? 'btn-primary' : 'btn-outline-secondary'}`}
              onClick={() => setActiveChart('pressure')}
            >
              Compressor Pressure (P30)
            </button>
            <button
              type="button"
              className={`btn ${activeChart === 'speed' ? 'btn-primary' : 'btn-outline-secondary'}`}
              onClick={() => setActiveChart('speed')}
            >
              Core Speed & Bypass (Nc, BPR)
            </button>
          </div>
        </div>

        {/* Recharts Container */}
        <div style={{ width: '100%', height: 320 }}>
          <ResponsiveContainer width="100%" height="100%">
            {activeChart === 'temperature' ? (
              <LineChart data={telemetryData} margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="cycle" label={{ value: 'Engine Cycles', position: 'insideBottomRight', offset: -5 }} />
                <YAxis domain={['auto', 'auto']} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', color: '#FFF', borderRadius: 8, border: 'none' }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="t30"
                  name="T30 - HPC Outlet Temp (°R)"
                  stroke="#EF4444"
                  strokeWidth={2.5}
                  dot={{ r: 3 }}
                  activeDot={{ r: 6 }}
                />
                <Line
                  type="monotone"
                  dataKey="t50"
                  name="T50 - LPT Outlet Temp (°R)"
                  stroke="#F59E0B"
                  strokeWidth={2}
                  dot={{ r: 2 }}
                />
              </LineChart>
            ) : activeChart === 'pressure' ? (
              <LineChart data={telemetryData} margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="cycle" label={{ value: 'Engine Cycles', position: 'insideBottomRight', offset: -5 }} />
                <YAxis domain={['auto', 'auto']} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', color: '#FFF', borderRadius: 8, border: 'none' }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="p30"
                  name="P30 - HPC Static Pressure (psia)"
                  stroke="#3B82F6"
                  strokeWidth={2.5}
                  dot={{ r: 3 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            ) : (
              <LineChart data={telemetryData} margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="cycle" label={{ value: 'Engine Cycles', position: 'insideBottomRight', offset: -5 }} />
                <YAxis domain={['auto', 'auto']} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', color: '#FFF', borderRadius: 8, border: 'none' }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="nc"
                  name="Nc - Physical Core Speed (rpm)"
                  stroke="#10B981"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
                <Line
                  type="monotone"
                  dataKey="bpr"
                  name="BPR - Bypass Ratio"
                  stroke="#8B5CF6"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            )}
          </ResponsiveContainer>
        </div>
      </div>

      {/* Complete 21 C-MAPSS Sensor Telemetry Grid */}
      <div className="aerocard">
        <div className="d-flex align-items-center justify-content-between mb-3 pb-2 border-bottom">
          <h6 className="fw-bold mb-0">Active Telemetry Channels (21 Sensors + 3 Settings)</h6>
          <span className="badge bg-light text-secondary border">Snapshot at Cycle {latestSensors.cycle}</span>
        </div>

        <div className="row g-2">
          {/* Key Sensor Tiles */}
          <div className="col-6 col-sm-4 col-md-3 col-lg-2">
            <div className="p-2 rounded bg-light border text-center">
              <div className="text-muted small" style={{ fontSize: '0.72rem' }}>Sensor 1 (T2)</div>
              <div className="fw-bold fw-mono">{latestSensors.sensor_1}°R</div>
              <div className="text-secondary" style={{ fontSize: '0.68rem' }}>Fan Inlet Temp</div>
            </div>
          </div>

          <div className="col-6 col-sm-4 col-md-3 col-lg-2">
            <div className="p-2 rounded bg-light border text-center">
              <div className="text-muted small" style={{ fontSize: '0.72rem' }}>Sensor 2 (T24)</div>
              <div className="fw-bold fw-mono">{latestSensors.sensor_2}°R</div>
              <div className="text-secondary" style={{ fontSize: '0.68rem' }}>LPC Outlet Temp</div>
            </div>
          </div>

          <div className="col-6 col-sm-4 col-md-3 col-lg-2">
            <div className="p-2 rounded bg-danger-subtle border border-danger-subtle text-center">
              <div className="text-danger small fw-semibold" style={{ fontSize: '0.72rem' }}>Sensor 3 (T30)</div>
              <div className="fw-bold fw-mono text-danger">{latestSensors.sensor_3}°R</div>
              <div className="text-danger" style={{ fontSize: '0.68rem' }}>HPC Outlet Temp</div>
            </div>
          </div>

          <div className="col-6 col-sm-4 col-md-3 col-lg-2">
            <div className="p-2 rounded bg-warning-subtle border border-warning-subtle text-center">
              <div className="text-warning-emphasis small fw-semibold" style={{ fontSize: '0.72rem' }}>Sensor 4 (T50)</div>
              <div className="fw-bold fw-mono text-warning-emphasis">{latestSensors.sensor_4}°R</div>
              <div className="text-secondary" style={{ fontSize: '0.68rem' }}>LPT Outlet Temp</div>
            </div>
          </div>

          <div className="col-6 col-sm-4 col-md-3 col-lg-2">
            <div className="p-2 rounded bg-light border text-center">
              <div className="text-muted small" style={{ fontSize: '0.72rem' }}>Sensor 7 (P30)</div>
              <div className="fw-bold fw-mono">{latestSensors.sensor_7} psia</div>
              <div className="text-secondary" style={{ fontSize: '0.68rem' }}>HPC Outlet Press</div>
            </div>
          </div>

          <div className="col-6 col-sm-4 col-md-3 col-lg-2">
            <div className="p-2 rounded bg-light border text-center">
              <div className="text-muted small" style={{ fontSize: '0.72rem' }}>Sensor 8 (Nf)</div>
              <div className="fw-bold fw-mono">{latestSensors.sensor_8} rpm</div>
              <div className="text-secondary" style={{ fontSize: '0.68rem' }}>Fan Speed</div>
            </div>
          </div>

          <div className="col-6 col-sm-4 col-md-3 col-lg-2">
            <div className="p-2 rounded bg-light border text-center">
              <div className="text-muted small" style={{ fontSize: '0.72rem' }}>Sensor 9 (Nc)</div>
              <div className="fw-bold fw-mono">{latestSensors.sensor_9} rpm</div>
              <div className="text-secondary" style={{ fontSize: '0.68rem' }}>Core Speed</div>
            </div>
          </div>

          <div className="col-6 col-sm-4 col-md-3 col-lg-2">
            <div className="p-2 rounded bg-light border text-center">
              <div className="text-muted small" style={{ fontSize: '0.72rem' }}>Sensor 11 (Ps30)</div>
              <div className="fw-bold fw-mono">{latestSensors.sensor_11} psia</div>
              <div className="text-secondary" style={{ fontSize: '0.68rem' }}>Static Pressure</div>
            </div>
          </div>

          <div className="col-6 col-sm-4 col-md-3 col-lg-2">
            <div className="p-2 rounded bg-light border text-center">
              <div className="text-muted small" style={{ fontSize: '0.72rem' }}>Sensor 12 (phi)</div>
              <div className="fw-bold fw-mono">{latestSensors.sensor_12}</div>
              <div className="text-secondary" style={{ fontSize: '0.68rem' }}>Fuel Flow Ratio</div>
            </div>
          </div>

          <div className="col-6 col-sm-4 col-md-3 col-lg-2">
            <div className="p-2 rounded bg-light border text-center">
              <div className="text-muted small" style={{ fontSize: '0.72rem' }}>Sensor 15 (BPR)</div>
              <div className="fw-bold fw-mono">{latestSensors.sensor_15}</div>
              <div className="text-secondary" style={{ fontSize: '0.68rem' }}>Bypass Ratio</div>
            </div>
          </div>

          <div className="col-6 col-sm-4 col-md-3 col-lg-2">
            <div className="p-2 rounded bg-light border text-center">
              <div className="text-muted small" style={{ fontSize: '0.72rem' }}>Sensor 17 (htBleed)</div>
              <div className="fw-bold fw-mono">{latestSensors.sensor_17}</div>
              <div className="text-secondary" style={{ fontSize: '0.68rem' }}>Bleed Enthalpy</div>
            </div>
          </div>

          <div className="col-6 col-sm-4 col-md-3 col-lg-2">
            <div className="p-2 rounded bg-light border text-center">
              <div className="text-muted small" style={{ fontSize: '0.72rem' }}>Sensor 20 (W31)</div>
              <div className="fw-bold fw-mono">{latestSensors.sensor_20}</div>
              <div className="text-secondary" style={{ fontSize: '0.68rem' }}>HPT Coolant Bleed</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
