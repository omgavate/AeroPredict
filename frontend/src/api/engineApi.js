// Engine Health Monitoring & Telemetry API Client
import apiClient from './apiClient';
import { MOCK_LATEST_SENSORS, MOCK_TELEMETRY_SERIES } from '../data/mockData';

export const engineApi = {
  /**
   * Fetch the latest sensor readings and thermodynamic indicator deltas for an aircraft.
   */
  async getLatestSensors(aircraftId) {
    try {
      const res = await apiClient.get(`/aircraft/${aircraftId}/sensors/latest`);
      return { success: true, data: res.data, isLive: true };
    } catch (err) {
      console.warn(`[AeroPredict Telemetry]: Live backend unavailable for aircraft #${aircraftId}, using fallback.`, err.message);
      return {
        success: true,
        data: {
          ...MOCK_LATEST_SENSORS,
          aircraft_id: aircraftId,
          cycle: MOCK_LATEST_SENSORS.cycle,
          health_indicators: {
            t30_delta_r: 12.4,
            p30_delta_psia: -2.8,
            overall_condition: 'ATTENTION_REQUIRED'
          }
        },
        isLive: false,
        error: err.message
      };
    }
  },

  /**
   * Fetch chronological sensor history for charts and trend visualizers.
   */
  async getSensorHistory(aircraftId, options = {}) {
    try {
      const params = {};
      if (options.limit) params.limit = options.limit;
      if (options.cycle_start) params.cycle_start = options.cycle_start;
      if (options.cycle_end) params.cycle_end = options.cycle_end;
      if (options.sensors) params.sensors = options.sensors;

      const res = await apiClient.get(`/aircraft/${aircraftId}/sensors/history`, { params });
      return { success: true, data: res.data, isLive: true };
    } catch (err) {
      console.warn(`[AeroPredict Telemetry]: Historical telemetry unavailable for aircraft #${aircraftId}, using fallback.`, err.message);
      return {
        success: true,
        data: {
          aircraft_id: aircraftId,
          history: MOCK_TELEMETRY_SERIES,
          count: MOCK_TELEMETRY_SERIES.length
        },
        isLive: false,
        error: err.message
      };
    }
  },

  /**
   * Advance telemetry cycle by +1 using actual C-MAPSS data from Flask / MySQL.
   */
  async advanceCycle(aircraftId) {
    try {
      const res = await apiClient.post(`/aircraft/${aircraftId}/sensors/advance-cycle`);
      return { success: true, data: res.data, isLive: true };
    } catch (err) {
      console.warn(`[AeroPredict Telemetry]: Advance cycle endpoint failed, applying local simulation fallback.`, err.message);
      return {
        success: false,
        error: err.message
      };
    }
  },

  /**
   * Fetch comprehensive thermodynamic health diagnostic report for the engine.
   */
  async getEngineOverview(aircraftId) {
    try {
      const res = await apiClient.get(`/aircraft/${aircraftId}/engine`);
      return { success: true, data: res.data, isLive: true };
    } catch (err) {
      console.warn(`[AeroPredict Telemetry]: Engine overview endpoint unavailable, using fallback.`, err.message);
      return {
        success: false,
        error: err.message
      };
    }
  }
};

export default engineApi;
