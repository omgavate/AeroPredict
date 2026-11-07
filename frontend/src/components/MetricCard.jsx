import React from 'react';

export default function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = 'blue',
  trend,
  trendPositive = true
}) {
  const variantStyles = {
    blue: {
      bg: '#EFF6FF',
      color: '#1D4ED8',
      border: '#BFDBFE'
    },
    emerald: {
      bg: '#ECFDF5',
      color: '#047857',
      border: '#A7F3D0'
    },
    amber: {
      bg: '#FFFBEB',
      color: '#B45309',
      border: '#FDE68A'
    },
    rose: {
      bg: '#FFF1F2',
      color: '#BE123C',
      border: '#FECDD3'
    },
    purple: {
      bg: '#FAF5FF',
      color: '#7E22CE',
      border: '#E9D5FF'
    }
  };

  const style = variantStyles[variant] || variantStyles.blue;

  return (
    <div className="stat-card aerocard-hover">
      <div className="flex-grow-1">
        <div className="stat-title">{title}</div>
        <div className="stat-value">{value}</div>
        {subtitle && (
          <div className="text-secondary small mt-1" style={{ fontSize: '0.8rem' }}>
            {subtitle}
          </div>
        )}
        {trend && (
          <div
            className="small mt-2 font-medium"
            style={{
              fontSize: '0.78rem',
              color: trendPositive ? '#059669' : '#DC2626'
            }}
          >
            {trend}
          </div>
        )}
      </div>
      {Icon && (
        <div
          className="stat-icon-wrapper ms-3"
          style={{
            backgroundColor: style.bg,
            color: style.color,
            border: `1px solid ${style.border}`
          }}
        >
          <Icon size={24} />
        </div>
      )}
    </div>
  );
}
