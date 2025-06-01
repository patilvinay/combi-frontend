interface PhaseData {
  v: number;
  i: number;
  p: number;
  f: number;
  pf: number;
}

export interface Measurement {
  id: number;
  device_id: string;
  enqueued_time: string;
  created_at: string;
  phases: PhaseData[];
}

const API_BASE_URL = 'http://localhost:5050/api/v1';
const API_KEY = 'Xj7Bq9Lp2Rt5Zk8Mn3Vx6Hs1';

// Common headers for all API requests
const headers = {
  'Content-Type': 'application/json',
  'X-API-Key': API_KEY,
  // Add the following header to handle CORS
  'Access-Control-Allow-Origin': '*'
};

class DeviceService {
  /**
   * Get the latest measurement for a specific device
   */
  async getLatestMeasurement(deviceId: string): Promise<Measurement | null> {
    try {
      // Use the proxy endpoint to avoid CORS issues
      const response = await fetch(`/api/measurements/latest/${deviceId}`, {
        headers
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching latest measurement:', error);
      return null;
    }
  }

  /**
   * Get recent measurements for a specific device
   */
  async getRecentMeasurements(deviceId: string, hours: number = 2): Promise<Measurement[]> {
    try {
      // Use the proxy endpoint to avoid CORS issues
      const response = await fetch(`/api/measurements/recent/${deviceId}?hours=${hours}`, {
        headers
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      const data = await response.json();
      return data; // This will be an empty array if no data is found
    } catch (error) {
      console.error('Error fetching recent measurements:', error);
      return []; // Return empty array on error
    }
  }

  /**
   * Get measurements in a specific time range for a device
   */
  async getMeasurementsInRange(
    deviceId: string, 
    startTime: string, 
    endTime: string
  ): Promise<Measurement[]> {
    try {
      // Use the proxy endpoint to avoid CORS issues
      const url = `/api/measurements/range/${deviceId}?start_time=${encodeURIComponent(startTime)}&end_time=${encodeURIComponent(endTime)}`;
      
      const response = await fetch(url, {
        headers
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      const data = await response.json();
      return data; // This will be an empty array if no data is found
    } catch (error) {
      console.error('Error fetching measurements in range:', error);
      return []; // Return empty array on error
    }
  }
  

  

}

export const deviceService = new DeviceService();
