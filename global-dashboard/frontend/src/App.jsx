import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import MapDashboard from './components/MapDashboard';
import SearchFilters from './components/SearchFilters';
import AnalyticsPanel from './components/AnalyticsPanel';
import PredictionPanel from './components/PredictionPanel';
import IncidentFeed from './components/IncidentFeed';

const socket = io(window.location.hostname === 'localhost' ? 'http://localhost:5000' : window.location.origin);

function App() {
  const [activeTab, setActiveTab] = useState('map');
  const [theme, setTheme] = useState('dark');
  
  // Real-time animated counters state
  const [stats, setStats] = useState({
    globalFraudIncidents: 0,
    aiVoiceCloneAttempts: 0,
    confirmedFraudCases: 0,
    countriesAffected: 0,
    highRiskRegions: 0,
    monthlyGrowthRatePercent: 0,
    globalRiskScore: 0
  });

  const [recentIncidents, setRecentIncidents] = useState([]);
  const [newIncidentAlert, setNewIncidentAlert] = useState(null);

  // Toggle theme helper
  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    document.documentElement.setAttribute('data-theme', nextTheme);
  };

  // Fetch initial dashboard metrics
  const fetchStats = async () => {
    try {
      const res = await fetch('/api/dashboard/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
      
      const resRecent = await fetch('/api/incidents/recent');
      if (resRecent.ok) {
        const dataRecent = await resRecent.json();
        setRecentIncidents(dataRecent);
      }
    } catch (e) {
      console.error("Failed to load dashboard metrics:", e);
    }
  };

  useEffect(() => {
    fetchStats();

    // Set default dark theme
    document.documentElement.setAttribute('data-theme', 'dark');

    // Bind Socket.IO listeners
    socket.on('new-incident', (incident) => {
      // Trigger dynamic increment animations
      setStats(prev => ({
        ...prev,
        globalFraudIncidents: prev.globalFraudIncidents + 1,
        aiVoiceCloneAttempts: prev.aiVoiceCloneAttempts + 2,
        confirmedFraudCases: prev.confirmedFraudCases + incident.victims
      }));

      // Add to recent feed
      setRecentIncidents(prev => [incident, ...prev].slice(0, 15));

      // Trigger custom toast pop notification
      setNewIncidentAlert(incident);
      setTimeout(() => setNewIncidentAlert(null), 5000);
    });

    return () => {
      socket.off('new-incident');
    };
  }, []);

  return (
    <div>
      <header>
        <div class="wrap nav">
          <a class="brand" href="/" onClick={(e) => { e.preventDefault(); setActiveTab('map'); }}>
            <div class="brand-mark">
              <svg viewBox="0 0 24 24" fill="none" width="20" height="20">
                <path d="M12 2L4 5v6c0 5 3.5 8.5 8 10 4.5-1.5 8-5 8-10V5l-8-3z" stroke="#FF6A1F" strokeWidth="1.8" strokeLinejoin="round"/>
                <path d="M9 12l2 2 4-4.5" stroke="#FFAB6B" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <span class="brand-name">Voice<span>Clone</span>Shield</span>
          </a>

          <nav class="navlinks">
            <a class={`navlink ${activeTab === 'map' ? 'is-active' : ''}`} onClick={() => setActiveTab('map')}>Heat Map</a>
            <a class={`navlink ${activeTab === 'search' ? 'is-active' : ''}`} onClick={() => setActiveTab('search')}>Incident Database</a>
            <a class={`navlink ${activeTab === 'analytics' ? 'is-active' : ''}`} onClick={() => setActiveTab('analytics')}>Analytics</a>
            <a class={`navlink ${activeTab === 'predictions' ? 'is-active' : ''}`} onClick={() => setActiveTab('predictions')}>AI Forecasts</a>
          </nav>

          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--muted)', fontFamily: 'var(--font-mono)', border: '1px solid var(--border)', padding: '6px 12px', borderRadius: '99px' }}>
              📡 LIVE SYNC ACTIVE
            </span>
            <button className="theme-btn" onClick={toggleTheme} title="Switch Theme">
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
          </div>
        </div>
      </header>

      {/* Main Stats Counters Banner */}
      <section style={{ background: 'var(--bg2)', borderBottom: '1px solid var(--border)', padding: '1.5rem 0' }}>
        <div className="wrap">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
            
            <div style={{ borderRight: '1px solid var(--border)', paddingRight: '10px' }}>
              <span style={{ fontSize: '0.62rem', color: 'var(--muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', display: 'block' }}>Global Incidents</span>
              <span style={{ fontSize: '1.65rem', fontFamily: 'var(--font-mono)', fontWeight: '700', color: 'var(--orange-light)' }}>
                {stats.globalFraudIncidents.toLocaleString()}
              </span>
            </div>

            <div style={{ borderRight: '1px solid var(--border)', paddingRight: '10px' }}>
              <span style={{ fontSize: '0.62rem', color: 'var(--muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', display: 'block' }}>Clone Attempts</span>
              <span style={{ fontSize: '1.65rem', fontFamily: 'var(--font-mono)', fontWeight: '700', color: 'var(--text)' }}>
                {stats.aiVoiceCloneAttempts.toLocaleString()}
              </span>
            </div>

            <div style={{ borderRight: '1px solid var(--border)', paddingRight: '10px' }}>
              <span style={{ fontSize: '0.62rem', color: 'var(--muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', display: 'block' }}>Confirmed Victims</span>
              <span style={{ fontSize: '1.65rem', fontFamily: 'var(--font-mono)', fontWeight: '700', color: 'var(--red)' }}>
                {stats.confirmedFraudCases.toLocaleString()}
              </span>
            </div>

            <div style={{ borderRight: '1px solid var(--border)', paddingRight: '10px' }}>
              <span style={{ fontSize: '0.62rem', color: 'var(--muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', display: 'block' }}>Countries Impacted</span>
              <span style={{ fontSize: '1.65rem', fontFamily: 'var(--font-mono)', fontWeight: '700', color: 'var(--text)' }}>
                {stats.countriesAffected}
              </span>
            </div>

            <div>
              <span style={{ fontSize: '0.62rem', color: 'var(--muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', display: 'block' }}>Global Risk Score</span>
              <span style={{ fontSize: '1.65rem', fontFamily: 'var(--font-mono)', fontWeight: '700', color: 'var(--orange)' }}>
                {stats.globalRiskScore}/100
              </span>
            </div>

          </div>
        </div>
      </section>

      {/* Main Page Rendering */}
      <main className="wrap" style={{ marginTop: '2.5rem', minHeight: '60vh' }}>
        
        {/* Demonstration Data Warning Label */}
        <div style={{ background: 'rgba(255,106,31,0.06)', border: '1px solid var(--orange-dim)', borderRadius: '12px', padding: '10px 18px', marginBottom: '1.5rem', fontSize: '0.78rem', color: 'var(--orange-light)', fontFamily: 'var(--font-mono)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>⚠️</span> <strong>AI Voice Fraud Intelligence Dashboard – Demonstration Dataset</strong> (Simulated/research records for educational evaluation)
        </div>

        {activeTab === 'map' && <MapDashboard onStateClick={() => {}} />}
        {activeTab === 'search' && <SearchFilters />}
        {activeTab === 'analytics' && <AnalyticsPanel />}
        {activeTab === 'predictions' && <PredictionPanel />}
        
        {/* Global Live Feed Sidebar Panel */}
        <div style={{ marginTop: '2.5rem' }}>
          <IncidentFeed incidents={recentIncidents} />
        </div>
      </main>

      {/* Dynamic Toast Alert (feature 3 popup) */}
      {newIncidentAlert && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          background: 'var(--card)',
          border: '1.5px solid var(--red)',
          borderRadius: '12px',
          padding: '14px 20px',
          zIndex: 10000,
          boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
          maxWidth: '350px',
          fontFamily: 'var(--font-mono)',
          fontSize: '12px',
          animation: 'slideUp 0.3s ease-out'
        }}>
          <div style={{ display: 'flex', justifyContent: 'between', alignItems: 'center', marginBottom: '6px' }}>
            <span style={{ fontWeight: '700', color: 'var(--red)', fontSize: '13px' }}>🚨 LIVE SCAM DETECTED</span>
            <span className="risk-pill risk-CRITICAL" style={{ marginLeft: 'auto', fontSize: '9px' }}>CRITICAL</span>
          </div>
          <div>
            <b>ID:</b> {newIncidentAlert.incidentId}<br />
            <b>Location:</b> {newIncidentAlert.city}, {newIncidentAlert.state}, {newIncidentAlert.country}<br />
            <b>Scam Type:</b> {newIncidentAlert.fraudType}<br />
            <b>Victims:</b> {newIncidentAlert.victims}
          </div>
        </div>
      )}

      <footer>
        <b>VoiceClone Shield</b> &nbsp;·&nbsp; <span>IBM Internship Project</span> &nbsp;·&nbsp; Global AI Voice Fraud Intelligence Dashboard v2.0
      </footer>
    </div>
  );
}

export default App;
