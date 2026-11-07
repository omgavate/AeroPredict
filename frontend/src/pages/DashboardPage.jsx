import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Plane,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ArrowRight,
  ShieldAlert,
  Activity,
  Cpu,
  RefreshCw,
  Database
} from 'lucide-react';
import MetricCard from '../components/MetricCard';
import StatusBadge from '../components/StatusBadge';
import AlertCard from '../components/AlertCard';
import aircraftApi from '../api/aircraftApi';
import {
  MOCK_AIRCRAFT,
  MOCK_ALERTS
} from '../data/mockData';

export default function DashboardPage() {
  const [alerts, setAlerts] = useState(MOCK_ALERTS);
  const [fleet, setFleet] = useState(MOCK_AIRCRAFT);
  const [isLive, setIsLive] = useState(false);

  useEffect(() => {
    async function fetchFleet() {
      try {
        const res = await aircraftApi.getAll();
        if (res.success && res.data && res.data.length > 0) {
          setFleet(res.data);
          setIsLive(res.isLive);
        }
      } catch (err) {
        console.warn('Dashboard using fallback fleet data:', err.message);
      }
    }
    fetchFleet();
  }, []);

  const totalAircraft = fleet.length;
  const operationalAircraft = fleet.filter(a => a.status === 'OPERATIONAL').length;
  const inMaintenance = fleet.filter(a => a.status === 'UNDER_MAINTENANCE').length;
  const attentionRequired = fleet.filter(a => a.status === 'ATTENTION_REQUIRED').length;

  const handleResolveAlert = (id) => {
    setAlerts(prev =>
      prev.map(a => (a.id === id ? { ...a, is_resolved: true } : a))
    );
  };

  return (
    <div>
      {/* Page Title & Actions */}
      <div className="d-flex align-items-center justify-content-between mb-4 flex-wrap gap-2">
        <div>
          <h4 className="fw-bold text-dark mb-1">Executive Fleet Dashboard</h4>
          <p className="text-secondary small mb-0">
            Real-time aircraft availability, turbofan degradation state and maintenance triage.
          </p>
        </div>
        <div className="d-flex align-items-center gap-2">
          {isLive && (
            <span className="badge bg-success-subtle text-success border border-success-subtle d-inline-flex align-items-center gap-1 px-2 py-1">
              <Database size={13} />
              <span>Database Connected</span>
            </span>
          )}
          <Link to="/monitoring" className="btn btn-sm btn-primary d-flex align-items-center gap-2">
            <Activity size={16} />
            <span>Live Engine Telemetry</span>
          </Link>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="row g-3 mb-4">
        <div className="col-12 col-sm-6 col-xl-3">
          <MetricCard
            title="Total Aircraft"
            value={totalAircraft}
            subtitle="Registered Fleet Assets"
            icon={Plane}
            variant="blue"
            trend="+1 this quarter"
            trendPositive={true}
          />
        </div>
        <div className="col-12 col-sm-6 col-xl-3">
          <MetricCard
            title="Operational"
            value={operationalAircraft}
            subtitle={`${Math.round((operationalAircraft / totalAircraft) * 100)}% Airworthy Rate`}
            icon={CheckCircle2}
            variant="emerald"
            trend="Active flight rotation"
            trendPositive={true}
          />
        </div>
        <div className="col-12 col-sm-6 col-xl-3">
          <MetricCard
            title="Under Maintenance"
            value={inMaintenance}
            subtitle="Active Hangar Bay Tasks"
            icon={Clock}
            variant="amber"
            trend="1 major C-Check"
            trendPositive={false}
          />
        </div>
        <div className="col-12 col-sm-6 col-xl-3">
          <MetricCard
            title="Attention Required"
            value={attentionRequired}
            subtitle="RUL Safety Margin Warning"
            icon={AlertTriangle}
            variant="rose"
            trend="Immediate triage needed"
            trendPositive={false}
          />
        </div>
      </div>

      {/* Engine Health Overview & Active Alerts */}
      <div className="row g-4 mb-4">
        {/* Health Overview Breakdown */}
        <div className="col-12 col-lg-7">
          <div className="aerocard h-100">
            <div className="d-flex align-items-center justify-content-between mb-3 pb-2 border-bottom">
              <div>
                <h6 className="fw-bold mb-0">Engine Health & Fleet Distribution</h6>
                <small className="text-muted">Calculated from C-MAPSS degradation indicators</small>
              </div>
              <span className="badge bg-light text-dark border">6 Turbofans Monitored</span>
            </div>

            <div className="row g-3 mb-3">
              <div className="col-6 col-md-3 text-center p-2 rounded bg-light border">
                <div className="small text-muted mb-1">Fleet Mean Health</div>
                <div className="h4 fw-bold text-primary mb-0">72.6%</div>
                <div className="small text-success fw-medium">Acceptable</div>
              </div>
              <div className="col-6 col-md-3 text-center p-2 rounded bg-light border">
                <div className="small text-muted mb-1">Critical RUL ≤10</div>
                <div className="h4 fw-bold text-danger mb-0">1 Unit</div>
                <div className="small text-danger fw-medium">N101AP</div>
              </div>
              <div className="col-6 col-md-3 text-center p-2 rounded bg-light border">
                <div className="small text-muted mb-1">Watchlist 11-30</div>
                <div className="h4 fw-bold text-warning mb-0">1 Unit</div>
                <div className="small text-warning fw-medium">VT-AER</div>
              </div>
              <div className="col-6 col-md-3 text-center p-2 rounded bg-light border">
                <div className="small text-muted mb-1">Nominal &gt;75</div>
                <div className="h4 fw-bold text-success mb-0">4 Units</div>
                <div className="small text-success fw-medium">Optimal</div>
              </div>
            </div>

            {/* Health Meter Bars for Each Aircraft */}
            <div className="mt-4">
              <div className="small fw-bold text-uppercase text-secondary mb-2" style={{ fontSize: '0.75rem' }}>
                Individual Aircraft Engine Degradation Index
              </div>
              {MOCK_AIRCRAFT.map(aircraft => {
                const isCritical = aircraft.health_score <= 55;
                const isWarning = aircraft.health_score > 55 && aircraft.health_score <= 75;
                const color = isCritical ? '#EF4444' : isWarning ? '#F59E0B' : '#10B981';

                return (
                  <div key={aircraft.id} className="mb-3">
                    <div className="d-flex justify-content-between small mb-1">
                      <span className="fw-semibold">
                        {aircraft.tail_number} ({aircraft.model})
                      </span>
                      <span className="fw-mono fw-bold" style={{ color }}>
                        {aircraft.health_score}% • Cycle {aircraft.current_cycles}
                      </span>
                    </div>
                    <div className="progress" style={{ height: 8 }}>
                      <div
                        className="progress-bar"
                        role="progressbar"
                        style={{
                          width: `${aircraft.health_score}%`,
                          backgroundColor: color
                        }}
                        aria-valuenow={aircraft.health_score}
                        aria-valuemin="0"
                        aria-valuemax="100"
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Recent Maintenance Alerts */}
        <div className="col-12 col-lg-5">
          <div className="aerocard h-100">
            <div className="d-flex align-items-center justify-content-between mb-3 pb-2 border-bottom">
              <div>
                <h6 className="fw-bold mb-0">Recent Maintenance Alerts</h6>
                <small className="text-muted">High-priority triggers requiring response</small>
              </div>
              <span className="badge bg-danger-subtle text-danger">
                {alerts.filter(a => !a.is_resolved).length} Active
              </span>
            </div>

            <div style={{ maxHeight: 380, overflowY: 'auto' }}>
              {alerts.length === 0 ? (
                <div className="text-center py-4 text-muted small">No active maintenance alerts.</div>
              ) : (
                alerts.map(alert => (
                  <AlertCard
                    key={alert.id}
                    alert={alert}
                    onResolve={handleResolveAlert}
                  />
                ))
              )}
            </div>

            <div className="mt-3 pt-2 border-top text-center">
              <Link to="/maintenance" className="small text-decoration-none fw-semibold d-inline-flex align-items-center gap-1 text-primary">
                <span>View Full Maintenance Backlog</span>
                <ArrowRight size={14} />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Fleet Overview Table */}
      <div className="aerocard">
        <div className="d-flex align-items-center justify-content-between mb-3 pb-2 border-bottom flex-wrap gap-2">
          <div>
            <h6 className="fw-bold mb-0">Aircraft Fleet Telemetry Quick-Scan</h6>
            <small className="text-muted">Current flight cycle, engine mapping and operational status</small>
          </div>
          <Link to="/aircraft" className="btn btn-sm btn-outline-primary d-inline-flex align-items-center gap-1">
            <span>Manage All Aircraft</span>
            <ArrowRight size={14} />
          </Link>
        </div>

        <div className="table-responsive">
          <table className="aero-table">
            <thead>
              <tr>
                <th>Tail Number</th>
                <th>Model & Manufacturer</th>
                <th>Engine Model</th>
                <th>C-MAPSS Unit</th>
                <th>Current Cycle</th>
                <th>Status</th>
                <th className="text-end">Actions</th>
              </tr>
            </thead>
            <tbody>
              {fleet.map(ac => (
                <tr key={ac.id}>
                  <td className="fw-bold">{ac.tail_number}</td>
                  <td>
                    <div>{ac.model}</div>
                    <div className="text-secondary small">{ac.manufacturer}</div>
                  </td>
                  <td>{ac.engine_type}</td>
                  <td>
                    <span className="badge bg-light text-dark border">
                      Unit #{ac.cmapss_unit_id}
                    </span>
                  </td>
                  <td className="fw-mono fw-semibold">{ac.current_cycles}</td>
                  <td>
                    <StatusBadge status={ac.status} />
                  </td>
                  <td className="text-end">
                    <div className="d-inline-flex gap-2">
                      <Link
                        to={`/monitoring?unit=${ac.cmapss_unit_id}&tail=${ac.tail_number}`}
                        className="btn btn-xs btn-outline-secondary py-1 px-2"
                        style={{ fontSize: '0.78rem' }}
                      >
                        Telemetry
                      </Link>
                      <Link
                        to={`/predictive?id=${ac.id}&tail=${ac.tail_number}`}
                        className="btn btn-xs btn-outline-primary py-1 px-2"
                        style={{ fontSize: '0.78rem' }}
                      >
                        Predict RUL
                      </Link>
                    </div>
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
