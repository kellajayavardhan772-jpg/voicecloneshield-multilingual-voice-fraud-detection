import React from 'react';

export default function IncidentFeed({ incidents }) {
  return (
    <div className="panel">
      <div className="panel-label">Live Activity Feed</div>
      <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        📢 Real-Time AI Fraud Incident Stream
        <span style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          background: 'var(--green)',
          display: 'inline-block',
          boxShadow: '0 0 10px var(--green)',
          animation: 'blink 2s infinite'
        }}></span>
      </h3>
      
      <div style={{
        display: 'flex',
        gap: '12px',
        overflowX: 'auto',
        padding: '10px 0',
        scrollSnapType: 'x mandatory'
      }} className="scroll-list">
        {incidents.length === 0 ? (
          <div style={{ padding: '1rem', color: 'var(--muted)', fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
            Awaiting live incident telemetry streams...
          </div>
        ) : (
          incidents.map((inc, idx) => (
            <div key={`ticker-${idx}`} style={{
              flex: '0 0 260px',
              scrollSnapAlign: 'start',
              background: 'var(--bg2)',
              border: '1px solid var(--border)',
              borderRadius: '12px',
              padding: '12px',
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              position: 'relative',
              overflow: 'hidden'
            }}>
              {/* Risk indicator bar */}
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                bottom: 0,
                width: '4px',
                background: inc.riskLevel === 'Critical' ? '#FF4D4D' : inc.riskLevel === 'High' ? 'var(--red)' : inc.riskLevel === 'Medium' ? 'var(--orange)' : 'var(--green)'
              }}></div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', paddingLeft: '6px' }}>
                <span style={{ fontWeight: '700', color: 'var(--orange-light)' }}>{inc.incidentId}</span>
                <span className={`risk-pill risk-${inc.riskLevel.toUpperCase()}`} style={{ fontSize: '8px', padding: '1px 5px' }}>{inc.riskLevel}</span>
              </div>
              <div style={{ color: 'var(--text)', paddingLeft: '6px', fontSize: '12px', fontWeight: '500', margin: '4px 0' }}>
                {inc.city}, {inc.state}
              </div>
              <div style={{ color: 'var(--muted)', paddingLeft: '6px', fontSize: '10px' }}>
                <b>Type:</b> {inc.fraudType}<br />
                <b>Victims:</b> {inc.victims}<br />
                <b>Date:</b> {new Date(inc.createdAt).toLocaleTimeString()}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
