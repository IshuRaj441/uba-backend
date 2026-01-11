import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Button, 
  Divider, 
  CircularProgress,
  Paper
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Business as BusinessIcon,
  SwapHoriz as ConvertIcon,
  History as HistoryIcon,
  CreditCard as CreditCardIcon,
  FileCopy as FileCopyIcon,
  CloudUpload as CloudUploadIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

interface Activity {
  id: number;
  type: 'conversion' | 'lead_generation';
  name: string;
  status: string;
  date: string;
}

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [recentActivities, setRecentActivities] = useState<Activity[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setRecentActivities([
        { id: 1, type: 'conversion', name: 'document.pdf', status: 'completed', date: '2023-05-15' },
        { id: 2, type: 'lead_generation', name: 'Tech Companies', status: 'completed', date: '2023-05-14' },
        { id: 3, type: 'conversion', name: 'presentation.pptx', status: 'completed', date: '2023-05-13' },
      ]);
      setIsLoading(false);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  const getActivityIcon = (type: 'conversion' | 'lead_generation') => {
    switch (type) {
      case 'conversion':
        return <ConvertIcon color="primary" sx={{ fontSize: 40 }} />;
      case 'lead_generation':
        return <BusinessIcon color="primary" sx={{ fontSize: 40 }} />;
      default:
        return <FileCopyIcon color="primary" sx={{ fontSize: 40 }} />;
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Welcome back, {user?.email?.split('@')[0] || 'User'}!
      </Typography>
      
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Credits Card */}
        <Grid item xs={12} md={4}>
          <Card elevation={3}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography color="textSecondary" gutterBottom>
                  Available Credits
                </Typography>
                <CreditCardIcon color="primary" />
              </Box>
              <Typography variant="h4" component="div">
                {user?.credits || 0}
              </Typography>
              <Button 
                variant="contained" 
                color="primary" 
                size="small" 
                sx={{ mt: 2 }}
                onClick={() => navigate('/billing')}
              >
                Buy More
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={8}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Grid container spacing={2} sx={{ width: '100%' }}>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<BusinessIcon />}
                    onClick={() => navigate('/leads')}
                    sx={{ height: '100%', py: 2 }}
                  >
                    Generate Leads
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<CloudUploadIcon />}
                    onClick={() => navigate('/converter')}
                    sx={{ height: '100%', py: 2 }}
                  >
                    Convert File
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<FileCopyIcon />}
                    onClick={() => navigate('/my-files')}
                    sx={{ height: '100%', py: 2 }}
                  >
                    My Files
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<HistoryIcon />}
                    onClick={() => navigate('/history')}
                    sx={{ height: '100%', py: 2 }}
                  >
                    History
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Card elevation={3} sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recent Activity
          </Typography>
          {isLoading ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : (
            <Box>
              {recentActivities.map((activity) => (
                <Box key={activity.id} mb={2}>
                  <Box display="flex" alignItems="center" p={2}>
                    <Box mr={2}>
                      {getActivityIcon(activity.type)}
                    </Box>
                    <Box flexGrow={1}>
                      <Typography variant="subtitle1">
                        {activity.type === 'conversion' 
                          ? `Converted ${activity.name}` 
                          : `Generated leads for ${activity.name}`}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        {new Date(activity.date).toLocaleDateString()} • {activity.status}
                      </Typography>
                    </Box>
                    <Button 
                      variant="text" 
                      color="primary" 
                      onClick={() => navigate(activity.type === 'conversion' ? '/my-files' : '/leads')}
                    >
                      View
                    </Button>
                  </Box>
                  <Divider />
                </Box>
              ))}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Tips & Updates */}
      <Card elevation={3}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Tips & Updates
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={4}>
              <Box p={2}>
                <Typography variant="subtitle2" gutterBottom>
                  <Box component="span" color="primary.main" mr={1}>•</Box>
                  New Feature
                </Typography>
                <Typography variant="body2">
                  Try our new bulk file conversion tool to process multiple files at once!
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Box p={2}>
                <Typography variant="subtitle2" gutterBottom>
                  <Box component="span" color="primary.main" mr={1}>•</Box>
                  Pro Tip
                </Typography>
                <Typography variant="body2">
                  Save credits by scheduling lead generation during off-peak hours.
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Box p={2}>
                <Typography variant="subtitle2" gutterBottom>
                  <Box component="span" color="primary.main" mr={1}>•</Box>
                  Coming Soon
                </Typography>
                <Typography variant="body2">
                  API access for developers to integrate directly with our services.
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Dashboard;