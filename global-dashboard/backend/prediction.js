import { USE_MOCK, mockDb } from './db.js';
import { Country, State, Incident } from './models.js';

export async function getPredictions() {
  let countries = [];
  let states = [];
  let incidents = [];

  if (USE_MOCK) {
    countries = mockDb.countries;
    states = mockDb.states;
    incidents = mockDb.incidents;
  } else {
    countries = await Country.find().lean();
    states = await State.find().lean();
    incidents = await Incident.find().lean();
  }

  // If no data is available, return empty results
  if (countries.length === 0) {
    return {
      highRiskCountries: [],
      highRiskStates: [],
      growthForecast: [],
      predictedHotspots: []
    };
  }

  // Calculate prediction data based on mock datasets
  const predictedCountries = countries.map(c => {
    // Basic AI scoring formula: combine total cases with active case ratios and add historical fluctuations
    const trendMultiplier = 1.0 + (Math.sin(c.fraudCases) * 0.15); // simulated fluctuation
    const predictedGrowth = Math.max(-5, Math.min(100, Math.round(((c.growthRate || 8) * trendMultiplier) * 10) / 10));
    const confidence = Math.round(85 + (Math.cos(c.fraudCases) * 12));
    const predictedScore = Math.max(10, Math.min(100, Math.round((c.riskScore * 0.8) + (predictedGrowth * 0.2))));

    return {
      country: c.country,
      currentCases: c.fraudCases,
      predictedScore,
      predictedGrowth,
      confidence: Math.min(99, Math.max(70, confidence))
    };
  }).sort((a, b) => b.predictedScore - a.predictedScore).slice(0, 10);

  const predictedStates = states.map(s => {
    const baselineCases = s.fraudCases;
    const factor = Math.abs(Math.sin(baselineCases)) * 1.5;
    const growth = Math.round(factor * 25);
    const score = Math.min(100, Math.max(10, Math.round((s.riskLevel === 'High' ? 80 : s.riskLevel === 'Medium' ? 50 : 25) + (factor * 10))));

    return {
      state: s.state,
      country: s.country,
      cases: baselineCases,
      predictedScore: score,
      predictedGrowth: growth,
      confidence: Math.round(75 + (factor * 15))
    };
  }).sort((a, b) => b.predictedScore - a.predictedScore).slice(0, 10);

  // Group recent incidents to identify hotspot clusters (Visakhapatnam, Noida, Mumbai, etc.)
  const cityCounts = {};
  incidents.forEach(inc => {
    const key = `${inc.city}, ${inc.state}, ${inc.country}`;
    if (!cityCounts[key]) {
      cityCounts[key] = {
        city: inc.city,
        state: inc.state,
        country: inc.country,
        latitude: inc.latitude,
        longitude: inc.longitude,
        count: 0,
        victims: 0
      };
    }
    cityCounts[key].count++;
    cityCounts[key].victims += inc.victims;
  });

  const predictedHotspots = Object.values(cityCounts).map(h => {
    const probability = Math.round(60 + (h.count * 1.8));
    return {
      location: `${h.city} (${h.state})`,
      country: h.country,
      coords: [h.latitude, h.longitude],
      currentCount: h.count,
      totalVictims: h.victims,
      probability: Math.min(98, Math.max(50, probability)),
      growthRate: Math.round(8 + (h.count * 0.8))
    };
  }).sort((a, b) => b.probability - a.probability).slice(0, 10);

  return {
    highRiskCountries: predictedCountries,
    highRiskStates: predictedStates,
    predictedHotspots
  };
}
