interface TelemetryData {
  voltages: number[];
  currents: number[];
  frequency: number[];
  power: number[];
  isConnected: boolean;
  timestamp?: string;
  device_id?: string;
}

class EventHubService {
  private pollingInterval: number = 10000; // 10 seconds
  private timerId: number | null = null;

  constructor() {
    console.log('EventHubService initialized');
  }

  async subscribe(callback: (data: TelemetryData) => void, deviceId?: string) {
    console.log('Starting telemetry polling...');

    // Initial state - disconnected
    callback({
      voltages: [],
      currents: [],
      frequency: [],
      power: [],
      isConnected: false,
      device_id: deviceId
    });

    // Function to fetch telemetry data
    const fetchTelemetry = async () => {
      try {
        // Use the device-specific endpoint if deviceId is provided
        const url = deviceId
          ? `http://localhost:5000/api/telemetry/${deviceId}`
          : 'http://localhost:5000/api/telemetry';

        console.log(`Fetching telemetry from: ${url}`);
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data: TelemetryData = await response.json();
        console.log('Fetched telemetry data:', data);
        callback({
          voltages: data.voltages || [],
          currents: data.currents || [],
          frequency: data.frequency || [],
          power: data.power || [],
          isConnected: data.isConnected,
          timestamp: data.timestamp,
          device_id: data.device_id
        });
      } catch (error) {
        console.error('Error fetching telemetry:', error);
        callback({
          voltages: [],
          currents: [],
          frequency: [],
          power: [],
          isConnected: false,
          device_id: deviceId
        });
      }
    };

    // Start polling
    fetchTelemetry(); // Fetch immediately
    this.timerId = window.setInterval(fetchTelemetry, this.pollingInterval);

    return {
      close: () => {
        if (this.timerId) {
          clearInterval(this.timerId);
          this.timerId = null;
          console.log('Telemetry polling stopped.');
        }
      }
    };
  }

  async close() {
    if (this.timerId) {
      clearInterval(this.timerId);
      this.timerId = null;
      console.log('Telemetry polling stopped.');
    }
  }
}

export const eventHubService = new EventHubService();

