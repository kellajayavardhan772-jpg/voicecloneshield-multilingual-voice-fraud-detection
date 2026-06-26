import express from 'express';
import { USE_MOCK, mockDb } from './db.js';
import { Country, State, District, City, Incident } from './models.js';
import { getPredictions } from './prediction.js';

const router = express.Router();

// Helper to query either mongo or mock in-memory DB
async function getCollectionData(model, mockArrayKey) {
  if (USE_MOCK) {
    return mockDb[mockArrayKey];
  }
  return await model.find().lean();
}

// -------------------------------------------------------------
// DASHBOARD APIS
// -------------------------------------------------------------

router.get('/dashboard/stats', async (req, res) => {
  try {
    let countries = await getCollectionData(Country, 'countries');
    let incidents = await getCollectionData(Incident, 'incidents');

    const totalIncidents = incidents.length;
    const affectedCountries = countries.length;
    
    // Confirmed cases (sum of victims)
    const confirmedCases = incidents.reduce((acc, curr) => acc + curr.victims, 0);
    
    // AI voice clone attempts (normally higher than reports, e.g. 1.8x of incidents)
    const cloneAttempts = Math.round(totalIncidents * 1.8);
    
    // High risk regions (> 1000 cases countries/states)
    let states = await getCollectionData(State, 'states');
    const highRiskRegions = countries.filter(c => c.fraudCases > 1000).length + 
                            states.filter(s => s.fraudCases > 400).length;

    // Average global growth rate
    const totalGrowth = countries.reduce((acc, curr) => acc + curr.growthRate, 0);
    const avgGrowthRate = countries.length > 0 ? (totalGrowth / countries.length).toFixed(1) : "0.0";

    res.json({
      globalFraudIncidents: totalIncidents,
      aiVoiceCloneAttempts: cloneAttempts,
      confirmedFraudCases: confirmedCases,
      countriesAffected: affectedCountries,
      highRiskRegions: highRiskRegions,
      monthlyGrowthRatePercent: parseFloat(avgGrowthRate),
      globalRiskScore: 78 // baseline rating
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.get('/dashboard/top-countries', async (req, res) => {
  try {
    let countries = await getCollectionData(Country, 'countries');
    const sorted = [...countries].sort((a, b) => b.fraudCases - a.fraudCases).slice(0, 10);
    res.json(sorted);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.get('/dashboard/top-states', async (req, res) => {
  try {
    let states = await getCollectionData(State, 'states');
    const sorted = [...states].sort((a, b) => b.fraudCases - a.fraudCases).slice(0, 10);
    res.json(sorted);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.get('/dashboard/top-cities', async (req, res) => {
  try {
    let cities = await getCollectionData(City, 'cities');
    const sorted = [...cities].sort((a, b) => b.fraudCases - a.fraudCases).slice(0, 10);
    res.json(sorted);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// -------------------------------------------------------------
// MAP APIS (World and multi-level drill downs)
// -------------------------------------------------------------

// World Map Data (country-level geometries loaded by Leaflet client, matched against this data)
router.get('/map/world', async (req, res) => {
  try {
    let countries = await getCollectionData(Country, 'countries');
    res.json(countries);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Country States Map Data (e.g. click India -> get state listings)
router.get('/map/country/:country', async (req, res) => {
  try {
    const countryName = req.params.country;
    let states = [];
    if (USE_MOCK) {
      states = mockDb.states.filter(s => s.country.toLowerCase() === countryName.toLowerCase());
    } else {
      states = await State.find({ country: new RegExp(`^${countryName}$`, 'i') }).lean();
    }
    res.json(states);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// State Districts Map Data
router.get('/map/state/:state', async (req, res) => {
  try {
    const stateName = req.params.state;
    let districts = [];
    if (USE_MOCK) {
      districts = mockDb.districts.filter(d => d.state.toLowerCase() === stateName.toLowerCase());
    } else {
      districts = await District.find({ state: new RegExp(`^${stateName}$`, 'i') }).lean();
    }
    res.json(districts);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// District Cities Map Data (district center coordinate and list of cities with coordinates)
router.get('/map/district/:district', async (req, res) => {
  try {
    const districtName = req.params.district;
    let cities = [];
    if (USE_MOCK) {
      cities = mockDb.cities.filter(c => c.district.toLowerCase() === districtName.toLowerCase());
    } else {
      cities = await City.find({ district: new RegExp(`^${districtName}$`, 'i') }).lean();
    }
    res.json(cities);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// -------------------------------------------------------------
// INCIDENT APIS
// -------------------------------------------------------------

router.get('/incidents', async (req, res) => {
  try {
    let incidents = await getCollectionData(Incident, 'incidents');
    res.json(incidents);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.get('/incidents/recent', async (req, res) => {
  try {
    let incidents = await getCollectionData(Incident, 'incidents');
    // Sort by Date (newest first)
    const sorted = [...incidents].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)).slice(0, 15);
    res.json(sorted);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.get('/incidents/:id', async (req, res) => {
  try {
    const id = req.params.id;
    let incident;
    if (USE_MOCK) {
      incident = mockDb.incidents.find(inc => inc.incidentId === id || inc._id === id);
    } else {
      incident = await Incident.findOne({ $or: [{ incidentId: id }, { _id: id }] }).lean();
    }
    if (!incident) return res.status(404).json({ error: "Incident not found" });
    res.json(incident);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// -------------------------------------------------------------
// SEARCH AND FILTER API
// -------------------------------------------------------------

router.get('/search', async (req, res) => {
  try {
    const { country, state, district, city, dateRange, fraudType } = req.query;

    let incidents = [];
    if (USE_MOCK) {
      incidents = mockDb.incidents;
    } else {
      incidents = await Incident.find().lean();
    }

    let filtered = [...incidents];

    if (country) {
      filtered = filtered.filter(inc => inc.country.toLowerCase().includes(country.toLowerCase()));
    }
    if (state) {
      filtered = filtered.filter(inc => inc.state.toLowerCase().includes(state.toLowerCase()));
    }
    if (district) {
      filtered = filtered.filter(inc => inc.district.toLowerCase().includes(district.toLowerCase()));
    }
    if (city) {
      filtered = filtered.filter(inc => inc.city.toLowerCase().includes(city.toLowerCase()));
    }
    if (fraudType) {
      filtered = filtered.filter(inc => inc.fraudType.toLowerCase().includes(fraudType.toLowerCase()));
    }

    if (dateRange) {
      const now = new Date();
      let thresholdDate = new Date();

      if (dateRange === '24h') {
        thresholdDate.setDate(now.getDate() - 1);
      } else if (dateRange === '7d') {
        thresholdDate.setDate(now.getDate() - 7);
      } else if (dateRange === '30d') {
        thresholdDate.setDate(now.getDate() - 30);
      } else if (dateRange === '6m') {
        thresholdDate.setMonth(now.getMonth() - 6);
      } else if (dateRange === '1y') {
        thresholdDate.setFullYear(now.getFullYear() - 1);
      }

      filtered = filtered.filter(inc => new Date(inc.createdAt) >= thresholdDate);
    }

    // Limit search results to max 200 items to avoid payload bloating
    res.json(filtered.slice(0, 200));
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// -------------------------------------------------------------
// AI PREDICTIONS API
// -------------------------------------------------------------

router.get('/predictions', async (req, res) => {
  try {
    const pred = await getPredictions();
    res.json(pred);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;
