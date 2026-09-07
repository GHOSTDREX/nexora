import type { REGIONS } from '@/lib/farmOptions'

type Region = (typeof REGIONS)[number]

// Indian Zonal Council groupings — the app's 5-region taxonomy has no
// "North East" bucket, so those states fold into East as the nearest fit.
const STATE_TO_REGION: Record<string, Region> = {
  'Chandigarh': 'North', 'Delhi': 'North', 'Haryana': 'North', 'Himachal Pradesh': 'North',
  'Jammu and Kashmir': 'North', 'Ladakh': 'North', 'Punjab': 'North', 'Rajasthan': 'North',
  'Andhra Pradesh': 'South', 'Karnataka': 'South', 'Kerala': 'South', 'Puducherry': 'South',
  'Tamil Nadu': 'South', 'Telangana': 'South', 'Andaman and Nicobar Islands': 'South', 'Lakshadweep': 'South',
  'Bihar': 'East', 'Jharkhand': 'East', 'Odisha': 'East', 'West Bengal': 'East',
  'Arunachal Pradesh': 'East', 'Assam': 'East', 'Manipur': 'East', 'Meghalaya': 'East',
  'Mizoram': 'East', 'Nagaland': 'East', 'Sikkim': 'East', 'Tripura': 'East',
  'Goa': 'West', 'Gujarat': 'West', 'Maharashtra': 'West',
  'Dadra and Nagar Haveli and Daman and Diu': 'West',
  'Chhattisgarh': 'Central', 'Madhya Pradesh': 'Central', 'Uttar Pradesh': 'Central', 'Uttarakhand': 'Central',
}

export function regionForState(state: string): Region | null {
  return STATE_TO_REGION[state] ?? null
}

/** Matches a reverse-geocoded state name (which may differ slightly in
 * casing/spelling from the backend's own state list) against the app's
 * actual dropdown options, so the auto-filled value is always one the
 * <select> already has as an <option>. */
export function matchKnownState(detected: string, known: string[]): string | null {
  const normalize = (s: string) => s.toLowerCase().replace(/[^a-z]/g, '')
  const target = normalize(detected)
  return known.find((s) => normalize(s) === target) ?? null
}

export interface DetectedLocation {
  latitude: number
  longitude: number
  state: string | null
}

/** Browser geolocation -> OpenStreetMap Nominatim reverse geocode (free,
 * no API key). Resolves to lat/lng always (if permission was granted);
 * `state` is null if reverse geocoding didn't return one — callers should
 * treat that as "keep the manual default", not an error. */
export function detectLocation(): Promise<DetectedLocation> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation not supported'))
      return
    }
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords
        try {
          const res = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=5&addressdetails=1`,
            { headers: { Accept: 'application/json' } },
          )
          const data = await res.json()
          resolve({ latitude, longitude, state: data?.address?.state ?? null })
        } catch {
          resolve({ latitude, longitude, state: null })
        }
      },
      (err) => reject(err),
      { timeout: 8000, maximumAge: 300_000 },
    )
  })
}
