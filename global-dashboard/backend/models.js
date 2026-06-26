import mongoose from 'mongoose';

const countrySchema = new mongoose.Schema({
  country: { type: String, required: true, unique: true },
  coords: { type: [Number], default: [0, 0] },
  fraudCases: { type: Number, default: 0 },
  activeCases: { type: Number, default: 0 },
  growthRate: { type: Number, default: 0 },
  riskScore: { type: Number, default: 0 },
  lastUpdated: { type: Date, default: Date.now }
});

const stateSchema = new mongoose.Schema({
  countryId: { type: mongoose.Schema.Types.ObjectId, ref: 'Country', required: true },
  country: { type: String, required: true },
  state: { type: String, required: true },
  fraudCases: { type: Number, default: 0 },
  riskLevel: { type: String, default: 'Low' }
});

const districtSchema = new mongoose.Schema({
  stateId: { type: mongoose.Schema.Types.ObjectId, ref: 'State', required: true },
  state: { type: String, required: true },
  district: { type: String, required: true },
  fraudCases: { type: Number, default: 0 },
  riskLevel: { type: String, default: 'Low' }
});

const citySchema = new mongoose.Schema({
  districtId: { type: mongoose.Schema.Types.ObjectId, ref: 'District', required: true },
  district: { type: String, required: true },
  city: { type: String, required: true },
  fraudCases: { type: Number, default: 0 },
  riskLevel: { type: String, default: 'Low' },
  latitude: { type: Number, required: true },
  longitude: { type: Number, required: true }
});

const incidentSchema = new mongoose.Schema({
  incidentId: { type: String, required: true, unique: true },
  country: { type: String, required: true },
  state: { type: String, required: true },
  district: { type: String, required: true },
  city: { type: String, required: true },
  fraudType: { type: String, required: true },
  victims: { type: Number, default: 1 },
  riskLevel: { type: String, default: 'Low' },
  latitude: { type: Number, required: true },
  longitude: { type: Number, required: true },
  createdAt: { type: Date, default: Date.now }
});

export const Country = mongoose.models.Country || mongoose.model('Country', countrySchema);
export const State = mongoose.models.State || mongoose.model('State', stateSchema);
export const District = mongoose.models.District || mongoose.model('District', districtSchema);
export const City = mongoose.models.City || mongoose.model('City', citySchema);
export const Incident = mongoose.models.Incident || mongoose.model('Incident', incidentSchema);
