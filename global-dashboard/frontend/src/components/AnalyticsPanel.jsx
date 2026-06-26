import React, { useState, useEffect } from 'react';
import { Bar, Pie, Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
);

export default function AnalyticsPanel() {
  const [topCountries, setTopCountries] = useState([]);
  const [topStates, setTopStates] = useState([]);
  const [topCities, setTopCities] = useState([]);

  const fetchAnalytics = async () => {
    try {
      const resCountries = await fetch('/api/dashboard/top-countries');
      const resStates = await fetch('/api/dashboard/top-states');
      const resCities = await fetch('/api/dashboard/top-cities');

      if (resCountries.ok) setTopCountries(await resCountries.json());
      if (resStates.ok) setTopStates(await resStates.json());
      if (resCities.ok) setTopCities(await resCities.json());
    } catch (e) {
      console.error("Failed to load analytics: ", e);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  // Top Countries Chart Data
  const barChartData = {
    labels: topCountries.slice(0, 5).map(c => c.country),
    datasets: [{
      label: 'Fraud Cases',
      data: topCountries.slice(0, 5).map(c => c.fraudCases),
      backgroundColor: [
        'rgba(229, 84, 74, 0.75)',
        'rgba(255, 106, 31, 0.75)',
        'rgba(255, 171, 107, 0.75)',
        'rgba(241, 196, 15, 0.75)',
        'rgba(95, 203, 122, 0.75)'
      ],
      borderColor: ['#E5544A', '#FF6A1F', '#FFAB6B', '#f1c40f', '#5FCB7A'],
      borderWidth: 1.5,
      borderRadius: 6
    }]
  };

  // Risk Distribution Chart Data
  const pieChartData = {
    labels: ['High Risk', 'Medium Risk', 'Low Risk'],
    datasets: [{
      data: [
        topCountries.filter(c => c.riskScore > 75).length,
        topCountries.filter(c => c.riskScore <= 75 && c.riskScore >= 40).length,
        topCountries.filter(c => c.riskScore < 40).length
      ],
      backgroundColor: [
        'rgba(229, 84, 74, 0.8)',
        'rgba(255, 106, 31, 0.8)',
        'rgba(95, 203, 122, 0.8)'
      ],
      borderColor: 'var(--card)',
      borderWidth: 2
    }]
  };

  // Trend line Chart Data (simulated historical monthly fraud counts)
  const lineChartData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [{
      label: 'Cloning Incidents (Monthly)',
      data: [1200, 1850, 2400, 3100, 4200, 5600],
      borderColor: '#FF6A1F',
      backgroundColor: 'rgba(255, 106, 31, 0.15)',
      fill: true,
      tension: 0.4,
      pointRadius: 4,
      pointHoverRadius: 6
    }]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: '#9A8F80',
          font: { family: 'Space Grotesk', size: 9 }
        }
      },
      tooltip: {
        backgroundColor: '#1A1614',
        titleColor: '#FFAB6B',
        bodyColor: '#E8E2D8',
        borderColor: '#3A332C',
        borderWidth: 1
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(58, 51, 44, 0.15)' },
        ticks: { color: '#9A8F80', font: { family: 'Inter', size: 9 } }
      },
      y: {
        grid: { color: 'rgba(58, 51, 44, 0.15)' },
        ticks: { color: '#9A8F80', font: { family: 'JetBrains Mono', size: 9 } }
      }
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Visual Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '18px' }}>
        
        <div className="panel" style={{ height: '300px' }}>
          <div className="panel-label">Visual Analytics</div>
          <h3>Top Affected Nations</h3>
          <div style={{ height: '200px' }}>
            <Bar data={barChartData} options={{ ...chartOptions, plugins: { ...chartOptions.plugins, legend: { display: false } } }} />
          </div>
        </div>

        <div className="panel" style={{ height: '300px' }}>
          <div className="panel-label">Risk Segments</div>
          <h3>Global Risk Distribution</h3>
          <div style={{ height: '200px' }}>
            <Pie data={pieChartData} options={{ ...chartOptions, scales: { x: { display: false }, y: { display: false } } }} />
          </div>
        </div>

        <div className="panel" style={{ height: '300px' }}>
          <div className="panel-label">Fraud Trend</div>
          <h3>Growth Graph (Monthly)</h3>
          <div style={{ height: '200px' }}>
            <Line data={lineChartData} options={chartOptions} />
          </div>
        </div>

      </div>

      {/* Leaderboard Lists Column */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '18px' }}>
        
        {/* Top Countries */}
        <div className="panel">
          <div className="panel-label">Leaderboards</div>
          <h3>Top 10 Affected Countries</h3>
          <div style={{ overflowX: 'auto', maxHeight: '350px' }} className="scroll-list">
            <table>
              <thead>
                <tr>
                  <th>Country</th>
                  <th>Cases</th>
                  <th>Risk Score</th>
                </tr>
              </thead>
              <tbody>
                {topCountries.slice(0, 10).map((c, idx) => (
                  <tr key={`tc-${idx}`}>
                    <td style={{ fontWeight: '600' }}>{c.country}</td>
                    <td style={{ color: 'var(--orange-light)' }}>{c.fraudCases.toLocaleString()}</td>
                    <td><span className={`risk-pill risk-${c.riskScore > 75 ? 'HIGH' : c.riskScore > 40 ? 'MEDIUM' : 'LOW'}`}>{c.riskScore}/100</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Top States */}
        <div className="panel">
          <div className="panel-label">Regional Breakdown</div>
          <h3>Top 10 Affected Regions</h3>
          <div style={{ overflowX: 'auto', maxHeight: '350px' }} className="scroll-list">
            <table>
              <thead>
                <tr>
                  <th>State/Region</th>
                  <th>Country</th>
                  <th>Cases</th>
                </tr>
              </thead>
              <tbody>
                {topStates.slice(0, 10).map((s, idx) => (
                  <tr key={`ts-${idx}`}>
                    <td style={{ fontWeight: '600' }}>{s.state}</td>
                    <td style={{ color: 'var(--muted)' }}>{s.country}</td>
                    <td style={{ color: 'var(--orange-light)' }}>{s.fraudCases.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Top Cities */}
        <div className="panel">
          <div className="panel-label">Localized Breakdown</div>
          <h3>Top 10 Targeted Cities</h3>
          <div style={{ overflowX: 'auto', maxHeight: '350px' }} className="scroll-list">
            <table>
              <thead>
                <tr>
                  <th>City</th>
                  <th>District</th>
                  <th>Cases</th>
                </tr>
              </thead>
              <tbody>
                {topCities.slice(0, 10).map((c, idx) => (
                  <tr key={`tci-${idx}`}>
                    <td style={{ fontWeight: '600' }}>{c.city}</td>
                    <td style={{ color: 'var(--muted)' }}>{c.district}</td>
                    <td style={{ color: 'var(--orange-light)' }}>{c.fraudCases.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>

    </div>
  );
}
