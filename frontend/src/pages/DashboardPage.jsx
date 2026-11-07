import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Plane,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ArrowRight,
  ShieldAlert,
  Activity,
  Wrench,
  RefreshCw,
  Database,
  Cpu,
  BarChart3,
  PieChart as PieIcon,
  History,
  Check,
  AlertCircle
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import MetricCard from '../components/MetricCard';
import StatusBadge from '../components/StatusBadge';
import AlertCard from '../components/AlertCard';
import LoadingSpinner from '../components/LoadingSpinner';
import dashboardApi from '../api/dashboardApi';

// Custom Tooltip for Charts
const CustomChartTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0];
    return (
      <div
        className="p-2 rounded shadow-sm bg-white border"
        style={{ fontSize: '0.8rem', minWidth: '120px' }}
      >
        <div className="fw-bold text-dark mb-1">{label || data.name}</div>
        <div className="d-flex align-items-center gap-2">
          <span
            className="d-inline-block rounded-circle"
            style={{ width: 8, height: 8, backgroundColor: data.fill || data.color }}
          />
          <span className="text-secondary">{data.name || 'Count'}:</span>
          <span className="fw-mono fw-bold text-dark">{data.value}</span>
        </div>
      </div>
    );
  }
  return null;
};

export default function DashboardPage() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [isLive, setIsLive] = useState(false);

  const fetchDashboard = useCallback(async (isManualRefresh = false) => {
    if (isManualRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const res = await dashboardApi.getDashboardData();
      if (res.success && res.data) {
        setDashboardData(res.data);
        setIsLive(res.isLive);
      } else {
        setError(res.error || 'Failed to retrieve dashboard metrics.');
      }
    } catch (err) {
      console.error('Error fetching dashboard:', err);
      setError(err.message || 'Network error while loading dashboard.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const handleResolveAlert = async (alertId) => {
    try {
      const res = await dashboardApi.resolveAlert(alertId);
      if (res.success) {
        // Optimistically update alerts list and active alert count
        setDashboardData(prev => {
          if (!prev) return prev;
          const updatedAlerts = prev.recent_alerts.map(a =>
            a.id === alertId ? { ...a, is_resolved: true } : a
          );
          const activeCount = updatedAlerts.filter(a => !a.is_resolved).length;
          return {
            ...prev,
            stats: {
              ...prev.stats,
              active_alerts_count: activeCount
            },
            recent_alerts: updatedAlerts
          };
        });
      }
    } catch (err) {
      console.error('Error resolving alert:', err);
    }
  };

  if (loading) {
    return (
      <div className="d-flex flex-column align-items-center justify-content-center py-5 my-5">
        <LoadingSpinner size="lg" />
        <p className="mt-3 text-secondary small fw-medium">
          Aggregating fleet telemetry &amp; health diagnostics...
        </p>
      </div>
    );
  }

  const stats = dashboardData?.stats || {
    total_aircraft: 0,
    operational: 0,
    under_maintenance: 0,
    attention_required: 0,
    pending_maintenance: 0,
    active_alerts_count: 0,
    critical_alerts_count: 0,
    airworthy_rate: 0
  };

  const healthOverview = dashboardData?.health_overview || {
    average_health_score: 0,
    average_rul: 0,
    monitored_engines: 0,
    risk_breakdown: { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 },
    distribution_chart: []
  };

  const maintenanceDist = dashboardData?.maintenance_distribution || {
    by_status: {},
    by_priority: {},
    status_chart: [],
    priority_chart: []
  };

  const recentAlerts = dashboardData?.recent_alerts || [];
  const fleetSummary = dashboardData?.fleet_summary || [];
  const recentActivity = dashboardData?.recent_activity || [];

  // Build Fleet Status Donut Chart Data
  const fleetStatusChartData = [
    { name: 'Operational', value: stats.operational, fill: '#10B981' },
    { name: 'Under Maint.', value: stats.under_maintenance, fill: '#F59E0B' },
    { name: 'Attention Req.', value: stats.attention_required, fill: '#EF4444' }
  ].filter(item => item.value > 0);

  // Fallback for empty fleet donut
  if (fleetStatusChartData.length === 0) {
    fleetStatusChartData.push({ name: 'No Aircraft', value: 1, fill: '#CBD5E1' });
  }

  // Build Engine Health Bar Chart Data for Fleet Summary
  const engineHealthChartData = fleetSummary.map(ac => ({
    name: ac.tail_number,
    health: ac.health_score,
    rul: ac.latest_predicted_rul !== null ? ac.latest_predicted_rul : 0,
    fill: ac.health_score <= 50 ? '#EF4444' : ac.health_score <= 75 ? '#F59E0B' : '#10B981'
  }));

  return (
    <div>
      {/* Page Title & Status Strip */}
      <div className="d-flex align-items-center justify-content-between mb-4 flex-wrap gap-2">
        <div>
          <h4 className="fw-bold text-dark mb-1">Executive Fleet Dashboard</h4>
          <p className="text-secondary small mb-0">
            Real-time aircraft availability, turbofan degradation state and maintenance triage.
          </p>
        </div>
        <div className="d-flex align-items-center gap-2">
          {isLive ? (
            <span className="badge bg-success-subtle text-success border border-success-subtle d-inline-flex align-items-center gap-1 px-2 py-1">
              <Database size={13} />
              <span>Database Connected</span>
            </span>
          ) : (
            <span className="badge bg-warning-subtle text-warning border border-warning-subtle d-inline-flex align-items-center gap-1 px-2 py-1">
              <span>Local Cached Dataset</span>
            </span>
          )}

          <button
            onClick={() => fetchDashboard(true)}
            disabled={refreshing}
            className="btn btn-sm btn-outline-secondary d-inline-flex align-items-center gap-1"
            title="Refresh dashboard metrics"
          >
            <RefreshCw size={14} className={refreshing ? 'spin' : ''} />
            <span>{refreshing ? 'Syncing...' : 'Sync'}</span>
          </button>

          <Link to="/monitoring" className="btn btn-sm btn-primary d-inline-flex align-items-center gap-2">
            <Activity size={15} />
            <span>Live Telemetry</span>
          </Link>
        </div>
      </div>

      {/* Error banner if network/query failure occurred */}
      {error && (
        <div className="alert alert-warning d-flex align-items-center justify-content-between py-2 px-3 mb-4">
          <div className="d-flex align-items-center gap-2 small">
            <AlertCircle size={16} className="text-warning flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={() => fetchDashboard(true)}
            className="btn btn-xs btn-outline-dark ms-2 py-1 px-2"
          >
            Retry
          </button>
        </div>
      )}

      {/* KPI Cards Row (6 Metric Cards) */}
      <div className="row g-3 mb-4">
        <div className="col-12 col-sm-6 col-lg-4 col-xl-2">
          <MetricCard
            title="Total Aircraft"
            value={stats.total_aircraft}
            subtitle="Registered Fleet Assets"
            icon={Plane}
            variant="blue"
            trend={`${fleetSummary.length} units listed`}
            trendPositive={true}
          />
        </div>
        <div className="col-12 col-sm-6 col-lg-4 col-xl-2">
          <MetricCard
            title="Operational"
            value={stats.operational}
            subtitle={`${stats.airworthy_rate}% Airworthy Rate`}
            icon={CheckCircle2}
            variant="emerald"
            trend="Active flight duty"
            trendPositive={true}
          />
        </div>
        <div className="col-12 col-sm-6 col-lg-4 col-xl-2">
          <MetricCard
            title="Under Maintenance"
            value={stats.under_maintenance}
            subtitle="Hangar Bay Status"
            icon={Clock}
            variant="amber"
            trend="Scheduled servicing"
            trendPositive={false}
          />
        </div>
        <div className="col-12 col-sm-6 col-lg-4 col-xl-2">
          <MetricCard
            title="Attention Req."
            value={stats.attention_required}
            subtitle="Safety Margin Warning"
            icon={AlertTriangle}
            variant="rose"
            trend="Triage recommended"
            trendPositive={false}
          />
        </div>
        <div className="col-12 col-sm-6 col-lg-4 col-xl-2">
          <MetricCard
            title="Pending Maint."
            value={stats.pending_maintenance}
            subtitle={`${stats.total_maintenance_records} Total Work Orders`}
            icon={Wrench}
            variant="purple"
            trend="Unresolved work tasks"
            trendPositive={stats.pending_maintenance === 0}
          />
        </div>
        <div className="col-12 col-sm-6 col-lg-4 col-xl-2">
          <MetricCard
            title="Active Alerts"
            value={stats.active_alerts_count}
            subtitle={`${stats.critical_alerts_count} Critical Level`}
            icon={ShieldAlert}
            variant="rose"
            trend="Requires response"
            trendPositive={stats.active_alerts_count === 0}
          />
        </div>
      </div>

      {/* Visual Charts Row: Fleet Operational Distribution & Maintenance Backlog */}
      <div className="row g-4 mb-4">
        {/* Fleet Status Donut Chart */}
        <div className="col-12 col-lg-6">
          <div className="aerocard h-100">
            <div className="d-flex align-items-center justify-content-between mb-3 pb-2 border-bottom">
              <div>
                <h6 className="fw-bold mb-0 d-flex align-items-center gap-2">
                  <PieIcon size={16} className="text-primary" />
                  <span>Fleet Operational Status</span>
                </h6>
                <small className="text-muted">Airworthiness ratio across active aircraft airframes</small>
              </div>
              <span className="badge bg-light text-dark border">
                {stats.total_aircraft} Total Units
              </span>
            </div>

            <div className="row align-items-center">
              <div className="col-12 col-sm-6" style={{ height: 210 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={fleetStatusChartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={78}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {fleetStatusChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} stroke="#ffffff" strokeWidth={2} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomChartTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="col-12 col-sm-6">
                <div className="d-flex flex-column gap-2 small">
                  <div className="d-flex align-items-center justify-content-between p-2 rounded bg-light border">
                    <div className="d-flex align-items-center gap-2">
                      <span className="d-inline-block rounded-circle" style={{ width: 10, height: 10, backgroundColor: '#10B981' }} />
                      <span className="fw-medium">Operational</span>
                    </div>
                    <span className="fw-mono fw-bold text-dark">{stats.operational}</span>
                  </div>
                  <div className="d-flex align-items-center justify-content-between p-2 rounded bg-light border">
                    <div className="d-flex align-items-center gap-2">
                      <span className="d-inline-block rounded-circle" style={{ width: 10, height: 10, backgroundColor: '#F59E0B' }} />
                      <span className="fw-medium">Under Maintenance</span>
                    </div>
                    <span className="fw-mono fw-bold text-dark">{stats.under_maintenance}</span>
                  </div>
                  <div className="d-flex align-items-center justify-content-between p-2 rounded bg-light border">
                    <div className="d-flex align-items-center gap-2">
                      <span className="d-inline-block rounded-circle" style={{ width: 10, height: 10, backgroundColor: '#EF4444' }} />
                      <span className="fw-medium">Attention Required</span>
                    </div>
                    <span className="fw-mono fw-bold text-dark">{stats.attention_required}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Maintenance Distribution Chart */}
        <div className="col-12 col-lg-6">
          <div className="aerocard h-100">
            <div className="d-flex align-items-center justify-content-between mb-3 pb-2 border-bottom">
              <div>
                <h6 className="fw-bold mb-0 d-flex align-items-center gap-2">
                  <BarChart3 size={16} className="text-primary" />
                  <span>Maintenance Work Order Distribution</span>
                </h6>
                <small className="text-muted">Work order status stages &amp; active shop tasks</small>
              </div>
              <Link to="/maintenance" className="small text-decoration-none fw-semibold text-primary d-inline-flex align-items-center gap-1">
                <span>Manage</span>
                <ArrowRight size={13} />
              </Link>
            </div>

            <div style={{ width: '100%', height: 210 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={maintenanceDist.status_chart}
                  margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748B' }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#64748B' }} />
                  <Tooltip content={<CustomChartTooltip />} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {maintenanceDist.status_chart.map((entry, index) => (
                      <Cell key={`bar-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>

      {/* Engine Health Diagnostic Overview & Active Alerts */}
      <div className="row g-4 mb-4">
        {/* Health Overview Breakdown */}
        <div className="col-12 col-lg-7">
          <div className="aerocard h-100">
            <div className="d-flex align-items-center justify-content-between mb-3 pb-2 border-bottom">
              <div>
                <h6 className="fw-bold mb-0 d-flex align-items-center gap-2">
                  <Cpu size={16} className="text-primary" />
                  <span>Engine Health Overview &amp; Degradation Index</span>
                </h6>
                <small className="text-muted">Derived from NASA C-MAPSS thermodynamic sensor readings &amp; RUL predictions</small>
              </div>
              <span className="badge bg-light text-dark border">
                {healthOverview.monitored_engines} Turbofans Monitored
              </span>
            </div>

            {/* Health KPI Summary Tiles */}
            <div className="row g-3 mb-4">
              <div className="col-6 col-md-3 text-center p-2 rounded bg-light border">
                <div className="small text-muted mb-1">Fleet Mean Health</div>
                <div className="h4 fw-bold text-primary mb-0">{healthOverview.average_health_score}%</div>
                <div className="small text-success fw-medium">
                  {healthOverview.average_health_score >= 70 ? 'Acceptable' : 'Attention Needed'}
                </div>
              </div>
              <div className="col-6 col-md-3 text-center p-2 rounded bg-light border">
                <div className="small text-muted mb-1">Mean Est. RUL</div>
                <div className="h4 fw-bold text-dark mb-0">{healthOverview.average_rul}</div>
                <div className="small text-secondary fw-medium">Flight Cycles</div>
              </div>
              <div className="col-6 col-md-3 text-center p-2 rounded bg-light border">
                <div className="small text-muted mb-1">Critical Tier (≤10)</div>
                <div className="h4 fw-bold text-danger mb-0">{healthOverview.risk_breakdown?.CRITICAL || 0} Units</div>
                <div className="small text-danger fw-medium">Triage Priority</div>
              </div>
              <div className="col-6 col-md-3 text-center p-2 rounded bg-light border">
                <div className="small text-muted mb-1">Nominal Tier (&gt;75)</div>
                <div className="h4 fw-bold text-success mb-0">{healthOverview.risk_breakdown?.LOW || 0} Units</div>
                <div className="small text-success fw-medium">Optimal Margin</div>
              </div>
            </div>

            {/* Health Meter Bars for Each Aircraft */}
            <div>
              <div className="small fw-bold text-uppercase text-secondary mb-2" style={{ fontSize: '0.75rem' }}>
                Per-Aircraft Turbofan Degradation &amp; Safety Margin
              </div>
              {fleetSummary.length === 0 ? (
                <div className="text-center py-4 text-muted small">No aircraft registered in fleet database.</div>
              ) : (
                fleetSummary.map(aircraft => {
                  const isCritical = aircraft.health_score <= 50;
                  const isWarning = aircraft.health_score > 50 && aircraft.health_score <= 75;
                  const color = isCritical ? '#EF4444' : isWarning ? '#F59E0B' : '#10B981';

                  return (
                    <div key={aircraft.id} className="mb-3">
                      <div className="d-flex justify-content-between align-items-center small mb-1">
                        <div>
                          <span className="fw-semibold text-dark">
                            {aircraft.tail_number}
                          </span>
                          <span className="text-muted ms-1">({aircraft.model})</span>
                        </div>
                        <div className="d-flex align-items-center gap-2">
                          {aircraft.latest_predicted_rul !== null && (
                            <span className="badge bg-light text-secondary border fw-normal" style={{ fontSize: '0.72rem' }}>
                              Est. RUL: {aircraft.latest_predicted_rul.toFixed(1)} cyc
                            </span>
                          )}
                          <span className="fw-mono fw-bold" style={{ color }}>
                            {aircraft.health_score}% • Cycle {aircraft.current_cycles}
                          </span>
                        </div>
                      </div>
                      <div className="progress" style={{ height: 8 }}>
                        <div
                          className="progress-bar"
                          role="progressbar"
                          style={{
                            width: `${Math.min(100, Math.max(5, aircraft.health_score))}%`,
                            backgroundColor: color
                          }}
                          aria-valuenow={aircraft.health_score}
                          aria-valuemin="0"
                          aria-valuemax="100"
                        />
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Recent Maintenance Alerts */}
        <div className="col-12 col-lg-5">
          <div className="aerocard h-100 d-flex flex-column">
            <div className="d-flex align-items-center justify-content-between mb-3 pb-2 border-bottom">
              <div>
                <h6 className="fw-bold mb-0 d-flex align-items-center gap-2">
                  <ShieldAlert size={16} className="text-danger" />
                  <span>Recent Maintenance Alerts</span>
                </h6>
                <small className="text-muted">High-priority triggers requiring dispatch</small>
              </div>
              <span className="badge bg-danger-subtle text-danger">
                {recentAlerts.filter(a => !a.is_resolved).length} Active
              </span>
            </div>

            <div className="flex-grow-1" style={{ maxHeight: 390, overflowY: 'auto' }}>
              {recentAlerts.length === 0 ? (
                <div className="text-center py-5 text-muted small">
                  <CheckCircle2 size={32} className="text-success mb-2 opacity-50" />
                  <div>No active maintenance alerts.</div>
                  <div className="text-secondary mt-1">Fleet systems operating within nominal limits.</div>
                </div>
              ) : (
                recentAlerts.map(alert => (
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

      {/* Bottom Section: Operational Activity & Fleet Telemetry Quick-Scan */}
      <div className="row g-4 mb-4">
        {/* Recent Operational Activity Timeline */}
        <div className="col-12 col-lg-4">
          <div className="aerocard h-100">
            <div className="d-flex align-items-center justify-content-between mb-3 pb-2 border-bottom">
              <div>
                <h6 className="fw-bold mb-0 d-flex align-items-center gap-2">
                  <History size={16} className="text-primary" />
                  <span>Recent Activity</span>
                </h6>
                <small className="text-muted">Operational timeline of events</small>
              </div>
              <span className="badge bg-light text-dark border">Latest</span>
            </div>

            <div className="d-flex flex-column gap-3" style={{ maxHeight: 360, overflowY: 'auto' }}>
              {recentActivity.length === 0 ? (
                <div className="text-center py-4 text-muted small">No recent activity logged.</div>
              ) : (
                recentActivity.map(act => (
                  <div key={act.id} className="d-flex align-items-start gap-2 pb-2 border-bottom">
                    <span
                      className="d-inline-flex p-1 rounded-circle mt-1"
                      style={{
                        backgroundColor:
                          act.severity === 'CRITICAL'
                            ? '#FEE2E2'
                            : act.severity === 'HIGH'
                            ? '#FEF3C7'
                            : '#EFF6FF',
                        color:
                          act.severity === 'CRITICAL'
                            ? '#DC2626'
                            : act.severity === 'HIGH'
                            ? '#D97706'
                            : '#2563EB'
                      }}
                    >
                      {act.type === 'ALERT' ? (
                        <ShieldAlert size={13} />
                      ) : act.type === 'PREDICTION' ? (
                        <Cpu size={13} />
                      ) : (
                        <Wrench size={13} />
                      )}
                    </span>
                    <div className="flex-grow-1">
                      <div className="d-flex align-items-center justify-content-between">
                        <span className="fw-bold text-dark small" style={{ fontSize: '0.82rem' }}>
                          {act.tail_number}
                        </span>
                        <span className="text-muted" style={{ fontSize: '0.72rem' }}>
                          {act.timestamp}
                        </span>
                      </div>
                      <div className="text-secondary small" style={{ fontSize: '0.78rem' }}>
                        {act.title}
                      </div>
                      <div className="text-muted small mt-1" style={{ fontSize: '0.74rem' }}>
                        {act.description}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Fleet Quick-Scan Table */}
        <div className="col-12 col-lg-8">
          <div className="aerocard h-100">
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
                    <th>Model &amp; Manufacturer</th>
                    <th>Engine Model</th>
                    <th>C-MAPSS Unit</th>
                    <th>Current Cycle</th>
                    <th>Health</th>
                    <th>Status</th>
                    <th className="text-end">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {fleetSummary.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="text-center py-4 text-muted small">
                        No aircraft currently registered in the database.
                      </td>
                    </tr>
                  ) : (
                    fleetSummary.map(ac => (
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
                          <span
                            className="fw-mono fw-bold small"
                            style={{
                              color:
                                ac.health_score <= 50
                                  ? '#EF4444'
                                  : ac.health_score <= 75
                                  ? '#F59E0B'
                                  : '#10B981'
                            }}
                          >
                            {ac.health_score}%
                          </span>
                        </td>
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
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
