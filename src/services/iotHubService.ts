import { EventHubConsumerClient } from '@azure/event-hubs';

interface TelemetryData {
  voltages: number[];
  currents: number[];
}

class IoTHubService {
  private client: EventHubConsumerClient | null = null;
  private connectionString: string;
  private consumerGroup: string;

  constructor() {
    // Load from environment variables
    this.connectionString = import.meta.env.VITE_EVENTHUB_CONNECTION_STRING || '';
    this.consumerGroup = import.meta.env.VITE_CONSUMER_GROUP || '$Default';
  }

  async initialize() {
    if (!this.client && this.connectionString) {
      this.client = new EventHubConsumerClient(
        this.consumerGroup,
        this.connectionString
      );
    }
  }

  async getTelemetryData(): Promise<TelemetryData> {
    if (!this.client) {
      await this.initialize();
    }

    return new Promise((resolve, reject) => {
      const voltages: number[] = [];
      const currents: number[] = [];

      try {
        this.client?.subscribe({
          processEvents: async (events, context) => {
            for (const event of events) {
              const telemetry = JSON.parse(event.body);
              if (telemetry.voltage !== undefined) {
                voltages.push(telemetry.voltage);
              }
              if (telemetry.current !== undefined) {
                currents.push(telemetry.current);
              }
            }
            await context.updateCheckpoint(events[events.length - 1]);
          },
          processError: async (err) => {
            console.error('Error processing events:', err);
            reject(err);
          }
        });

        // Resolve after collecting some data or timeout
        setTimeout(() => {
          resolve({ voltages, currents });
        }, 5000);
      } catch (error) {
        reject(error);
      }
    });
  }

  async close() {
    if (this.client) {
      await this.client.close();
      this.client = null;
    }
  }
}

export const iotHubService = new IoTHubService();
export type { TelemetryData };
