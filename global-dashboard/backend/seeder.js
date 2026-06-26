import mongoose from 'mongoose';
import dotenv from 'dotenv';
import { connectDb, USE_MOCK, mockDb } from './db.js';
import { Country, State, District, City, Incident } from './models.js';

dotenv.config();

// Standard major countries for seed base
const BASE_COUNTRIES = [
  { name: "India", code: "IN", coords: [20.5937, 78.9629], risk: 85 },
  { name: "United States", code: "US", coords: [37.0902, -95.7129], risk: 90 },
  { name: "United Kingdom", code: "GB", coords: [55.3781, -3.4360], risk: 75 },
  { name: "Canada", code: "CA", coords: [56.1304, -106.3468], risk: 70 },
  { name: "Australia", code: "AU", coords: [-25.2744, 133.7751], risk: 65 },
  { name: "Germany", code: "DE", coords: [51.1657, 10.4515], risk: 60 },
  { name: "Japan", code: "JP", coords: [36.2048, 138.2529], risk: 55 },
  { name: "Singapore", code: "SG", coords: [1.3521, 103.8198], risk: 80 },
  { name: "South Africa", code: "ZA", coords: [-30.5595, 22.9375], risk: 72 },
  { name: "Brazil", code: "BR", coords: [-14.2350, -51.9253], risk: 78 }
];

const EXTENDED_COUNTRY_NAMES = [
  "France", "Italy", "Spain", "Mexico", "Argentina", "Netherlands", "Sweden", "Switzerland", "Norway", "Denmark",
  "Finland", "Belgium", "Austria", "Russia", "China", "South Korea", "India", "New Zealand", "Ireland", "Poland",
  "Turkey", "Saudi Arabia", "UAE", "Egypt", "Nigeria", "Kenya", "Ghana", "Malaysia", "Indonesia", "Thailand",
  "Vietnam", "Philippines", "Israel", "Greece", "Portugal", "Chile", "Colombia", "Peru", "Ukraine", "Romania",
  "Hungary", "Czech Republic", "Slovakia", "Czechia", "Morocco", "Pakistan", "Bangladesh", "Siri Lanka", "Nepal", "Maldives"
];

// Major Indian States & Cities
const INDIA_GEOGRAPHY = [
  {
    state: "Andhra Pradesh",
    districts: [
      {
        district: "Visakhapatnam District",
        cities: [
          { city: "Visakhapatnam City", coords: [17.6868, 83.2185] },
          { city: "Gajuwaka", coords: [17.6904, 83.1644] },
          { city: "Anakapalle", coords: [17.6913, 83.0031] }
        ]
      },
      {
        district: "Krishna District",
        cities: [
          { city: "Vijayawada", coords: [16.5062, 80.6480] },
          { city: "Machilipatnam", coords: [16.1875, 81.1300] }
        ]
      }
    ]
  },
  {
    state: "Telangana",
    districts: [
      {
        district: "Hyderabad District",
        cities: [
          { city: "Hyderabad City", coords: [17.3850, 78.4867] },
          { city: "Secunderabad", coords: [17.4399, 78.4983] }
        ]
      },
      {
        district: "Warangal District",
        cities: [
          { city: "Warangal City", coords: [17.9689, 79.5941] },
          { city: "Kazipet", coords: [17.9818, 79.5303] }
        ]
      }
    ]
  },
  {
    state: "Maharashtra",
    districts: [
      {
        district: "Mumbai Suburban",
        cities: [
          { city: "Mumbai City", coords: [19.0760, 72.8777] },
          { city: "Andheri", coords: [19.1136, 72.8697] },
          { city: "Bandra", coords: [19.0596, 72.8295] }
        ]
      },
      {
        district: "Pune District",
        cities: [
          { city: "Pune City", coords: [18.5204, 73.8567] },
          { city: "Pimpri-Chinchwad", coords: [18.6298, 73.7997] }
        ]
      }
    ]
  },
  {
    state: "Karnataka",
    districts: [
      {
        district: "Bengaluru Urban",
        cities: [
          { city: "Bengaluru City", coords: [12.9716, 77.5946] },
          { city: "Whitefield", coords: [12.9698, 77.7500] }
        ]
      }
    ]
  }
];

const US_GEOGRAPHY = [
  {
    state: "California",
    districts: [
      {
        district: "Los Angeles County",
        cities: [
          { city: "Los Angeles", coords: [34.0522, -118.2437] },
          { city: "Pasadena", coords: [34.1478, -118.1445] }
        ]
      },
      {
        district: "San Francisco County",
        cities: [
          { city: "San Francisco", coords: [37.7749, -122.4194] }
        ]
      }
    ]
  },
  {
    state: "New York",
    districts: [
      {
        district: "New York County",
        cities: [
          { city: "Manhattan", coords: [40.7831, -73.9712] },
          { city: "Brooklyn", coords: [40.6782, -73.9442] }
        ]
      }
    ]
  }
];

// Helper prefixes and suffixes to generate thousands of mock locations procedurally
const STATE_PREFIXES = ["North", "South", "East", "West", "Central", "Upper", "Lower", "New", "Greater"];
const STATE_SUFFIXES = ["land", "shire", " province", " State", " Region", " territory", " Area", " Division"];
const DISTRICT_NAMES = ["Lincoln", "Washington", "Franklin", "Jefferson", "Hamilton", "Jackson", "Madison", "Monroe", "Victoria", "Albert", "King", "Queen", "Green", "Blue", "Stone", "River", "Lake", "Valley", "Hill", "Ridge"];
const CITY_PREFIXES = ["Port ", "Saint ", "Mount ", "Fort ", "San ", "Santa ", "New ", "Old "];
const CITY_SUFFIXES = ["ville", "burg", "port", "ton", "field", "wood", "creek", "mouth", "chester", "ford", "ham", "bury", "pur", "abad", "nagar", "ore", "pet", "giri", "halli"];

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

export function generateData(incidentCount = 15000) {
  console.log(`  📊 Procedurally generating ${incidentCount} AI voice fraud incidents...`);
  
  const countries = [];
  const states = [];
  const districts = [];
  const cities = [];
  const incidents = [];

  // Generate Countries (Total 100)
  // First seed real base countries
  BASE_COUNTRIES.forEach((c, idx) => {
    countries.push({
      _id: new mongoose.Types.ObjectId(),
      country: c.name,
      code: c.code,
      coords: c.coords,
      fraudCases: 0,
      activeCases: 0,
      growthRate: Math.round(5 + Math.random() * 20),
      riskScore: c.risk,
      lastUpdated: new Date()
    });
  });

  // Generate extended mock countries
  let index = 1;
  while (countries.length < 100) {
    const name = EXTENDED_COUNTRY_NAMES[index % EXTENDED_COUNTRY_NAMES.length] + " " + Math.ceil(index / EXTENDED_COUNTRY_NAMES.length);
    // Random coordinates around the globe
    const lat = (Math.random() * 120) - 60;
    const lng = (Math.random() * 260) - 130;
    countries.push({
      _id: new mongoose.Types.ObjectId(),
      country: name,
      code: "MC" + index,
      coords: [lat, lng],
      fraudCases: 0,
      activeCases: 0,
      growthRate: Math.round(2 + Math.random() * 12),
      riskScore: Math.round(30 + Math.random() * 45),
      lastUpdated: new Date()
    });
    index++;
  }

  // Generate States (500), Districts (2000), Cities (5000)
  // First seed specific real geo-hierarchies (India & US)
  
  // 1. Seed India
  const indiaObj = countries.find(c => c.country === "India");
  if (indiaObj) {
    INDIA_GEOGRAPHY.forEach(st => {
      const stateObj = {
        _id: new mongoose.Types.ObjectId(),
        countryId: indiaObj._id,
        country: indiaObj.country,
        state: st.state,
        fraudCases: 0,
        riskLevel: st.state === "Maharashtra" ? "High" : "Medium"
      };
      states.push(stateObj);

      st.districts.forEach(dst => {
        const distObj = {
          _id: new mongoose.Types.ObjectId(),
          stateId: stateObj._id,
          state: stateObj.state,
          district: dst.district,
          fraudCases: 0,
          riskLevel: "Medium"
        };
        districts.push(distObj);

        dst.cities.forEach(cty => {
          cities.push({
            _id: new mongoose.Types.ObjectId(),
            districtId: distObj._id,
            district: distObj.district,
            city: cty.city,
            fraudCases: 0,
            riskLevel: "Medium",
            latitude: cty.coords[0],
            longitude: cty.coords[1]
          });
        });
      });
    });
  }

  // 2. Seed US
  const usObj = countries.find(c => c.country === "United States");
  if (usObj) {
    US_GEOGRAPHY.forEach(st => {
      const stateObj = {
        _id: new mongoose.Types.ObjectId(),
        countryId: usObj._id,
        country: usObj.country,
        state: st.state,
        fraudCases: 0,
        riskLevel: "High"
      };
      states.push(stateObj);

      st.districts.forEach(dst => {
        const distObj = {
          _id: new mongoose.Types.ObjectId(),
          stateId: stateObj._id,
          state: stateObj.state,
          district: dst.district,
          fraudCases: 0,
          riskLevel: "Medium"
        };
        districts.push(distObj);

        dst.cities.forEach(cty => {
          cities.push({
            _id: new mongoose.Types.ObjectId(),
            districtId: distObj._id,
            district: distObj.district,
            city: cty.city,
            fraudCases: 0,
            riskLevel: "Medium",
            latitude: cty.coords[0],
            longitude: cty.coords[1]
          });
        });
      });
    });
  }

  // 3. Generate remaining states, districts, and cities procedurally
  let cIdx = 2; // skip India/US base mappings
  
  // Fill states up to 500
  while (states.length < 500) {
    const parentCountry = countries[cIdx % countries.length];
    const prefix = STATE_PREFIXES[states.length % STATE_PREFIXES.length];
    const suffix = STATE_SUFFIXES[states.length % STATE_SUFFIXES.length];
    const name = `${prefix} ${parentCountry.country}${suffix}`;

    states.push({
      _id: new mongoose.Types.ObjectId(),
      countryId: parentCountry._id,
      country: parentCountry.country,
      state: name,
      fraudCases: 0,
      riskLevel: "Low"
    });
    cIdx++;
  }

  // Fill districts up to 2000
  let sIdx = 0;
  while (districts.length < 2000) {
    const parentState = states[sIdx % states.length];
    const name = DISTRICT_NAMES[districts.length % DISTRICT_NAMES.length] + " District " + Math.ceil((districts.length + 1) / DISTRICT_NAMES.length);

    districts.push({
      _id: new mongoose.Types.ObjectId(),
      stateId: parentState._id,
      state: parentState.state,
      district: name,
      fraudCases: 0,
      riskLevel: "Low"
    });
    sIdx++;
  }

  // Fill cities up to 5000
  let dIdx = 0;
  while (cities.length < 5000) {
    const parentDistrict = districts[dIdx % districts.length];
    const prefix = CITY_PREFIXES[cities.length % CITY_PREFIXES.length];
    const suffix = CITY_SUFFIXES[cities.length % CITY_SUFFIXES.length];
    
    // Pick base name from district
    const cleanDistName = parentDistrict.district.split(' ')[0];
    const name = `${prefix}${cleanDistName}${suffix}`;
    
    // Find state and country coordinates to generate city lat/lng relative to them
    const parentState = states.find(s => s._id === parentDistrict.stateId);
    const parentCountry = countries.find(c => c._id === parentState.countryId);
    
    // Random offset around parent country center
    const latOffset = (Math.random() * 4) - 2;
    const lngOffset = (Math.random() * 4) - 2;
    const lat = parentCountry.coords[0] + latOffset;
    const lng = parentCountry.coords[1] + lngOffset;

    cities.push({
      _id: new mongoose.Types.ObjectId(),
      districtId: parentDistrict._id,
      district: parentDistrict.district,
      city: name,
      fraudCases: 0,
      riskLevel: "Low",
      latitude: lat,
      longitude: lng
    });
    dIdx++;
  }

  console.log("  📂 Locations generated. Mapping incidents...");

  // Generate Incident Documents
  for (let i = 0; i < incidentCount; i++) {
    // Distribute incidents: 40% in India & US to make drill-downs interesting, 60% rest of the world
    let randomCity;
    if (Math.random() < 0.40) {
      // Find a city in India or US
      const localCities = cities.filter(c => c.district.includes("Visakhapatnam") || c.district.includes("Krishna") || c.district.includes("Hyderabad") || c.district.includes("Mumbai Suburban") || c.district.includes("Pune") || c.district.includes("Bengaluru") || c.district.includes("Los Angeles") || c.district.includes("San Francisco") || c.district.includes("New York"));
      randomCity = localCities[Math.floor(Math.random() * localCities.length)];
    } else {
      randomCity = cities[Math.floor(Math.random() * cities.length)];
    }

    // Find parent hierarchy
    const parentDistrict = districts.find(d => d._id === randomCity.districtId);
    const parentState = states.find(s => s._id === parentDistrict.stateId);
    const parentCountry = countries.find(c => c._id === parentState.countryId);

    const type = FRAUD_TYPES[i % FRAUD_TYPES.length];
    const victims = Math.floor(Math.random() * 25) + 1;
    const risk = victims > 15 ? "Critical" : victims > 8 ? "High" : victims > 3 ? "Medium" : "Low";

    // Random coordinates very close to city center
    const lat = randomCity.latitude + ((Math.random() * 0.04) - 0.02);
    const lng = randomCity.longitude + ((Math.random() * 0.04) - 0.02);

    // Dynamic date in last 12 months
    const date = new Date();
    date.setDate(date.getDate() - Math.floor(Math.random() * 365));

    incidents.push({
      _id: new mongoose.Types.ObjectId(),
      incidentId: `INC-${100000 + i}`,
      country: parentCountry.country,
      state: parentState.state,
      district: parentDistrict.district,
      city: randomCity.city,
      fraudType: type,
      victims: victims,
      riskLevel: risk,
      latitude: lat,
      longitude: lng,
      createdAt: date
    });

    // Update case counters in parent layers
    parentCountry.fraudCases += 1;
    parentCountry.activeCases += Math.random() > 0.4 ? 1 : 0;
    parentState.fraudCases += 1;
    parentDistrict.fraudCases += 1;
    randomCity.fraudCases += 1;
  }

  // Set risk thresholds dynamically based on case sums
  countries.forEach(c => {
    c.riskScore = Math.min(100, Math.max(10, Math.round((c.fraudCases / 150) * 100)));
  });

  states.forEach(s => {
    s.riskLevel = s.fraudCases > 100 ? "High" : s.fraudCases >= 40 ? "Medium" : "Low";
  });

  districts.forEach(d => {
    d.riskLevel = d.fraudCases > 40 ? "High" : d.fraudCases >= 15 ? "Medium" : "Low";
  });

  cities.forEach(c => {
    c.riskLevel = c.fraudCases > 20 ? "High" : c.fraudCases >= 8 ? "Medium" : "Low";
  });

  console.log("  ✅ Seeding data generated successfully.");

  return { countries, states, districts, cities, incidents };
}

// If run directly via command line
if (import.meta.url === `file://${process.argv[1]}`) {
  (async () => {
    console.log("🚀 Starting database seeding...");
    await connectDb();
    
    if (USE_MOCK) {
      console.warn("⚠️ Cannot run seeder on MongoDB because connection failed. Check MONGODB_URI.");
      process.exit(1);
    }

    try {
      // Clear existing records
      console.log("🧹 Clearing collections...");
      await Country.deleteMany({});
      await State.deleteMany({});
      await District.deleteMany({});
      await City.deleteMany({});
      await Incident.deleteMany({});

      // Generate seed data
      const data = generateData(15000); // Seeding 15k for fast execution. Update parameter to 50000 if needed.

      // Insert in large chunks
      console.log("📥 Inserting Country documents...");
      await Country.insertMany(data.countries);

      console.log("📥 Inserting State documents...");
      await State.insertMany(data.states);

      console.log("📥 Inserting District documents...");
      await District.insertMany(data.districts);

      console.log("📥 Inserting City documents...");
      await City.insertMany(data.cities);

      console.log("📥 Inserting Incident documents in batches...");
      const batchSize = 2000;
      for (let i = 0; i < data.incidents.length; i += batchSize) {
        const batch = data.incidents.slice(i, i + batchSize);
        await Incident.insertMany(batch);
        console.log(`   - Seeded ${i + batch.length}/${data.incidents.length} incidents`);
      }

      console.log("🎉 Database fully seeded successfully!");
      mongoose.disconnect();
    } catch (e) {
      console.error("❌ Seeding failed: ", e);
      process.exit(1);
    }
  })();
}
