// Maintenance Management API Client
import apiClient from './apiClient';
import { MOCK_MAINTENANCE_RECORDS } from '../data/mockData';

export const maintenanceApi = {
  /**
   * Fetch all maintenance work orders with optional filtering.
   */
  async getAll(params = {}) {
    try {
      const queryParams = {};
      if (params.aircraft_id) queryParams.aircraft_id = params.aircraft_id;
      if (params.status && params.status !== 'ALL') queryParams.status = params.status;
      if (params.priority && params.priority !== 'ALL') queryParams.priority = params.priority;
      if (params.search && params.search.trim()) queryParams.search = params.search.trim();

      const res = await apiClient.get('/maintenance', { params: queryParams });
      return { success: true, data: res.data || [], isLive: true };
    } catch (err) {
      console.warn('[AeroPredict Maintenance]: Live API unavailable, falling back to local dataset.', err.message);
      let filtered = [...MOCK_MAINTENANCE_RECORDS];
      if (params.status && params.status !== 'ALL') {
        filtered = filtered.filter(r => r.status === params.status);
      }
      if (params.priority && params.priority !== 'ALL') {
        filtered = filtered.filter(r => r.priority === params.priority);
      }
      if (params.search) {
        const s = params.search.toLowerCase();
        filtered = filtered.filter(r =>
          r.title.toLowerCase().includes(s) ||
          r.description.toLowerCase().includes(s) ||
          r.tail_number.toLowerCase().includes(s)
        );
      }
      return { success: true, data: filtered, isLive: false, error: err.message };
    }
  },

  /**
   * Fetch single maintenance work order by ID.
   */
  async getById(id) {
    try {
      const res = await apiClient.get(`/maintenance/${id}`);
      return { success: true, data: res.data, isLive: true };
    } catch (err) {
      const fallback = MOCK_MAINTENANCE_RECORDS.find(r => r.id === parseInt(id, 10));
      return { success: false, data: fallback, error: err.message, isLive: false };
    }
  },

  /**
   * Create a new maintenance work order.
   */
  async create(payload) {
    try {
      const res = await apiClient.post('/maintenance', payload);
      return { success: true, data: res.data, isLive: true };
    } catch (err) {
      return {
        success: false,
        error: err.message || 'Failed to create work order.',
        details: err.details || {}
      };
    }
  },

  /**
   * Update an existing maintenance work order.
   */
  async update(id, payload) {
    try {
      const res = await apiClient.put(`/maintenance/${id}`, payload);
      return { success: true, data: res.data, isLive: true };
    } catch (err) {
      return {
        success: false,
        error: err.message || 'Failed to update work order.',
        details: err.details || {}
      };
    }
  },

  /**
   * Delete a maintenance record.
   */
  async delete(id) {
    try {
      const res = await apiClient.delete(`/maintenance/${id}`);
      return { success: true, data: res.data, isLive: true };
    } catch (err) {
      return {
        success: false,
        error: err.message || 'Failed to delete work order.'
      };
    }
  },

  /**
   * Fetch maintenance history for an aircraft.
   */
  async getHistoryByAircraft(aircraftId) {
    try {
      const res = await apiClient.get(`/maintenance/history/${aircraftId}`);
      return { success: true, data: res.data || [], isLive: true };
    } catch (err) {
      return { success: false, data: [], error: err.message, isLive: false };
    }
  }
};

export default maintenanceApi;
