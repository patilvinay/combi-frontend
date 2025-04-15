import React from 'react';
import { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  Grid,
  ThemeProvider,
  createTheme,
  CssBaseline,
  Alert,
  Chip,
  TextField,
  Button,
  Box
} from '@mui/material';
import ElectricMeterIcon from '@mui/icons-material/ElectricMeter';
import SignalWifiStatusbar4BarIcon from '@mui/icons-material/SignalWifiStatusbar4Bar';
import SignalWifiOffIcon from '@mui/icons-material/SignalWifiOff';
import { eventHubService } from './services/eventHub';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
    },
    secondary: {
      main: '#f48fb1',
    },
    background: {
      default: '#0a1929',
      paper: '#1e2a3a',
    },
  },
});

interface TelemetryData {
  voltages: number[];
  currents: number[];
  frequency: number[];
  power: number[];
  isConnected: boolean;
  device_id?: string;
}

function App() {
  const [telemetryData, setTelemetryData] = useState<TelemetryData>({
    voltages: [],
    currents: [],
    frequency: [],
    power: [],
    isConnected: false,
    device_id: undefined
  });
  const [error, setError] = useState<string | null>(null);

  // State to store the device ID input
  const [deviceIdInput, setDeviceIdInput] = useState<string>('');
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | undefined>(undefined);

  useEffect(() => {
    let subscription: any;

    const connectToEventHub = async () => {
      try {
        setError(null);
        subscription = await eventHubService.subscribe((data) => {
          setTelemetryData(data);
        }, selectedDeviceId);
      } catch (err) {
        setError('Failed to connect to IoT Hub. Please check your connection settings.');
        console.error('Error connecting to Event Hub:', err);
      }
    };

    connectToEventHub();

    return () => {
      if (subscription) {
        subscription.close();
      }
      eventHubService.close();
    };
  }, [selectedDeviceId]);

  // Handler for device ID input change
  const handleDeviceIdChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setDeviceIdInput(event.target.value);
  };

  // Handler for device ID form submission
  const handleDeviceIdSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setSelectedDeviceId(deviceIdInput);
  };

  const getConnectionStatusChip = () => (
    <Chip
      icon={telemetryData.isConnected ? <SignalWifiStatusbar4BarIcon /> : <SignalWifiOffIcon />}
      label={telemetryData.isConnected ? "Connected" : "Disconnected"}
      color={telemetryData.isConnected ? "success" : "error"}
      variant="outlined"
      sx={{ ml: 2 }}
    />
  );

  if (error) {
    return (
      <ThemeProvider theme={darkTheme}>
        <CssBaseline />
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
          <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
        </Container>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom sx={{
          color: 'primary.main',
          display: 'flex',
          alignItems: 'center'
        }}>
          <ElectricMeterIcon sx={{ fontSize: 40, mr: 2 }} />
          IoT Device Dashboard
          {getConnectionStatusChip()}
          {telemetryData.device_id && (
            <Chip
              label={`Device: ${telemetryData.device_id}`}
              color="primary"
              variant="outlined"
              sx={{ ml: 2 }}
            />
          )}
        </Typography>

        {/* Device ID input form */}
        <Paper sx={{ p: 2, mb: 3, background: 'linear-gradient(145deg, #1e2a3a 0%, #141e2a 100%)' }}>
          <form onSubmit={handleDeviceIdSubmit}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <TextField
                label="Device ID"
                variant="outlined"
                value={deviceIdInput}
                onChange={handleDeviceIdChange}
                placeholder="Enter device ID"
                size="small"
                sx={{ mr: 2, flexGrow: 1 }}
              />
              <Button
                type="submit"
                variant="contained"
                color="primary"
              >
                Connect to Device
              </Button>
            </Box>
          </form>
        </Paper>

        <Grid container spacing={3}>
          {[...Array(8)].map((_, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Paper
                sx={{
                  p: 3,
                  display: 'flex',
                  flexDirection: 'column',
                  height: '100%',
                  background: 'linear-gradient(145deg, #1e2a3a 0%, #141e2a 100%)',
                  borderRadius: 2,
                  boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
                  opacity: telemetryData.isConnected ? 1 : 0.7,
                }}
              >
                <Typography variant="h6" gutterBottom sx={{
                  color: 'primary.main',
                  borderBottom: '1px solid rgba(144, 202, 249, 0.2)',
                  pb: 1
                }}>
                  {index === 7 ? 'Frequency' : `Channel ${index + 1}`}
                </Typography>

                <Grid container spacing={2} sx={{ mt: 1 }}>
                  {index !== 7 ? (
                    <>
                      <Grid item xs={4}>
                        <Typography variant="body2" color="text.secondary">
                          Voltage
                        </Typography>
                        <Typography variant="h4" sx={{
                          color: '#8884d8',
                          fontWeight: 'bold',
                          opacity: telemetryData.isConnected ? 1 : 0.7
                        }}>
                          {telemetryData.isConnected ?
                            (telemetryData.voltages[index]?.toFixed(1) || '0.0') :
                            '--'
                          }
                          <Typography component="span" variant="h6" sx={{ ml: 1, opacity: 0.8 }}>V</Typography>
                        </Typography>
                      </Grid>
                      <Grid item xs={4}>
                        <Typography variant="body2" color="text.secondary">
                          Current
                        </Typography>
                        <Typography variant="h4" sx={{
                          color: '#82ca9d',
                          fontWeight: 'bold',
                          opacity: telemetryData.isConnected ? 1 : 0.7
                        }}>
                          {telemetryData.isConnected ?
                            (telemetryData.currents[index]?.toFixed(1) || '0.0') :
                            '--'
                          }
                          <Typography component="span" variant="h6" sx={{ ml: 1, opacity: 0.8 }}>A</Typography>
                        </Typography>
                      </Grid>
                      <Grid item xs={4}>
                        <Typography variant="body2" color="text.secondary">
                          Power
                        </Typography>
                        <Typography variant="h4" sx={{
                          color: '#ff7300',
                          fontWeight: 'bold',
                          opacity: telemetryData.isConnected ? 1 : 0.7
                        }}>
                          {telemetryData.isConnected ?
                            (telemetryData.power[index]?.toFixed(2) || '0.00') :
                            '0.00'
                          }
                          <Typography component="span" variant="h6" sx={{ ml: 1, opacity: 0.8 }}>W</Typography>
                        </Typography>
                      </Grid>
                    </>
                  ) : (
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">
                        Frequency
                      </Typography>
                      <Typography variant="h4" sx={{
                        color: '#ff7300',
                        fontWeight: 'bold',
                        opacity: telemetryData.isConnected ? 1 : 0.7
                      }}>
                        {telemetryData.isConnected ?
                          (telemetryData.frequency[0]?.toFixed(1) || '0.0') :
                          '--'
                        }
                        <Typography component="span" variant="h6" sx={{ ml: 1, opacity: 0.8 }}>Hz</Typography>
                      </Typography>
                    </Grid>
                  )}
                </Grid>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Container>
    </ThemeProvider>
  );
}

export default App;
