// Aircraft Fleet API Client
import apiClient from './apiClient';
import { MOCK_AIRCRAFT } from '../data/mockData';

export const aircraftApi = {
  /**
   * Fetch all aircraft with optional search and status filtering.
   */
  async getAll(search = '', status = 'ALL') {
    try {
      const params = {};
      if (search && search.trim()) params.search = search.trim();
      if (status && status !== 'ALL') params.status = status;

      const res = await apiClient.get('/aircraft', { params });
      return { success: true, data: res.data, isLive: true };
    } catch (err) {
      console.warn('[AeroPredict API Notice]: Backend unreachable, falling back to local dataset.', err.message);
      // Client-side fallback filter
      let filtered = [...MOCK_AIRCRAFT];
      if (search) {
        const s = search.toLowerCase();
        filtered = filtered.filter(a =>
          a.tail_number.toLowerCase().includes(s) ||
          a.model.toLowerCase().includes(s) ||
          a.manufacturer.toLowerCase().includes(s)
        );
      }
      if (status && status !== 'ALL') {
        filtered = filtered.filter(a => a.status === status);
      }
      return { success: true, data: filtered, isLive: false, fallbackNote: 'Using offline demonstration dataset' };
    }
  },

  /**
   * Fetch single aircraft details by ID.
   */
  async getById(id) {
    try {
      const res = await apiClient.get(`/aircraft/${id}`);
      return { success: true, data: res.data, isLive: true };
    } catch (err) {
      console.warn(`[AeroPredict API Notice]: Backend unreachable for aircraft #${id}, using fallback.`);
      const found = MOCK_AIRCRAFT.find(a => a.id === parseInt(id, 10)) || MOCK_AIRCRAFT[0];
      return { success: true, data: found, isLive: false };
    }
  },

  /**
   * Create new aircraft record.
   */
  async create(payload) {
    try {
      const res = await apiClient.post('/aircraft', payload);
      return { success: true, data: res.data, message: res.message, isLive: true };
    } catch (err) {
      if (err.details) {
        // Validation errors from Flask
        return { success: false, error: err.message, details: err.details };
      }
      throw err;
    }
  },

  /**
   * Update existing aircraft record.
   */
  async update(id, payload) {
    try {
      const res = await apiClient.put(`/aircraft/${id}`, payload);
      return { success: true, data: res.data, message: res.message, isLive: true };
    } catch (err) {
      if (err.details) {
        return { success: false, error: err.message, details: err.details };
      }
      throw err;
    }
  },

  /**
   * Delete aircraft record.
   */
  async delete(id) {
    try {
      const res = await apiClient.delete(`/aircraft/${id}`);
      return { success: true, message: res.message, isLive: true };
    } catch (err) {
      throw err;
    }
  }
};

export default aircraftApi;
