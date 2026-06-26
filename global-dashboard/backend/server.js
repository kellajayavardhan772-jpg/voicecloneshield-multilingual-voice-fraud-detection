import express from 'express';
import http from 'http';
import { Server } from 'socket.io';
import cors from 'cors';
import dotenv from 'dotenv';
import { connectDb, USE_MOCK, mockDb } from './db.js';
import { generateData } from './seeder.js';
import router from './routes.js';
import { Country, State, District, City, Incident } from './models.js';

dotenv.config();

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

app.use(cors());
app.use(express.json());

// API Base Router
app.use('/api', router);

// Serve simple health endpoint
app.get('/health', (req, res) => {
  res.json({
    status: "healthy",
    database: USE_MOCK ? "in-memory (mock)" : "MongoDB connected"
  });
});

// Setup websocket event dispatchers
io.on('connection', (socket) => {
  console.log(`🔌 Client connected: ${socket.id}`);
  
  socket.on('disconnect', () => {
    console.log(`❌ Client disconnected: ${socket.id}`);
  });
});

// Real-Time Incident Simulator interval (triggers every 6 seconds)
function startIncidentSimulator() {
  const FRAUD_TYPES = [
    "AI Voice Clone Scam",
    "KYC Authentication Bypass",
    "Grandparent Voice Hijack",
    "CEO Voice Clone Impersonation",
    "Emergency Ransom Call",
    "Bank Representative Vishing",
    "Robotic Identity Extraction",
    "Biometric Audio Forgery",
    "Fake Utility Operator Call",
    "Lottery / Prize Claims"
  ];

  setInterval(async () => {
    try {
      let targetCity;
      let targetState;
      let targetCountry;
      let targetDistrict;

      if (USE_MOCK) {
        if (mockDb.cities.length === 0) return;
        targetCity = mockDb.cities[Math.floor(Math.random() * mockDb.cities.length)];
        targetDistrict = mockDb.districts.find(d => d._id === targetCity.districtId);
        targetState = mockDb.states.find(s => s._id === targetDistrict.stateId);
        targetCountry = mockDb.countries.find(c => c._id === targetState.countryId);
      } else {
        const count = await City.countDocuments();
        if (count === 0) return;
        const randomIdx = Math.floor(Math.random() * count);
        targetCity = await City.findOne().skip(randomIdx).lean();
        targetDistrict = await District.findById(targetCity.districtId).lean();
        targetState = await State.findById(targetDistrict.stateId).lean();
        targetCountry = await Country.findById(targetState.countryId).lean();
      }

      if (!targetCity) return;

      const victims = Math.floor(Math.random() * 12) + 1;
      const risk = victims > 8 ? "Critical" : victims > 5 ? "High" : victims > 2 ? "Medium" : "Low";
      const type = FRAUD_TYPES[Math.floor(Math.random() * FRAUD_TYPES.length)];
      const incId = `INC-${Date.now().toString().slice(-6)}`;

      const newIncident = {
        incidentId: incId,
        country: targetCountry.country,
        state: targetState.state,
        district: targetDistrict.district,
        city: targetCity.city,
        fraudType: type,
        victims: victims,
        riskLevel: risk,
        latitude: targetCity.latitude + ((Math.random() * 0.02) - 0.01),
        longitude: targetCity.longitude + ((Math.random() * 0.02) - 0.01),
        createdAt: new Date()
      };

      // Push to DB / update counters
      if (USE_MOCK) {
        mockDb.incidents.push(newIncident);
        targetCountry.fraudCases += 1;
        targetCountry.activeCases += Math.random() > 0.4 ? 1 : 0;
        targetState.fraudCases += 1;
        targetDistrict.fraudCases += 1;
        targetCity.fraudCases += 1;
      } else {
        await Incident.create(newIncident);
        await Country.findByIdAndUpdate(targetCountry._id, { $inc: { fraudCases: 1 } });
        await State.findByIdAndUpdate(targetState._id, { $inc: { fraudCases: 1 } });
        await District.findByIdAndUpdate(targetDistrict._id, { $inc: { fraudCases: 1 } });
        await City.findByIdAndUpdate(targetCity._id, { $inc: { fraudCases: 1 } });
      }

      // Emit new incident to all websocket clients
      io.emit('new-incident', newIncident);

    } catch (err) {
      console.error(`Error in incident simulator: ${err.message}`);
    }
  }, 6000);
}

const PORT = process.env.PORT || 5000;

// Initialize Database & Server Startup
(async () => {
  console.log("🚀 Starting Global AI Voice Fraud Intelligence Dashboard Server...");
  
  await connectDb();

  // If running in Mock mode, seed initial database in memory
  if (USE_MOCK) {
    console.log("📥 Seeding initial in-memory database...");
    const seedData = generateData(4000); // 4k incidents for lightweight memory usage
    mockDb.countries = seedData.countries;
    mockDb.states = seedData.states;
    mockDb.districts = seedData.districts;
    mockDb.cities = seedData.cities;
    mockDb.incidents = seedData.incidents;
    console.log(`   - Seeded ${mockDb.incidents.length} in-memory incidents.`);
  }

  server.listen(PORT, () => {
    console.log(`🌐 Server running in ${USE_MOCK ? 'MOCK' : 'MONGO'} mode on port ${PORT}`);
    startIncidentSimulator();
  });
})();
