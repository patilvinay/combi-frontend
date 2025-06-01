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
  Box,
  Button
} from '@mui/material';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ElectricMeterIcon from '@mui/icons-material/ElectricMeter';
import SignalWifiStatusbar4BarIcon from '@mui/icons-material/SignalWifiStatusbar4Bar';
import SignalWifiOffIcon from '@mui/icons-material/SignalWifiOff';
import { deviceService } from './services/deviceService';
import DeviceList from './components/DeviceList';
import DeviceDetail from './components/DeviceDetail';

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
  powers: number[];
  frequencies: number[];
  powerFactors: number[];
  isConnected: boolean;
  timestamp?: string;
}

function App() {
  const [telemetryData, setTelemetryData] = useState<TelemetryData>({
    voltages: [],
    currents: [],
    powers: [],
    frequencies: [],
    powerFactors: [],
    isConnected: false
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Use a demo device ID for the dashboard
    const demoDeviceId = '48:CA:43:36:71:04';
    let intervalId: number;

    const fetchDeviceData = async () => {
      try {
        setError(null);
        const measurement = await deviceService.getLatestMeasurement(demoDeviceId);
        
        if (!measurement) {
          // No data available
          setTelemetryData(prev => ({ ...prev, isConnected: false }));
          return;
        }
        
        // Extract data from the measurement
        const voltages: number[] = [];
        const currents: number[] = [];
        const powers: number[] = [];
        const frequencies: number[] = [];
        const powerFactors: number[] = [];
        
        measurement.phases.forEach(phase => {
          voltages.push(phase.v);
          currents.push(phase.i);
          powers.push(phase.p);
          frequencies.push(phase.f);
          powerFactors.push(phase.pf);
        });
        
        setTelemetryData({
          voltages,
          currents,
          powers,
          frequencies,
          powerFactors,
          isConnected: true,
          timestamp: measurement.enqueued_time
        });
      } catch (err) {
        console.error('Error fetching device data:', err);
        setTelemetryData(prev => ({ ...prev, isConnected: false }));
        setError('Failed to fetch device data. Please try again later.');
      }
    };

    // Fetch immediately
    fetchDeviceData();
    
    // Then set up polling every 10 seconds
    intervalId = window.setInterval(fetchDeviceData, 10000);

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, []);

  const getConnectionStatusChip = () => (
    <Chip
      icon={telemetryData.isConnected ? <SignalWifiStatusbar4BarIcon /> : <SignalWifiOffIcon />}
      label={telemetryData.isConnected ? "Connected" : "Disconnected"}
      color={telemetryData.isConnected ? "success" : "error"}
      variant="outlined"
      sx={{ ml: 2 }}
    />
  );

  const Dashboard = () => (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h3" component="h1" gutterBottom sx={{ 
          color: 'primary.main', 
          display: 'flex', 
          alignItems: 'center',
          mb: 0
        }}>
          <ElectricMeterIcon sx={{ fontSize: 40, mr: 2 }} />
          IoT Device Dashboard
          {getConnectionStatusChip()}
        </Typography>
        
        <Button 
          variant="contained" 
          color="primary" 
          component={Link} 
          to="/devices"
        >
          View All Devices
        </Button>
      </Box>
      
      <Grid container spacing={3}>
        {[...Array(6)].map((_, index) => (
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
                Channel {index + 1}
              </Typography>
              
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={6}>
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
                <Grid item xs={6}>
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
              </Grid>
            </Paper>
          </Grid>
        ))}
      </Grid>
    </>
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
      <Router>
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/devices" element={<DeviceList />} />
            <Route path="/devices/:deviceId" element={<DeviceDetail />} />
          </Routes>
        </Container>
      </Router>
    </ThemeProvider>
  );
}

export default App;
