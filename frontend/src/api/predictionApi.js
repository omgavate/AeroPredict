// Prediction API Client
import apiClient from './apiClient';
import { MOCK_RUL_PREDICTION, MOCK_PREDICTION_HISTORY } from '../data/mockData';

export const predictionApi = {
  /**
   * Run RUL prediction for an aircraft using current telemetry readings.
   */
  async predictRul(aircraftId, cycle, telemetry, saveToDb = true) {
    try {
      const payload = {
        aircraft_id: aircraftId,
        cycle: cycle,
        telemetry: telemetry,
        save_to_db: saveToDb
      };
      const res = await apiClient.post('/predict', payload);
      return { success: true, data: res.data, isLive: true };
    } catch (err) {
      console.warn(`[AeroPredict Prediction]: Live prediction unavailable for aircraft #${aircraftId}, using fallback.`, err.message);
      return {
        success: false,
        error: err.message
      };
    }
  },

  /**
   * Fetch the latest prediction record for an aircraft.
   */
  async getLatestPrediction(aircraftId) {
    try {
      const res = await apiClient.get(`/predict/latest/${aircraftId}`);
      return { success: true, data: res.data, isLive: true };
    } catch (err) {
      return {
        success: false,
        error: err.message,
        isLive: false
      };
    }
  },

  /**
   * Fetch prediction history for an aircraft.
   */
  async getPredictionHistory(aircraftId, limit = 50) {
    try {
      const res = await apiClient.get(`/predict/history/${aircraftId}`, { params: { limit } });
      return { success: true, data: res.data || [], isLive: true };
    } catch (err) {
      return {
        success: false,
        data: [],
        error: err.message,
        isLive: false
      };
    }
  },

  /**
   * Fetch machine learning model metadata.
   */
  async getModelInfo() {
    try {
      const res = await apiClient.get('/predict/model-info');
      return { success: true, data: res.data, isLive: true };
    } catch (err) {
      return {
        success: false,
        error: err.message
      };
    }
  }
};

export default predictionApi;
