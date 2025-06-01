import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  Container, 
  Typography, 
  Paper, 
  Box,
  CircularProgress,
  Alert,
  Grid,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';
import { deviceService, Measurement } from '../services/deviceService';

interface DeviceDetailParams {
  deviceId: string;
  [key: string]: string | undefined;
}

const DeviceDetail: React.FC = () => {
  const { deviceId } = useParams<DeviceDetailParams>();
  const [latestMeasurement, setLatestMeasurement] = useState<Measurement | null>(null);
  const [timeSeriesData, setTimeSeriesData] = useState<Measurement[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<number>(2); // Default to 2 hours
  const [selectedMetric, setSelectedMetric] = useState<string>('v'); // Default to voltage

  useEffect(() => {
    if (!deviceId) {
      setError('Device ID is required');
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch latest measurement using device service
        const latest = await deviceService.getLatestMeasurement(deviceId);
        setLatestMeasurement(latest);
        
        // Fetch time series data using device service
        const timeSeries = await deviceService.getRecentMeasurements(deviceId, timeRange);
        setTimeSeriesData(timeSeries);
      } catch (error) {
        console.error('Error fetching device data:', error);
        setError('Failed to fetch device data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Set up polling every 30 seconds to keep data fresh
    const intervalId = setInterval(fetchData, 30000);
    
    return () => {
      clearInterval(intervalId);
    };
  }, [deviceId, timeRange]);
  
  const handleTimeRangeChange = (event: SelectChangeEvent) => {
    setTimeRange(Number(event.target.value));
  };

  const handleMetricChange = (event: SelectChangeEvent) => {
    setSelectedMetric(event.target.value);
  };

  const formatChartData = (data: Measurement[]) => {
    if (!data || data.length === 0) {
      return [];
    }
    
    return data.map(measurement => {
      const result: any = {
        time: new Date(measurement.enqueued_time).toLocaleTimeString(),
        timestamp: measurement.enqueued_time,
      };
      
      // Ensure we handle all 7 possible channels
      for (let i = 0; i < 7; i++) {
        const phase = measurement.phases[i];
        
        // Make sure the phase exists and has the selected metric
        if (phase && phase[selectedMetric as keyof typeof phase] !== undefined) {
          result[`phase${i + 1}`] = phase[selectedMetric as keyof typeof phase];
        } else {
          result[`phase${i + 1}`] = null; // Use null instead of 0 to handle missing data properly
        }
      }
      
      return result;
    }).sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
  };

  const getMetricUnit = () => {
    switch (selectedMetric) {
      case 'v': return 'V';
      case 'i': return 'A';
      case 'p': return 'W';
      case 'f': return 'Hz';
      case 'pf': return '';
      default: return '';
    }
  };

  const getMetricName = () => {
    switch (selectedMetric) {
      case 'v': return 'Voltage';
      case 'i': return 'Current';
      case 'p': return 'Power';
      case 'f': return 'Frequency';
      case 'pf': return 'Power Factor';
      default: return selectedMetric;
    }
  };

  const getLineColors = () => [
    '#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088fe', '#00C49F', '#FFBB28'
  ];

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Button 
          component={Link} 
          to="/devices" 
          startIcon={<ArrowBackIcon />}
          sx={{ mr: 2 }}
        >
          Back to Devices
        </Button>
        <Typography variant="h4" component="h1" sx={{ mb: 0 }}>
          Device: {deviceId}
        </Typography>
      </Box>
      
      {latestMeasurement ? (
        <Paper sx={{ p: 3, mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            Latest Measurement
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Timestamp: {new Date(latestMeasurement.enqueued_time).toLocaleString()}
          </Typography>
          
          <Grid container spacing={3} sx={{ mt: 1 }}>
            {/* Display up to 7 channels (phases) */}
            {Array.from({ length: 7 }).map((_, index) => {
              const phase = latestMeasurement.phases[index];
              if (!phase) return null; // Skip if phase doesn't exist
              
              return (
                <Grid item xs={12} sm={6} md={4} lg={3} key={index}>
                  <Paper elevation={2} sx={{ p: 2 }}>
                    <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold', color: getLineColors()[index] }}>
                      Channel {index + 1}
                    </Typography>
                    <Typography variant="body2">
                      Voltage: {phase.v?.toFixed(2) || 'N/A'} V
                    </Typography>
                    <Typography variant="body2">
                      Current: {phase.i?.toFixed(2) || 'N/A'} A
                    </Typography>
                    <Typography variant="body2">
                      Power: {phase.p?.toFixed(2) || 'N/A'} W
                    </Typography>
                    <Typography variant="body2">
                      Frequency: {phase.f?.toFixed(2) || 'N/A'} Hz
                    </Typography>
                    <Typography variant="body2">
                      Power Factor: {phase.pf?.toFixed(2) || 'N/A'}
                    </Typography>
                  </Paper>
                </Grid>
              );
            })}
          </Grid>
        </Paper>
      ) : (
        <Paper sx={{ p: 3, mb: 4, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '200px' }}>
          <Typography variant="h6" color="text.secondary">
            No Latest Measurement Data Available
          </Typography>
        </Paper>
      )}
      
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6">
            {getMetricName()} Time Series
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel id="metric-select-label">Metric</InputLabel>
              <Select
                labelId="metric-select-label"
                value={selectedMetric}
                label="Metric"
                onChange={handleMetricChange}
              >
                <MenuItem value="v">Voltage (V)</MenuItem>
                <MenuItem value="i">Current (A)</MenuItem>
                <MenuItem value="p">Power (W)</MenuItem>
                <MenuItem value="f">Frequency (Hz)</MenuItem>
                <MenuItem value="pf">Power Factor</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel id="time-range-select-label">Time Range</InputLabel>
              <Select
                labelId="time-range-select-label"
                value={timeRange.toString()}
                label="Time Range"
                onChange={handleTimeRangeChange}
              >
                <MenuItem value="1">Last 1 hour</MenuItem>
                <MenuItem value="2">Last 2 hours</MenuItem>
                <MenuItem value="6">Last 6 hours</MenuItem>
                <MenuItem value="12">Last 12 hours</MenuItem>
                <MenuItem value="24">Last 24 hours</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Box>
        
        <Box sx={{ width: '100%', height: 400 }}>
          {timeSeriesData.length > 0 ? (
            <ResponsiveContainer>
              <LineChart
                data={formatChartData(timeSeriesData)}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis label={{ value: getMetricUnit(), angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                {/* Display up to 7 channels in the chart */}
                {Array.from({ length: 7 }).map((_, index) => {
                  // Check if we have data for this channel in any measurement
                  const hasChannel = timeSeriesData.some(m => 
                    m.phases[index] && m.phases[index][selectedMetric as keyof typeof m.phases[0]] !== undefined
                  );
                  
                  if (!hasChannel) return null;
                  
                  return (
                    <Line
                      key={`channel${index + 1}`}
                      type="monotone"
                      dataKey={`phase${index + 1}`}
                      name={`Channel ${index + 1}`}
                      stroke={getLineColors()[index % getLineColors().length]}
                      activeDot={{ r: 8 }}
                      connectNulls={true}
                    />
                  );
                })}
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', bgcolor: '#f5f5f5', borderRadius: 1 }}>
              <Typography variant="h6" color="text.secondary">
                No Time Series Data Available
              </Typography>
            </Box>
          )}
        </Box>
      </Paper>
    </Container>
  );
};

export default DeviceDetail;
