import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Plane,
  Activity,
  Cpu,
  Wrench,
  ShieldCheck,
  Radio
} from 'lucide-react';

export default function Sidebar({ isOpen, onClose }) {
  const navItems = [
    {
      to: '/',
      label: 'Executive Dashboard',
      icon: LayoutDashboard,
      badge: null
    },
    {
      to: '/aircraft',
      label: 'Fleet Management',
      icon: Plane,
      badge: '6'
    },
    {
      to: '/monitoring',
      label: 'Engine Telemetry',
      icon: Activity,
      badge: 'Live'
    },
    {
      to: '/predictive',
      label: 'Predictive Maintenance',
      icon: Cpu,
      badge: 'RUL'
    },
    {
      to: '/maintenance',
      label: 'Maintenance Orders',
      icon: Wrench,
      badge: '2 Due'
    }
  ];

  return (
    <aside className={`app-sidebar ${isOpen ? 'show' : ''}`}>
      {/* Brand Header */}
      <div className="sidebar-brand">
        <div
          className="d-flex align-items-center justify-content-center rounded"
          style={{
            width: 38,
            height: 38,
            backgroundColor: '#194391',
            color: '#FFFFFF'
          }}
        >
          <Radio size={20} />
        </div>
        <div>
          <div className="fw-bold" style={{ fontSize: '1.1rem', letterSpacing: '0.5px' }}>
            AeroPredict
          </div>
          <div className="text-secondary" style={{ fontSize: '0.68rem', letterSpacing: '0.8px' }}>
            ENGINE HEALTH MONITOR
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="sidebar-nav">
        <div
          className="text-uppercase fw-semibold px-3 mb-2"
          style={{ fontSize: '0.68rem', color: '#64748B', letterSpacing: '0.8px' }}
        >
          Main Navigation
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              className={({ isActive }) =>
                `nav-item-link ${isActive ? 'active' : ''}`
              }
            >
              <Icon size={19} />
              <span className="flex-grow-1">{item.label}</span>
              {item.badge && (
                <span
                  className="badge rounded-pill"
                  style={{
                    backgroundColor:
                      item.badge === 'RUL' || item.badge === 'Live'
                        ? 'rgba(59, 130, 246, 0.25)'
                        : 'rgba(255, 255, 255, 0.1)',
                    color: item.badge === 'RUL' || item.badge === 'Live' ? '#60A5FA' : '#E2E8F0',
                    fontSize: '0.7rem'
                  }}
                >
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </div>

      {/* System Status Footer */}
      <div className="p-3 mt-auto border-top border-secondary border-opacity-10">
        <div
          className="p-3 rounded"
          style={{ backgroundColor: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.08)' }}
        >
          <div className="d-flex align-items-center gap-2 mb-1">
            <span
              className="d-inline-block rounded-circle"
              style={{ width: 8, height: 8, backgroundColor: '#10B981' }}
            />
            <span className="small fw-semibold text-light">Telemetry Stream Active</span>
          </div>
          <div className="text-muted" style={{ fontSize: '0.72rem' }}>
            NASA C-MAPSS FD001 Hub
          </div>
        </div>
      </div>
    </aside>
  );
}
