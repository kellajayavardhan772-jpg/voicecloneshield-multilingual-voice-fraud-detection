import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';

// Sub-component to programmatically change map zoom and view center
function MapController({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, zoom, { animate: true, duration: 0.8 });
    }
  }, [center, zoom, map]);
  return null;
}

export default function MapDashboard() {
  const [level, setLevel] = useState('world'); // world, country, state, district, city
  const [currentCountry, setCurrentCountry] = useState(null);
  const [currentState, setCurrentState] = useState(null);
  const [currentDistrict, setCurrentDistrict] = useState(null);
  
  const [mapCenter, setMapCenter] = useState([20, 0]);
  const [mapZoom, setMapZoom] = useState(2.2);
  const [markersData, setMarkersData] = useState([]);
  const [sidebarStats, setSidebarStats] = useState({ name: 'Global Statistics', cases: 0, active: 0, risk: 'Medium' });
  const [sidebarIncidents, setSidebarIncidents] = useState([]);

  // Fetch data depending on active drill-down level
  const loadMapData = async () => {
    try {
      let url = '/api/map/world';
      let statName = 'Global Statistics';

      if (level === 'world') {
        url = '/api/map/world';
        statName = 'Global Overview';
      } else if (level === 'country' && currentCountry) {
        url = `/api/map/country/${encodeURIComponent(currentCountry.country)}`;
        statName = currentCountry.country;
      } else if (level === 'state' && currentState) {
        url = `/api/map/state/${encodeURIComponent(currentState.state)}`;
        statName = currentState.state;
      } else if (level === 'district' && currentDistrict) {
        url = `/api/map/district/${encodeURIComponent(currentDistrict.district)}`;
        statName = currentDistrict.district;
      }

      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setMarkersData(data);
        
        // Sum total cases for sidebar
        const totalCases = data.reduce((acc, curr) => acc + (curr.fraudCases || curr.cases || 0), 0);
        setSidebarStats({
          name: statName,
          cases: totalCases,
          risk: totalCases > 1200 ? 'High' : totalCases > 500 ? 'Medium' : 'Low'
        });
      }

      // Load recent incidents for sidebar
      const resRecent = await fetch('/api/incidents/recent');
      if (resRecent.ok) {
        const recent = await resRecent.json();
        // Filter incidents based on active drill-down paths
        let filtered = recent;
        if (level === 'country' && currentCountry) {
          filtered = recent.filter(i => i.country === currentCountry.country);
        } else if (level === 'state' && currentState) {
          filtered = recent.filter(i => i.state === currentState.state);
        } else if (level === 'district' && currentDistrict) {
          filtered = recent.filter(i => i.district === currentDistrict.district);
        }
        setSidebarIncidents(filtered);
      }
    } catch (e) {
      console.error("Map loading error: ", e);
    }
  };

  useEffect(() => {
    loadMapData();
  }, [level, currentCountry, currentState, currentDistrict]);

  // Navigate drills
  const handleCountryClick = (c) => {
    setCurrentCountry(c);
    setMapCenter(c.coords || [20.5937, 78.9629]);
    setMapZoom(5);
    setLevel('country');
  };

  const handleStateClick = (s) => {
    setCurrentState(s);
    // Rough coordinates lookup based on state name for centering (mock fallback)
    const baseCoords = s.coords || [17.6868, 83.2185];
    setMapCenter(baseCoords);
    setMapZoom(7);
    setLevel('state');
  };

  const handleDistrictClick = (d) => {
    setCurrentDistrict(d);
    setLevel('district');
    setMapZoom(9);
  };

  const resetToWorld = () => {
    setLevel('world');
    setCurrentCountry(null);
    setCurrentState(null);
    setCurrentDistrict(null);
    setMapCenter([20, 0]);
    setMapZoom(2.2);
  };

  const backToCountry = () => {
    setLevel('country');
    setCurrentState(null);
    setCurrentDistrict(null);
    setMapZoom(5);
  };

  const backToState = () => {
    setLevel('state');
    setCurrentDistrict(null);
    setMapZoom(7);
  };

  // Helper color indicators
  const getMarkerColor = (cases) => {
    if (cases > 1000) return '#E5544A'; // Critical Red
    if (cases >= 400) return '#FF6A1F';  // Medium Orange
    if (cases >= 100) return '#f1c40f';  // Low Yellow
    return '#5FCB7A';                   // Minimal Green
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1.8fr 1fr', gap: '18px', marginBottom: '18px' }}>
      
      {/* MAP VIEW PANEL */}
      <div className="panel" style={{ padding: '0.85rem', position: 'relative', display: 'flex', flexDirection: 'column' }}>
        
        {/* Navigation Breadcrumbs */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'var(--bg2)',
          padding: '8px 16px',
          borderRadius: '8px',
          marginBottom: '10px',
          fontSize: '0.78rem',
          fontFamily: 'var(--font-mono)',
          border: '1px solid var(--border)'
        }}>
          <span style={{ color: 'var(--orange-light)', cursor: 'pointer' }} onClick={resetToWorld}>World</span>
          {currentCountry && (
            <>
              <span style={{ color: 'var(--muted)' }}>➔</span>
              <span style={{ color: 'var(--orange-light)', cursor: 'pointer' }} onClick={backToCountry}>{currentCountry.country}</span>
            </>
          )}
          {currentState && (
            <>
              <span style={{ color: 'var(--muted)' }}>➔</span>
              <span style={{ color: 'var(--orange-light)', cursor: 'pointer' }} onClick={backToState}>{currentState.state}</span>
            </>
          )}
          {currentDistrict && (
            <>
              <span style={{ color: 'var(--muted)' }}>➔</span>
              <span style={{ color: 'var(--text)' }}>{currentDistrict.district}</span>
            </>
          )}

          {level !== 'world' && (
            <button className="btn btn-primary" style={{ marginLeft: 'auto', padding: '2px 10px', borderRadius: '4px', fontSize: '9px' }} onClick={
              level === 'country' ? resetToWorld :
              level === 'state' ? backToCountry :
              backToState
            }>
              ⬅ Back
            </button>
          )}
        </div>

        <div style={{ height: '480px', borderRadius: '12px', border: '1px solid var(--border)', overflow: 'hidden', zIndex: 10 }}>
          <MapContainer center={mapCenter} zoom={mapZoom} zoomControl={true} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; OpenStreetMap &copy; CARTO'
            />
            <MapController center={mapCenter} zoom={mapZoom} />

            {/* Render geographic markers dynamically depending on active drill-down level */}
            {level === 'world' && markersData.map((m, idx) => (
              <CircleMarker
                key={`c-${idx}`}
                center={m.coords || [20,0]}
                radius={Math.max(6, Math.min(22, (m.fraudCases || 0) / 100))}
                fillColor={getMarkerColor(m.fraudCases)}
                color={getMarkerColor(m.fraudCases)}
                weight={2}
                opacity={0.8}
                fillOpacity={0.45}
                eventHandlers={{
                  click: () => handleCountryClick(m)
                }}
              >
                <Popup>
                  <div style={{ fontFamily: 'var(--font-body)', fontSize: '11px', color: 'var(--text)' }}>
                    <b style={{ fontSize: '13px', color: 'var(--orange-light)', display: 'block' }}>{m.country}</b>
                    <b>Total Incidents:</b> {m.fraudCases.toLocaleString()}<br />
                    <b>Active Campaigns:</b> {m.activeCases}<br />
                    <b>Monthly Growth:</b> +{m.growthRate}%
                  </div>
                </Popup>
              </CircleMarker>
            ))}

            {level === 'country' && markersData.map((m, idx) => (
              <CircleMarker
                key={`s-${idx}`}
                center={m.coords || mapCenter}
                radius={Math.max(8, Math.min(20, (m.fraudCases || 0) / 45))}
                fillColor={getMarkerColor(m.fraudCases)}
                color={getMarkerColor(m.fraudCases)}
                weight={2}
                opacity={0.8}
                fillOpacity={0.45}
                eventHandlers={{
                  click: () => handleStateClick(m)
                }}
              >
                <Popup>
                  <div style={{ fontFamily: 'var(--font-body)', fontSize: '11px', color: 'var(--text)' }}>
                    <b style={{ fontSize: '13px', color: 'var(--orange-light)', display: 'block' }}>{m.state}</b>
                    <b>Total Cases:</b> {m.fraudCases}<br />
                    <b>Risk Category:</b> <span className={`risk-pill risk-${m.riskLevel.toUpperCase()}`} style={{ fontSize: '8px' }}>{m.riskLevel}</span>
                  </div>
                </Popup>
              </CircleMarker>
            ))}

            {level === 'state' && markersData.map((m, idx) => (
              <CircleMarker
                key={`d-${idx}`}
                center={mapCenter}
                radius={Math.max(8, Math.min(22, (m.fraudCases || 0) / 10))}
                fillColor={getMarkerColor(m.fraudCases)}
                color={getMarkerColor(m.fraudCases)}
                weight={2}
                opacity={0.8}
                fillOpacity={0.45}
                eventHandlers={{
                  click: () => handleDistrictClick(m)
                }}
              >
                <Popup>
                  <div style={{ fontFamily: 'var(--font-body)', fontSize: '11px', color: 'var(--text)' }}>
                    <b style={{ fontSize: '13px', color: 'var(--orange-light)', display: 'block' }}>{m.district}</b>
                    <b>Fraud Cases:</b> {m.fraudCases}<br />
                    <b>Risk Category:</b> {m.riskLevel}
                  </div>
                </Popup>
              </CircleMarker>
            ))}

            {level === 'district' && markersData.map((m, idx) => (
              <CircleMarker
                key={`cty-${idx}`}
                center={[m.latitude, m.longitude]}
                radius={Math.max(6, Math.min(20, (m.fraudCases || 0) / 3))}
                fillColor={getMarkerColor(m.fraudCases * 50)}
                color={getMarkerColor(m.fraudCases * 50)}
                weight={2}
                opacity={0.8}
                fillOpacity={0.45}
              >
                <Popup>
                  <div style={{ fontFamily: 'var(--font-body)', fontSize: '11px', color: 'var(--text)' }}>
                    <b style={{ fontSize: '13px', color: 'var(--orange-light)', display: 'block' }}>{m.city}</b>
                    <b>City Cases:</b> {m.fraudCases}<br />
                    <b>Local Risk:</b> {m.riskLevel}
                  </div>
                </Popup>
              </CircleMarker>
            ))}

          </MapContainer>
        </div>
      </div>

      {/* STATE SIDEBAR PANEL */}
      <div className="panel" style={{ display: 'flex', flexDirection: 'column', minHeight: '520px' }}>
        <div className="panel-label">Dashboard View</div>
        <h3 id="sidebar-state-name">{sidebarStats.name}</h3>

        <div style={{ display: 'flex', gap: '12px', marginTop: '0.5rem', marginBottom: '1.5rem' }}>
          <div style={{ flex: '1', background: 'var(--bg2)', border: '1px solid var(--border)', padding: '10px', borderRadius: '10px', textAlign: 'center' }}>
            <span style={{ fontSize: '0.62rem', color: 'var(--muted)', fontFamily: 'var(--font-mono)', display: 'block' }}>REPORTS</span>
            <b style={{ fontSize: '1.25rem', color: 'var(--orange-light)', fontFamily: 'var(--font-mono)' }}>{sidebarStats.cases.toLocaleString()}</b>
          </div>
          <div style={{ flex: '1', background: 'var(--bg2)', border: '1px solid var(--border)', padding: '10px', borderRadius: '10px', textAlign: 'center', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
            <span style={{ fontSize: '0.62rem', color: 'var(--muted)', fontFamily: 'var(--font-mono)', display: 'block', marginBottom: '2px' }}>RISK</span>
            <span className={`risk-pill risk-${sidebarStats.risk.toUpperCase()}`} style={{ fontSize: '9px', fontWeight: '700' }}>
              {sidebarStats.risk}
            </span>
          </div>
        </div>

        <h4 style={{ fontFamily: 'var(--font-display)', fontSize: '0.85rem', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text)', marginBottom: '0.75rem', letterSpacing: '0.05em' }}>
          Active Campaigns
        </h4>

        {/* Incidents feed inside sidebar */}
        <div style={{ flex: 1, overflowY: 'auto', paddingRight: '4px' }} className="scroll-list">
          {sidebarIncidents.length === 0 ? (
            <div style={{ textAlign: 'center', color: 'var(--muted2)', fontSize: '0.78rem', padding: '2.5rem 1rem', fontFamily: 'var(--font-mono)' }}>
              No recent campaigns logged in this location bounds. Click state/regions to query sub-incidents.
            </div>
          ) : (
            sidebarIncidents.map((inc, idx) => (
              <div key={`side-inc-${idx}`} className="map-incident-item" style={{
                background: 'var(--bg2)',
                border: '1px solid rgba(58,51,44,0.4)',
                borderRadius: '8px',
                padding: '10px',
                marginBottom: '8px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--muted)', fontFamily: 'var(--font-mono)', marginBottom: '4px' }}>
                  <span style={{ fontWeight: '700', color: 'var(--orange-light)' }}>{inc.city}</span>
                  <span className={`risk-pill risk-${inc.riskLevel.toUpperCase()}`} style={{ fontSize: '8px', padding: '1px 5px' }}>{inc.riskLevel}</span>
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text)' }}>
                  Detected <b>{inc.fraudType}</b> attempts.
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', color: 'var(--muted2)', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>
                  <span>📅 {new Date(inc.createdAt).toLocaleDateString()}</span>
                  <span>👥 {inc.victims} victims</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

    </div>
  );
}
