import React from 'react';
import { CheckCircle2, AlertTriangle, AlertCircle, Clock, ShieldCheck, XCircle } from 'lucide-react';

export default function StatusBadge({ status, type = 'status' }) {
  if (!status) return null;

  if (type === 'risk') {
    switch (status.toUpperCase()) {
      case 'LOW':
        return (
          <span className="badge-status badge-risk-low">
            <ShieldCheck size={13} />
            <span>Low Risk</span>
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="badge-status badge-risk-medium">
            <Clock size={13} />
            <span>Medium Risk</span>
          </span>
        );
      case 'HIGH':
        return (
          <span className="badge-status badge-risk-high">
            <AlertTriangle size={13} />
            <span>High Risk</span>
          </span>
        );
      case 'CRITICAL':
        return (
          <span className="badge-status badge-risk-critical">
            <AlertCircle size={13} />
            <span>Critical Risk</span>
          </span>
        );
      default:
        return <span className="badge bg-secondary">{status}</span>;
    }
  }

  // Operational Aircraft Status
  switch (status.toUpperCase()) {
    case 'OPERATIONAL':
      return (
        <span className="badge-status badge-operational">
          <CheckCircle2 size={13} />
          <span>Operational</span>
        </span>
      );
    case 'UNDER_MAINTENANCE':
      return (
        <span className="badge-status badge-maintenance">
          <Clock size={13} />
          <span>In Maintenance</span>
        </span>
      );
    case 'ATTENTION_REQUIRED':
      return (
        <span className="badge-status badge-attention">
          <AlertTriangle size={13} />
          <span>Attention Required</span>
        </span>
      );
    case 'RETIRED':
      return (
        <span className="badge-status badge-retired">
          <XCircle size={13} />
          <span>Retired</span>
        </span>
      );
    default:
      return <span className="badge bg-light text-dark">{status}</span>;
  }
}
