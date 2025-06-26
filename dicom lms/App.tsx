import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useParams } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { 
  Box, 
  AppBar, 
  Toolbar, 
  Typography, 
  Container,
  Alert,
  CircularProgress
} from '@mui/material';
import MedicalImagingActivity from './components/MedicalImagingActivity';
import StudySelector from './components/StudySelector';
import './App.css';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#0a0a0a',
      paper: '#1a1a1a',
    },
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#1a1a1a',
        },
      },
    },
  },
});

const ViewerWrapper: React.FC = () => {
  const { studyUID } = useParams<{ studyUID: string }>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate loading delay for demonstration
    const timer = setTimeout(() => {
      setLoading(false);
    }, 1000);

    return () => clearTimeout(timer);
  }, [studyUID]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="70vh">
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Loading medical imaging viewer...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      </Container>
    );
  }

  return (
    <Box sx={{ height: 'calc(100vh - 64px)', overflow: 'hidden' }}>
      <MedicalImagingActivity studyUID={studyUID || ''} />
    </Box>
  );
};

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ flexGrow: 1 }}>
          <AppBar position="static">
            <Toolbar>
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                Medical LMS - Imaging Viewer
              </Typography>
              <Typography variant="body2" sx={{ mr: 2 }}>
                Unified DICOM & Pathology Viewer
              </Typography>
            </Toolbar>
          </AppBar>

          <Routes>
            <Route path="/" element={<StudySelector />} />
            <Route path="/viewer/:studyUID" element={<ViewerWrapper />} />
            <Route path="/study/:studyUID" element={<ViewerWrapper />} />
          </Routes>
        </Box>
      </Router>
    </ThemeProvider>
  );
};

export default App;
