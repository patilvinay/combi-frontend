import React from 'react';
import { Link } from 'react-router-dom';
import {
  Container,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  Divider
} from '@mui/material';
import ElectricMeterIcon from '@mui/icons-material/ElectricMeter';

// For demo purposes, we'll use a hardcoded list of devices
// In a real app, this would come from an API
const DEMO_DEVICES = [
  { id: '48:CA:43:36:71:04', name: 'Device 1' },
  { id: '48:CA:43:36:71:05', name: 'Device 2' },
  { id: '48:CA:43:36:71:06', name: 'Device 3' }
];

const DeviceList: React.FC = () => {
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom sx={{ 
        display: 'flex', 
        alignItems: 'center'
      }}>
        <ElectricMeterIcon sx={{ fontSize: 40, mr: 2 }} />
        Devices
      </Typography>
      
      <Paper sx={{ mt: 3 }}>
        <List>
          {DEMO_DEVICES.map((device, index) => (
            <React.Fragment key={device.id}>
              {index > 0 && <Divider />}
              <ListItem disablePadding>
                <ListItemButton component={Link} to={`/devices/${device.id}`}>
                  <ListItemText 
                    primary={device.name} 
                    secondary={`ID: ${device.id}`} 
                  />
                </ListItemButton>
              </ListItem>
            </React.Fragment>
          ))}
        </List>
      </Paper>
    </Container>
  );
};

export default DeviceList;
