import mongoose from 'mongoose';
import dotenv from 'dotenv';

dotenv.config();

export let USE_MOCK = false;

// Mock database storage
export const mockDb = {
  countries: [],
  states: [],
  districts: [],
  cities: [],
  incidents: []
};

export async function connectDb() {
  const uri = process.env.MONGODB_URI;
  if (!uri) {
    console.warn("  ⚠️  MONGODB_URI not found in env. Falling back to In-Memory mock database.");
    USE_MOCK = true;
    return;
  }

  try {
    // Attempt connecting with a short 3-second timeout
    await mongoose.connect(uri, {
      serverSelectionTimeoutMS: 3000
    });
    console.log("  ✅ MongoDB connected successfully.");
    USE_MOCK = false;
  } catch (err) {
    console.error(`  ❌ MongoDB connection error: ${err.message}`);
    console.warn("  ⚠️  Falling back to In-Memory mock database.");
    USE_MOCK = true;
  }
}
