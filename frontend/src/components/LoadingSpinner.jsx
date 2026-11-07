import React from 'react';

export default function LoadingSpinner({ message = 'Loading engine telemetry...' }) {
  return (
    <div className="d-flex flex-column align-items-center justify-content-center p-5 text-center">
      <div className="spinner-border text-primary mb-3" role="status" style={{ width: '2.5rem', height: '2.5rem' }}>
        <span className="visually-hidden">Loading...</span>
      </div>
      <div className="text-secondary small fw-medium">{message}</div>
    </div>
  );
}
