import React from 'react';
import { Menu, Bell, Shield, Radio, RefreshCw } from 'lucide-react';

export default function Navbar({ onToggleSidebar, activeTitle = 'Operations Overview' }) {
  const currentTime = new Date().toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });

  return (
    <header className="top-navbar">
      <div className="d-flex align-items-center gap-3">
        <button
          className="btn btn-sm btn-outline-secondary d-lg-none"
          onClick={onToggleSidebar}
          aria-label="Toggle Navigation"
        >
          <Menu size={18} />
        </button>
        <div>
          <h5 className="mb-0 fw-bold text-dark" style={{ fontSize: '1.1rem' }}>
            {activeTitle}
          </h5>
          <div className="text-secondary small d-none d-md-block" style={{ fontSize: '0.78rem' }}>
            Aviation Turbofan Predictive Health System
          </div>
        </div>
      </div>

      <div className="d-flex align-items-center gap-3">
        {/* Simulation Clock */}
        <div
          className="d-none d-sm-flex align-items-center gap-2 px-3 py-1 rounded bg-light border"
          style={{ fontSize: '0.8rem' }}
        >
          <Radio size={14} className="text-primary" />
          <span className="text-secondary">UTC Flight Clock:</span>
          <span className="fw-mono fw-bold text-dark">{currentTime}</span>
        </div>

        {/* Demo Indicator */}
        <span
          className="badge d-none d-md-inline-block py-2 px-3 rounded-pill text-uppercase"
          style={{
            backgroundColor: '#EFF6FF',
            color: '#1D4ED8',
            border: '1px solid #BFDBFE',
            fontSize: '0.72rem',
            letterSpacing: '0.5px'
          }}
        >
          ● Demo Simulation Active
        </span>

        {/* Alerts Pill */}
        <div
          className="d-flex align-items-center gap-2 px-2 py-1 rounded"
          style={{ backgroundColor: '#FEF2F2', border: '1px solid #FECDD3' }}
        >
          <Bell size={16} className="text-danger" />
          <span className="small fw-bold text-danger">2 Critical</span>
        </div>
      </div>
    </header>
  );
}
