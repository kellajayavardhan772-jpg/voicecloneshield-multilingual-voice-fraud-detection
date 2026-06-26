import React, { useState, useEffect } from 'react';

export default function SearchFilters() {
  const [filters, setFilters] = useState({
    country: '',
    state: '',
    district: '',
    city: '',
    dateRange: '',
    fraudType: ''
  });

  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const executeSearch = async () => {
    setLoading(true);
    try {
      const queryParams = new URLSearchParams();
      if (filters.country) queryParams.append('country', filters.country);
      if (filters.state) queryParams.append('state', filters.state);
      if (filters.district) queryParams.append('district', filters.district);
      if (filters.city) queryParams.append('city', filters.city);
      if (filters.dateRange) queryParams.append('dateRange', filters.dateRange);
      if (filters.fraudType) queryParams.append('fraudType', filters.fraudType);

      const res = await fetch(`/api/search?${queryParams.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setResults(data);
      }
    } catch (e) {
      console.error("Incident search query error:", e);
    } finally {
      setLoading(false);
    }
  };

  // Run initial search on mount
  useEffect(() => {
    executeSearch();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Filtering selectors Panel */}
      <div className="panel">
        <div className="panel-label">Database Query</div>
        <h3>🔍 Search & Filter Incident Records</h3>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '14px',
          alignItems: 'end'
        }}>
          
          <div>
            <label style={{ display: 'block', fontSize: '0.72rem', color: 'var(--muted)', marginBottom: '4px', fontFamily: 'var(--font-mono)' }}>Country</label>
            <input
              type="text"
              name="country"
              value={filters.country}
              onChange={handleInputChange}
              placeholder="e.g. India"
              style={{ width: '100%', padding: '8px 14px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg2)', color: 'var(--text)' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.72rem', color: 'var(--muted)', marginBottom: '4px', fontFamily: 'var(--font-mono)' }}>State/Region</label>
            <input
              type="text"
              name="state"
              value={filters.state}
              onChange={handleInputChange}
              placeholder="e.g. Andhra Pradesh"
              style={{ width: '100%', padding: '8px 14px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg2)', color: 'var(--text)' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.72rem', color: 'var(--muted)', marginBottom: '4px', fontFamily: 'var(--font-mono)' }}>District</label>
            <input
              type="text"
              name="district"
              value={filters.district}
              onChange={handleInputChange}
              placeholder="e.g. Visakhapatnam"
              style={{ width: '100%', padding: '8px 14px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg2)', color: 'var(--text)' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.72rem', color: 'var(--muted)', marginBottom: '4px', fontFamily: 'var(--font-mono)' }}>City</label>
            <input
              type="text"
              name="city"
              value={filters.city}
              onChange={handleInputChange}
              placeholder="e.g. Gajuwaka"
              style={{ width: '100%', padding: '8px 14px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg2)', color: 'var(--text)' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.72rem', color: 'var(--muted)', marginBottom: '4px', fontFamily: 'var(--font-mono)' }}>Date Range</label>
            <select
              name="dateRange"
              value={filters.dateRange}
              onChange={handleInputChange}
              style={{ width: '100%', padding: '8px 14px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg2)', color: 'var(--text)' }}
            >
              <option value="">All Time</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="6m">Last 6 Months</option>
              <option value="1y">Last 1 Year</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.72rem', color: 'var(--muted)', marginBottom: '4px', fontFamily: 'var(--font-mono)' }}>Fraud Type</label>
            <input
              type="text"
              name="fraudType"
              value={filters.fraudType}
              onChange={handleInputChange}
              placeholder="e.g. Voice Clone"
              style={{ width: '100%', padding: '8px 14px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg2)', color: 'var(--text)' }}
            />
          </div>

          <div>
            <button className="btn btn-primary btn-block" onClick={executeSearch} disabled={loading}>
              {loading ? 'Searching...' : '🔍 Execute Query'}
            </button>
          </div>

        </div>
      </div>

      {/* Results Table Panel */}
      <div className="panel">
        <div className="panel-label">Telemetry Output</div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.2rem' }}>
          <h3>📋 Query Results ({results.length} records found)</h3>
          <span style={{ fontSize: '0.7rem', color: 'var(--muted)', fontFamily: 'var(--font-mono)' }}>Max Limit: 200 records</span>
        </div>

        <div style={{ overflowX: 'auto', maxHeight: '450px' }} className="scroll-list">
          <table>
            <thead>
              <tr>
                <th>Incident ID</th>
                <th>Timestamp</th>
                <th>Location</th>
                <th>Fraud Type</th>
                <th>Victims</th>
                <th>Risk Level</th>
              </tr>
            </thead>
            <tbody>
              {results.length === 0 ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', color: 'var(--muted2)', padding: '3rem 0', fontFamily: 'var(--font-mono)' }}>
                    No incident logs match your query parameters.
                  </td>
                </tr>
              ) : (
                results.map((inc, idx) => (
                  <tr key={`inc-row-${idx}`}>
                    <td style={{ color: 'var(--orange-light)', fontWeight: '600' }}>{inc.incidentId}</td>
                    <td>{new Date(inc.createdAt).toLocaleString()}</td>
                    <td>{inc.city}, {inc.state}, {inc.country}</td>
                    <td>{inc.fraudType}</td>
                    <td style={{ fontWeight: '700' }}>{inc.victims}</td>
                    <td>
                      <span className={`risk-pill risk-${inc.riskLevel.toUpperCase()}`}>
                        {inc.riskLevel}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
