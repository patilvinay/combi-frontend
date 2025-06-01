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
  SelectChangeEvent,
  Tabs,
  Tab,
  Card,
  CardContent
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
  ResponsiveContainer,
  Text
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
  const [timeRange, setTimeRange] = useState<number>(2);
  const [selectedMetric, setSelectedMetric] = useState<string>('v');
  const [selectedChannel, setSelectedChannel] = useState<number>(0);
  const [selectedChannels, setSelectedChannels] = useState<{[key: number]: boolean}>({
    0: true, 1: true, 2: true, 3: true, 4: true, 5: true, 6: true
  });

  useEffect(() => {
    if (!deviceId) {
      setError('No device ID provided');
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch latest measurement
        const latest = await deviceService.getLatestMeasurement(deviceId);
        setLatestMeasurement(latest);
        
        // Fetch time series data
        const endTime = new Date();
        const startTime = new Date();
        startTime.setHours(startTime.getHours() - timeRange);
        
        const timeSeries = await deviceService.getMeasurementsInRange(
          deviceId,
          startTime.toISOString(),
          endTime.toISOString()
        );
        
        setTimeSeriesData(timeSeries || []);
      } catch (err) {
        console.error('Error fetching device data:', err);
        setError('Failed to fetch device data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Set up polling every 30 seconds
    const intervalId = setInterval(fetchData, 30000);
    
    return () => clearInterval(intervalId);
  }, [deviceId, timeRange]);

  const handleTimeRangeChange = (event: SelectChangeEvent) => {
    setTimeRange(Number(event.target.value));
  };

  const handleMetricChange = (event: SelectChangeEvent) => {
    setSelectedMetric(event.target.value);
  };

  const formatChartData = (data: Measurement[]) => {
    if (!data || data.length === 0) return [];
    
    return data.map(measurement => {
      const formattedData: any = {
        time: new Date(measurement.enqueued_time).toLocaleTimeString()
      };
      
      // Add data for each channel
      measurement.phases.forEach((phase, index) => {
        if (phase) {
          formattedData[`phase${index + 1}`] = phase[selectedMetric as keyof typeof phase];
        }
      });
      
      return formattedData;
    });
  };

  const getMetricUnit = () => {
    switch (selectedMetric) {
      case 'v': return 'Voltage (V)';
      case 'i': return 'Current (A)';
      case 'p': return 'Power (W)';
      case 'f': return 'Frequency (Hz)';
      case 'pf': return 'Power Factor';
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
      default: return '';
    }
  };

  const getLineColors = () => [
    '#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE', '#00C49F', '#FFBB28'
  ];

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header with back button */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Button 
          component={Link} 
          to="/devices" 
          startIcon={<ArrowBackIcon />}
          sx={{ mr: 2 }}
        >
          Back to Devices
        </Button>
        <Typography variant="h4" component="h1">
          Device: {deviceId}
        </Typography>
      </Box>

      {/* Latest Measurement */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
          <Tabs 
            value={selectedChannel}
            onChange={(_, newValue) => setSelectedChannel(newValue)}
            variant="scrollable"
            scrollButtons="auto"
          >
            {Array.from({ length: 7 }).map((_, index) => (
              <Tab 
                key={`tab-${index}`}
                label={`Channel ${index + 1}${!latestMeasurement?.phases?.[index] ? ' (N/A)' : ''}`}
                disabled={!latestMeasurement?.phases?.[index]}
                sx={{ 
                  minWidth: 120,
                  opacity: latestMeasurement?.phases?.[index] ? 1 : 0.7,
                  '&.Mui-selected': {
                    color: getLineColors()[index],
                    borderBottom: `2px solid ${getLineColors()[index]}`
                  }
                }}
              />
            ))}
          </Tabs>
        </Box>

        {latestMeasurement?.phases?.[selectedChannel] ? (
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">Voltage (V)</Typography>
                  <Typography variant="h5" color={getLineColors()[selectedChannel]}>
                    {latestMeasurement.phases[selectedChannel]?.v?.toFixed(2) || 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">Current (A)</Typography>
                  <Typography variant="h5" color={getLineColors()[selectedChannel]}>
                    {latestMeasurement.phases[selectedChannel]?.i?.toFixed(2) || 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">Power (W)</Typography>
                  <Typography variant="h5" color={getLineColors()[selectedChannel]}>
                    {latestMeasurement.phases[selectedChannel]?.p?.toFixed(2) || 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">Frequency (Hz)</Typography>
                  <Typography variant="h5" color={getLineColors()[selectedChannel]}>
                    {latestMeasurement.phases[selectedChannel]?.f?.toFixed(2) || 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">Power Factor</Typography>
                  <Typography variant="h5" color={getLineColors()[selectedChannel]}>
                    {latestMeasurement.phases[selectedChannel]?.pf?.toFixed(2) || 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">Last Updated</Typography>
                  <Typography variant="body2">
                    {latestMeasurement ? new Date(latestMeasurement.enqueued_time).toLocaleString() : 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        ) : (
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            minHeight: 200,
            bgcolor: 'action.hover',
            borderRadius: 1,
            p: 3,
            textAlign: 'center'
          }}>
            <Typography variant="body1" color="text.secondary">
              No data available for Channel {selectedChannel + 1}
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Time Series Chart */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6">
            {getMetricName()} Time Series
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel id="time-range-label">Time Range</InputLabel>
              <Select
                labelId="time-range-label"
                value={timeRange.toString()}
                label="Time Range"
                onChange={handleTimeRangeChange}
              >
                <MenuItem value={1}>1 Hour</MenuItem>
                <MenuItem value={2}>2 Hours</MenuItem>
                <MenuItem value={6}>6 Hours</MenuItem>
                <MenuItem value={12}>12 Hours</MenuItem>
                <MenuItem value={24}>24 Hours</MenuItem>
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel id="metric-label">Metric</InputLabel>
              <Select
                labelId="metric-label"
                value={selectedMetric}
                label="Metric"
                onChange={handleMetricChange}
              >
                <MenuItem value="v">Voltage</MenuItem>
                <MenuItem value="i">Current</MenuItem>
                <MenuItem value="p">Power</MenuItem>
                <MenuItem value="f">Frequency</MenuItem>
                <MenuItem value="pf">Power Factor</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Box>

        {/* Channel Selection */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>Show Channels:</Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {Array.from({ length: 7 }).map((_, index) => {
              const hasData = timeSeriesData.some(m => m.phases?.[index]);
              return (
                <Button
                  key={`channel-btn-${index}`}
                  variant={selectedChannels[index] ? 'contained' : 'outlined'}
                  size="small"
                  onClick={() => {
                    setSelectedChannels(prev => ({
                      ...prev,
                      [index]: !prev[index]
                    }));
                  }}
                  disabled={!hasData}
                  sx={{
                    minWidth: 40,
                    bgcolor: selectedChannels[index] ? getLineColors()[index] : 'transparent',
                    color: selectedChannels[index] ? 'white' : 'text.primary',
                    borderColor: getLineColors()[index],
                    opacity: hasData ? 1 : 0.6,
                    '&:hover': {
                      bgcolor: selectedChannels[index] ? getLineColors()[index] : 'action.hover',
                    },
                  }}
                >
                  {index + 1}
                </Button>
              );
            })}
          </Box>
        </Box>

        {/* Chart */}
        <Box sx={{ width: '100%', height: 400 }}>
          <ResponsiveContainer>
            <LineChart
              data={formatChartData(timeSeriesData)}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <defs>
                <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8884d8" stopOpacity={0.1}/>
                  <stop offset="95%" stopColor="#8884d8" stopOpacity={0.05}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis label={{ value: getMetricUnit(), angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              
              {/* No data watermark */}
              {timeSeriesData.length === 0 && (
                <Text
                  x="50%"
                  y="50%"
                  textAnchor="middle"
                  verticalAnchor="middle"
                  style={{
                    fontSize: 24,
                    fill: 'rgba(0, 0, 0, 0.2)',
                    fontWeight: 'bold',
                    pointerEvents: 'none'
                  }}
                >
                  No Data Available
                </Text>
              )}
              
              {/* Channel lines */}
              {Array.from({ length: 7 }).map((_, index) => {
                if (!selectedChannels[index]) return null;
                
                const hasData = timeSeriesData.some(m => m.phases?.[index]);
                const color = getLineColors()[index];
                
                if (!hasData) {
                  return (
                    <Line
                      key={`channel-${index}`}
                      type="monotone"
                      dataKey={`phase${index + 1}`}
                      name={`Channel ${index + 1} (No Data)`}
                      stroke={color}
                      strokeDasharray="5 5"
                      strokeOpacity={0.5}
                      dot={false}
                      activeDot={false}
                      connectNulls={true}
                    />
                  );
                }
                
                return (
                  <Line
                    key={`channel-${index}`}
                    type="monotone"
                    dataKey={`phase${index + 1}`}
                    name={`Channel ${index + 1}`}
                    stroke={color}
                    activeDot={{ r: 4 }}
                    connectNulls={true}
                  />
                );
              })}
            </LineChart>
          </ResponsiveContainer>
        </Box>
      </Paper>
    </Container>
  );
};

export default DeviceDetail;
