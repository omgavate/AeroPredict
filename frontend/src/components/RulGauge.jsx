import React from 'react';
import { AlertCircle, CheckCircle, Clock } from 'lucide-react';

export default function RulGauge({ rul = 0, maxRul = 125, cycle = 0 }) {
  // Normalize RUL percentage
  const percentage = Math.min(Math.max((rul / maxRul) * 100, 0), 100);

  // Determine status color and label
  let color = '#10B981'; // Green
  let riskLabel = 'LOW RISK';
  let riskDesc = 'Normal Flight Envelope';
  let badgeClass = 'badge-risk-low';

  if (rul <= 10) {
    color = '#EF4444'; // Red
    riskLabel = 'CRITICAL RISK';
    riskDesc = 'Immediate Grounding Required';
    badgeClass = 'badge-risk-critical';
  } else if (rul <= 30) {
    color = '#F97316'; // Orange
    riskLabel = 'HIGH RISK';
    riskDesc = 'Maintenance Due within 15 Cycles';
    badgeClass = 'badge-risk-high';
  } else if (rul <= 75) {
    color = '#F59E0B'; // Amber
    riskLabel = 'MEDIUM RISK';
    riskDesc = 'Watchlist - Monitor Telemetry Drift';
    badgeClass = 'badge-risk-medium';
  }

  // Semi-circle SVG parameters
  const radius = 80;
  const strokeWidth = 14;
  const circumference = Math.PI * radius; // Half-circle
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="text-center p-3">
      <div className="position-relative d-inline-block" style={{ width: 220, height: 125 }}>
        <svg width="220" height="125" viewBox="0 0 220 125">
          {/* Background Arc */}
          <path
            d="M 20 110 A 80 80 0 0 1 200 110"
            fill="none"
            stroke="#E2E8F0"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />
          {/* Progress Arc */}
          <path
            d="M 20 110 A 80 80 0 0 1 200 110"
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.8s ease, stroke 0.4s ease' }}
          />
        </svg>

        {/* Center Display */}
        <div
          className="position-absolute w-100"
          style={{ bottom: 0, left: 0, transform: 'translateY(-10px)' }}
        >
          <div className="display-6 fw-bold mb-0" style={{ color: '#0F172A', lineHeight: 1 }}>
            {rul.toFixed(1)}
          </div>
          <div className="text-muted text-uppercase fw-semibold" style={{ fontSize: '0.75rem', letterSpacing: '1px' }}>
            Flight Cycles Left
          </div>
        </div>
      </div>

      <div className="mt-2">
        <span className={`badge-status ${badgeClass} mb-1`}>
          {riskLabel}
        </span>
        <div className="small text-secondary">{riskDesc}</div>
      </div>

      <div className="d-flex justify-content-between mt-3 pt-2 border-top text-muted small" style={{ fontSize: '0.78rem' }}>
        <span>Current: Cycle {cycle}</span>
        <span>Safety Limit: 10 Cycles</span>
      </div>
    </div>
  );
}
