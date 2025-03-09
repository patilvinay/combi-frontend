import { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Paper, 
  Grid,
  ThemeProvider,
  createTheme,
  CssBaseline
} from '@mui/material';
import ElectricMeterIcon from '@mui/icons-material/ElectricMeter';

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
}

function App() {
  const [telemetryData, setTelemetryData] = useState<TelemetryData>({
    voltages: [],
    currents: []
  });

  const fetchData = async () => {
    try {
      // Sample data - replace with actual IoT Hub data fetching
      const sampleData = {
        voltages: [5.0, 10.0, 15.0, 20.0, 25.0, 30.0],
        currents: [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
      };
      setTelemetryData(sampleData);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom sx={{ color: 'primary.main', display: 'flex', alignItems: 'center', gap: 2 }}>
          <ElectricMeterIcon sx={{ fontSize: 40 }} />
          IoT Device Dashboard
        </Typography>
        
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
                }}
              >
                <Typography variant="h6" gutterBottom sx={{ color: 'primary.main', borderBottom: '1px solid rgba(144, 202, 249, 0.2)', pb: 1 }}>
                  Channel {index + 1}
                </Typography>
                
                <Grid container spacing={2} sx={{ mt: 1 }}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Voltage
                    </Typography>
                    <Typography variant="h4" sx={{ color: '#8884d8', fontWeight: 'bold' }}>
                      {telemetryData.voltages[index]?.toFixed(1) || '0.0'}
                      <Typography component="span" variant="h6" sx={{ ml: 1, opacity: 0.8 }}>V</Typography>
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Current
                    </Typography>
                    <Typography variant="h4" sx={{ color: '#82ca9d', fontWeight: 'bold' }}>
                      {telemetryData.currents[index]?.toFixed(1) || '0.0'}
                      <Typography component="span" variant="h6" sx={{ ml: 1, opacity: 0.8 }}>A</Typography>
                    </Typography>
                  </Grid>
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
