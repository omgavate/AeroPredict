import React from 'react';
import { AlertCircle, AlertTriangle, Info, CheckCircle2 } from 'lucide-react';

export default function AlertCard({ alert, onResolve }) {
  const isCritical = alert.severity === 'CRITICAL';
  const isHigh = alert.severity === 'HIGH';
  const isResolved = alert.is_resolved;

  const getBorderColor = () => {
    if (isResolved) return '#CBD5E1';
    if (isCritical) return '#EF4444';
    if (isHigh) return '#F97316';
    return '#F59E0B';
  };

  const getBgColor = () => {
    if (isResolved) return '#F8FAFC';
    if (isCritical) return '#FEF2F2';
    if (isHigh) return '#FFF7ED';
    return '#FFFBEB';
  };

  const getIcon = () => {
    if (isResolved) return <CheckCircle2 size={18} className="text-secondary" />;
    if (isCritical) return <AlertCircle size={18} className="text-danger" />;
    if (isHigh) return <AlertTriangle size={18} className="text-warning" />;
    return <Info size={18} className="text-primary" />;
  };

  return (
    <div
      className="p-3 mb-3 rounded"
      style={{
        backgroundColor: getBgColor(),
        borderLeft: `4px solid ${getBorderColor()}`,
        borderTop: '1px solid #E2E8F0',
        borderRight: '1px solid #E2E8F0',
        borderBottom: '1px solid #E2E8F0',
        opacity: isResolved ? 0.75 : 1,
        transition: 'all 0.2s ease'
      }}
    >
      <div className="d-flex align-items-start justify-content-between gap-3">
        <div className="d-flex align-items-start gap-2">
          <div className="mt-1">{getIcon()}</div>
          <div>
            <div className="d-flex align-items-center gap-2 mb-1 flex-wrap">
              <span className="fw-bold text-dark" style={{ fontSize: '0.9rem' }}>
                {alert.tail_number}
              </span>
              <span
                className="badge rounded-pill"
                style={{
                  backgroundColor: isCritical ? '#FEE2E2' : '#FEF3C7',
                  color: isCritical ? '#991B1B' : '#92400E',
                  fontSize: '0.72rem'
                }}
              >
                {alert.alert_type}
              </span>
              {alert.cycle && (
                <span className="badge bg-light text-secondary border" style={{ fontSize: '0.7rem' }}>
                  Cycle {alert.cycle}
                </span>
              )}
            </div>
            <p className="mb-1 text-dark small" style={{ fontSize: '0.85rem' }}>
              {alert.message}
            </p>
            <div className="text-muted" style={{ fontSize: '0.74rem' }}>
              Logged: {alert.timestamp}
            </div>
          </div>
        </div>

        <div>
          {onResolve && !isResolved && (
            <button
              className="btn btn-sm btn-outline-secondary py-1 px-2"
              style={{ fontSize: '0.75rem' }}
              onClick={() => onResolve(alert.id)}
            >
              Acknowledge
            </button>
          )}
          {isResolved && (
            <span className="badge bg-secondary-subtle text-secondary" style={{ fontSize: '0.72rem' }}>
              Resolved
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
