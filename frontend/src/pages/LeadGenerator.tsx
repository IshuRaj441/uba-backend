import React, { useState } from 'react';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Grid,
  Card,
  CardContent,
  CardActions,
  Divider,
  CircularProgress,
  Alert,
  Chip,
  IconButton,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Avatar,
} from '@mui/material';
import { 
  Search as SearchIcon, 
  FileDownload as FileDownloadIcon,
  Business as BusinessIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  Language as WebsiteIcon,
  LocationOn as LocationIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

interface Lead {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  website?: string;
  address: string;
  rating: number;
  industry: string;
  isSaved: boolean;
}

const LeadGenerator: React.FC = () => {
  const { user } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);

  const formik = useFormik({
    initialValues: {
      keyword: '',
      location: '',
      industry: '',
    },
    validationSchema: Yup.object({
      keyword: Yup.string().required('Keyword is required'),
      location: Yup.string().required('Location is required'),
    }),
    onSubmit: async (values) => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Simulate API call with mock data
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        // Mock data - in a real app, this would come from the API
        const mockLeads: Lead[] = Array.from({ length: 12 }, (_, i) => ({
          id: `lead-${i + 1}`,
          name: `${values.keyword} Business ${i + 1}`,
          email: `contact@${values.keyword.toLowerCase()}${i + 1}.com`,
          phone: `+1 (555) ${Math.floor(100 + Math.random() * 900)}-${Math.floor(1000 + Math.random() * 9000)}`,
          website: `https://${values.keyword.toLowerCase()}${i + 1}.com`,
          address: `${i + 100} ${values.location} St, ${values.location}, ${['NY', 'CA', 'TX', 'FL', 'IL'][i % 5]} ${10000 + i}`,
          rating: Math.floor(1 + Math.random() * 5),
          industry: values.industry || 'Technology',
          isSaved: false,
        }));

        setLeads(mockLeads);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to generate leads');
      } finally {
        setIsLoading(false);
      }
    },
  });

  const handleSaveLead = (leadId: string) => {
    setLeads(leads.map(lead => 
      lead.id === leadId ? { ...lead, isSaved: !lead.isSaved } : lead
    ));
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleExportLeads = () => {
    // In a real app, this would generate a CSV or similar
    const csvContent = [
      ['Name', 'Email', 'Phone', 'Website', 'Address', 'Rating', 'Industry'],
      ...leads.map(lead => [
        lead.name,
        lead.email || '',
        lead.phone || '',
        lead.website || '',
        lead.address,
        lead.rating,
        lead.industry,
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `leads-${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const renderRating = (rating: number) => {
    return Array(5).fill(0).map((_, i) => (
      i < rating ? 
        <StarIcon key={i} color="primary" fontSize="small" /> : 
        <StarBorderIcon key={i} fontSize="small" />
    ));
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Lead Generator
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        Generate targeted business leads by industry, location, and keywords.
      </Typography>

      <Paper sx={{ p: 3, mb: 4 }} elevation={3}>
        <form onSubmit={formik.handleSubmit}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                id="keyword"
                name="keyword"
                label="Business Type/Keyword"
                value={formik.values.keyword}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.keyword && Boolean(formik.errors.keyword)}
                helperText={formik.touched.keyword && formik.errors.keyword}
                placeholder="e.g. Software Development"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                id="location"
                name="location"
                label="Location"
                value={formik.values.location}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.location && Boolean(formik.errors.location)}
                helperText={formik.touched.location && formik.errors.location}
                placeholder="e.g. New York, NY"
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <TextField
                fullWidth
                id="industry"
                name="industry"
                label="Industry (Optional)"
                value={formik.values.industry}
                onChange={formik.handleChange}
                placeholder="e.g. Technology"
              />
            </Grid>
            <Grid item xs={12} md={2} sx={{ display: 'flex', alignItems: 'center' }}>
              <Button
                fullWidth
                type="submit"
                variant="contained"
                color="primary"
                size="large"
                startIcon={<SearchIcon />}
                disabled={isLoading}
                sx={{ height: '56px' }}
              >
                {isLoading ? <CircularProgress size={24} /> : 'Find Leads'}
              </Button>
            </Grid>
          </Grid>
        </form>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 4 }}>
          {error}
        </Alert>
      )}

      {leads.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              {leads.length} {leads.length === 1 ? 'Lead' : 'Leads'} Found
            </Typography>
            <Button
              variant="outlined"
              startIcon={<FileDownloadIcon />}
              onClick={handleExportLeads}
              disabled={leads.length === 0}
            >
              Export to CSV
            </Button>
          </Box>
          
          <TableContainer component={Paper} elevation={3}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Business</TableCell>
                  <TableCell>Contact</TableCell>
                  <TableCell>Location</TableCell>
                  <TableCell>Rating</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {leads.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((lead) => (
                  <TableRow key={lead.id} hover>
                    <TableCell>
                      <Box display="flex" alignItems="center">
                        <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                          <BusinessIcon />
                        </Avatar>
                        <Box>
                          <Typography variant="subtitle1">{lead.name}</Typography>
                          <Chip 
                            label={lead.industry} 
                            size="small" 
                            sx={{ mt: 0.5 }}
                          />
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box>
                        {lead.email && (
                          <Box display="flex" alignItems="center" mb={0.5}>
                            <EmailIcon color="action" fontSize="small" sx={{ mr: 1 }} />
                            <Typography variant="body2">{lead.email}</Typography>
                          </Box>
                        )}
                        {lead.phone && (
                          <Box display="flex" alignItems="center">
                            <PhoneIcon color="action" fontSize="small" sx={{ mr: 1 }} />
                            <Typography variant="body2">{lead.phone}</Typography>
                          </Box>
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center">
                        <LocationIcon color="action" fontSize="small" sx={{ mr: 1 }} />
                        <Typography variant="body2">{lead.address}</Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center">
                        {renderRating(lead.rating)}
                        <Typography variant="body2" sx={{ ml: 1 }}>({lead.rating}.0)</Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box display="flex" gap={1}>
                        <Tooltip title={lead.isSaved ? 'Remove from saved' : 'Save lead'}>
                          <IconButton 
                            size="small" 
                            color={lead.isSaved ? 'primary' : 'default'}
                            onClick={() => handleSaveLead(lead.id)}
                          >
                            {lead.isSaved ? <StarIcon /> : <StarBorderIcon />}
                          </IconButton>
                        </Tooltip>
                        {lead.website && (
                          <Tooltip title="Visit website">
                            <IconButton 
                              size="small" 
                              href={lead.website} 
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              <WebsiteIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <TablePagination
              rowsPerPageOptions={[5, 10, 25]}
              component="div"
              count={leads.length}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
            />
          </TableContainer>
        </Box>
      )}

      {leads.length === 0 && !isLoading && (
        <Paper 
          elevation={3} 
          sx={{ 
            p: 4, 
            textAlign: 'center',
            background: 'linear-gradient(45deg, #f5f7fa 0%, #e8ecf1 100%)',
          }}
        >
          <BusinessIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2, opacity: 0.6 }} />
          <Typography variant="h6" color="textSecondary" gutterBottom>
            No leads generated yet
          </Typography>
          <Typography variant="body1" color="textSecondary" paragraph>
            Enter your search criteria above to find potential business leads.
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Tip: Be specific with your keywords for more relevant results.
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default LeadGenerator;
