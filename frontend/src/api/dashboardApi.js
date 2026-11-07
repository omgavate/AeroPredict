// Executive Fleet Dashboard API Client
import apiClient from './apiClient';
import { MOCK_AIRCRAFT, MOCK_ALERTS, MOCK_MAINTENANCE_RECORDS } from '../data/mockData';

export const dashboardApi = {
  /**
   * Fetch complete aggregated dashboard dataset in a single call.
   */
  async getDashboardData() {
    try {
      const res = await apiClient.get('/dashboard');
      return {
        success: true,
        data: res.data,
        isLive: true
      };
    } catch (err) {
      console.warn('[AeroPredict Dashboard]: Live API unreachable, using graceful fallback dataset.', err.message);

      // Build realistic fallback dataset matching backend structure
      const totalAircraft = MOCK_AIRCRAFT.length;
      const operational = MOCK_AIRCRAFT.filter(a => a.status === 'OPERATIONAL').length;
      const underMaintenance = MOCK_AIRCRAFT.filter(a => a.status === 'UNDER_MAINTENANCE').length;
      const attentionRequired = MOCK_AIRCRAFT.filter(a => a.status === 'ATTENTION_REQUIRED').length;
      const pendingMaint = MOCK_MAINTENANCE_RECORDS.filter(m => m.status === 'PENDING').length;
      const activeAlerts = MOCK_ALERTS.filter(a => !a.is_resolved).length;

      const fallbackFleet = MOCK_AIRCRAFT.map(a => ({
        ...a,
        health_score: a.health_score || 85,
        latest_predicted_rul: a.predicted_rul || (a.health_score > 60 ? 84.5 : 9.5),
        latest_risk_level: a.health_score <= 50 ? 'CRITICAL' : a.health_score <= 70 ? 'HIGH' : 'LOW',
        pending_maintenance_count: MOCK_MAINTENANCE_RECORDS.filter(m => m.aircraft_id === a.id && m.status !== 'COMPLETED').length,
        active_alerts_count: MOCK_ALERTS.filter(al => al.aircraft_id === a.id && !al.is_resolved).length
      }));

      const avgHealth = Math.round(fallbackFleet.reduce((acc, curr) => acc + curr.health_score, 0) / totalAircraft);

      return {
        success: true,
        data: {
          stats: {
            total_aircraft: totalAircraft,
            operational: operational,
            under_maintenance: underMaintenance,
            attention_required: attentionRequired,
            retired: 0,
            pending_maintenance: pendingMaint,
            in_progress_maintenance: 1,
            total_maintenance_records: MOCK_MAINTENANCE_RECORDS.length,
            active_alerts_count: activeAlerts,
            critical_alerts_count: 1,
            airworthy_rate: Math.round((operational / totalAircraft) * 100)
          },
          health_overview: {
            average_health_score: avgHealth,
            average_rul: 68.4,
            monitored_engines: totalAircraft,
            risk_breakdown: {
              CRITICAL: 1,
              HIGH: 2,
              MEDIUM: 0,
              LOW: 3
            },
            status_breakdown: {
              OPERATIONAL: operational,
              UNDER_MAINTENANCE: underMaintenance,
              ATTENTION_REQUIRED: attentionRequired,
              RETIRED: 0
            },
            distribution_chart: [
              { category: 'Nominal (>75)', key: 'LOW', count: 3, fill: '#10B981' },
              { category: 'Moderate (31-75)', key: 'MEDIUM', count: 0, fill: '#3B82F6' },
              { category: 'Watchlist (11-30)', key: 'HIGH', count: 2, fill: '#F59E0B' },
              { category: 'Critical (≤10)', key: 'CRITICAL', count: 1, fill: '#EF4444' }
            ]
          },
          maintenance_distribution: {
            by_status: {
              PENDING: 2,
              SCHEDULED: 1,
              IN_PROGRESS: 1,
              COMPLETED: 1,
              CANCELLED: 0
            },
            by_priority: {
              CRITICAL: 1,
              HIGH: 1,
              MEDIUM: 2,
              LOW: 1
            },
            status_chart: [
              { name: 'Pending', value: 2, fill: '#F59E0B' },
              { name: 'Scheduled', value: 1, fill: '#3B82F6' },
              { name: 'In Progress', value: 1, fill: '#8B5CF6' },
              { name: 'Completed', value: 1, fill: '#10B981' }
            ],
            priority_chart: [
              { priority: 'Critical', count: 1, fill: '#EF4444' },
              { priority: 'High', count: 1, fill: '#F97316' },
              { priority: 'Medium', count: 2, fill: '#FBBF24' },
              { priority: 'Low', count: 1, fill: '#10B981' }
            ]
          },
          recent_alerts: MOCK_ALERTS,
          fleet_summary: fallbackFleet,
          recent_activity: [
            {
              id: 'maint-1',
              type: 'MAINTENANCE',
              title: 'Work Order: Emergency HPC Borescope & Blade Replacement',
              tail_number: 'N101AP',
              description: 'Status: Pending • Priority: CRITICAL',
              severity: 'CRITICAL',
              timestamp: '18m ago'
            },
            {
              id: 'alert-1',
              type: 'ALERT',
              title: 'Alert: RUL CRITICAL',
              tail_number: 'N101AP',
              description: 'Predicted RUL ≤ 10 flight cycles. Immediate borescope inspection required.',
              severity: 'CRITICAL',
              timestamp: '25m ago'
            },
            {
              id: 'pred-1',
              type: 'PREDICTION',
              title: 'Inference: Cycle 192',
              tail_number: 'N101AP',
              description: 'Predicted RUL: 6.2 cycles (CRITICAL Risk)',
              severity: 'CRITICAL',
              timestamp: '32m ago'
            }
          ]
        },
        isLive: false,
        error: err.message
      };
    }
  },

  /**
   * Fetch KPI statistics only.
   */
  async getStats() {
    try {
      const res = await apiClient.get('/dashboard/stats');
      return { success: true, data: res.data, isLive: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  },

  /**
   * Fetch health overview metrics only.
   */
  async getHealthOverview() {
    try {
      const res = await apiClient.get('/dashboard/health-overview');
      return { success: true, data: res.data, isLive: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  },

  /**
   * Fetch recent alerts with optional limit and filter.
   */
  async getAlerts(params = {}) {
    try {
      const res = await apiClient.get('/dashboard/alerts', { params });
      return { success: true, data: res.data, isLive: true };
    } catch (err) {
      return { success: false, error: err.message, data: MOCK_ALERTS };
    }
  },

  /**
   * Resolve / acknowledge a maintenance alert.
   */
  async resolveAlert(alertId) {
    try {
      const res = await apiClient.put(`/dashboard/alerts/${alertId}/resolve`);
      return { success: true, data: res.data, isLive: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }
};

export default dashboardApi;
