import React, { useState, useEffect } from 'react';

export default function PredictionPanel() {
  const [predictions, setPredictions] = useState({
    highRiskCountries: [],
    highRiskStates: [],
    predictedHotspots: []
  });
  const [loading, setLoading] = useState(true);

  const fetchPredictions = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/predictions');
      if (res.ok) {
        const data = await res.json();
        setPredictions(data);
      }
    } catch (e) {
      console.error("Failed to load predictions: ", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPredictions();
  }, []);

  if (loading) {
    return (
      <div className="panel" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '300px' }}>
        <span style={{ fontSize: '2rem', animation: 'spin 1s linear infinite', display: 'inline-block', marginBottom: '10px' }}>⏳</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', color: 'var(--muted)' }}>Calculating predictive forecasting vectors...</span>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Overview Intro Banner */}
      <div className="panel" style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px', alignItems: 'center' }}>
        <div>
          <div className="panel-label">Cognitive Forecasting</div>
          <h3>🧠 Machine Learning Incident Projections</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--muted)', lineHeight: '1.7' }}>
            This predictive engine analyzes historical incident frequencies, spatial density clusters, and growth velocities to forecast emerging threat levels. Values indicate target probabilities for high-frequency cloning operations in the next quarterly cycle.
          </p>
        </div>
        <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '14px', textAlign: 'center' }}>
          <span style={{ fontSize: '0.65rem', color: 'var(--muted)', display: 'block', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>AI Engine Confidence</span>
          <b style={{ fontSize: '1.75rem', color: 'var(--orange-light)', fontFamily: 'var(--font-mono)' }}>91.4%</b>
          <div style={{ height: '6px', background: 'var(--border)', borderRadius: '99px', overflow: 'hidden', marginTop: '6px' }}>
            <div style={{ height: '100%', background: 'var(--orange)', width: '91.4%' }}></div>
          </div>
        </div>
      </div>

      {/* Forecast Lists Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '18px' }}>
        
        {/* Next High Risk Countries */}
        <div className="panel">
          <div className="panel-label">High-Risk Forecast (Countries)</div>
          <h3>Next High-Risk Countries</h3>
          <div style={{ overflowY: 'auto', maxHeight: '350px' }} className="scroll-list">
            {predictions.highRiskCountries.map((c, idx) => (
              <div key={`pred-c-${idx}`} style={{
                background: 'var(--bg2)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '12px',
                marginBottom: '10px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: '700', fontSize: '0.85rem', marginBottom: '6px' }}>
                  <span>{c.country}</span>
                  <span style={{ color: 'var(--orange-light)' }}>Risk Score: {c.predictedScore}/100</span>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--muted)', fontFamily: 'var(--font-mono)', marginBottom: '4px' }}>
                  <span>Growth Velocity: <b style={{ color: c.predictedGrowth > 0 ? 'var(--red)' : 'var(--green)' }}>+{c.predictedGrowth}%</b></span>
                  <span>Confidence: {c.confidence}%</span>
                </div>

                <div style={{ height: '4px', background: 'var(--border)', borderRadius: '99px', overflow: 'hidden', marginTop: '4px' }}>
                  <div style={{
                    height: '100%',
                    background: c.predictedScore > 75 ? 'var(--red)' : c.predictedScore > 40 ? 'var(--orange)' : 'var(--green)',
                    width: `${c.predictedScore}%`
                  }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Next High Risk States */}
        <div className="panel">
          <div className="panel-label">High-Risk Forecast (Regions)</div>
          <h3>Next High-Risk Regions</h3>
          <div style={{ overflowY: 'auto', maxHeight: '350px' }} className="scroll-list">
            {predictions.highRiskStates.map((s, idx) => (
              <div key={`pred-s-${idx}`} style={{
                background: 'var(--bg2)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '12px',
                marginBottom: '10px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: '700', fontSize: '0.85rem', marginBottom: '6px' }}>
                  <span>{s.state}</span>
                  <span style={{ color: 'var(--muted)', fontSize: '0.78rem' }}>{s.country}</span>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--muted)', fontFamily: 'var(--font-mono)', marginBottom: '4px' }}>
                  <span>Risk Score: {s.predictedScore}/100</span>
                  <span>Forecast growth: <b style={{ color: 'var(--red)' }}>+{s.predictedGrowth}%</b></span>
                </div>

                <div style={{ height: '4px', background: 'var(--border)', borderRadius: '99px', overflow: 'hidden', marginTop: '4px' }}>
                  <div style={{
                    height: '100%',
                    background: s.predictedScore > 75 ? 'var(--red)' : s.predictedScore > 40 ? 'var(--orange)' : 'var(--green)',
                    width: `${s.predictedScore}%`
                  }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Future Hotspot Locations */}
        <div className="panel">
          <div className="panel-label">Emerging Hotspot Projections</div>
          <h3>Predicted Hotspot Cities</h3>
          <div style={{ overflowY: 'auto', maxHeight: '350px' }} className="scroll-list">
            {predictions.predictedHotspots.map((h, idx) => (
              <div key={`pred-h-${idx}`} style={{
                background: 'var(--bg2)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '12px',
                marginBottom: '10px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: '700', fontSize: '0.85rem', marginBottom: '6px' }}>
                  <span style={{ color: 'var(--orange-light)' }}>{h.location}</span>
                  <span style={{ color: 'var(--muted)', fontSize: '0.74rem' }}>{h.country}</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--muted)', fontFamily: 'var(--font-mono)', marginBottom: '4px' }}>
                  <span>Hotspot Probability: <b>{h.probability}%</b></span>
                  <span>Predicted growth: <b>+{h.growthRate}%</b></span>
                </div>

                <div style={{ height: '4px', background: 'var(--border)', borderRadius: '99px', overflow: 'hidden', marginTop: '4px' }}>
                  <div style={{
                    height: '100%',
                    background: h.probability > 75 ? 'var(--red)' : h.probability > 40 ? 'var(--orange)' : 'var(--green)',
                    width: `${h.probability}%`
                  }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

    </div>
  );
}
