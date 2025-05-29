import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

const theme = createTheme({
  palette: {
    mode: 'dark',
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ p: 3 }}>
        <Typography variant="h3" component="h1" gutterBottom>
          FPL H2H Analyzer
        </Typography>
        <Typography variant="h6" gutterBottom>
          Material-UI Theme Test
        </Typography>
        <Typography variant="body1" paragraph>
          ✅ React: Working
        </Typography>
        <Typography variant="body1" paragraph>
          ✅ Material-UI: Working
        </Typography>
        <Typography variant="body1" paragraph>
          ✅ Dark Theme: Working
        </Typography>
        <Button variant="contained" color="primary" sx={{ mt: 2 }}>
          Test Button
        </Button>
      </Box>
    </ThemeProvider>
  );
}

export default App;