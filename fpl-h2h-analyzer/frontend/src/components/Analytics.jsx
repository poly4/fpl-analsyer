import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Chip,
  Divider,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  EmojiEvents,
  Timeline,
  Download,
  Assessment
} from '@mui/icons-material';

function Analytics({ leagueId = 620117 }) {
  const [leagueData, setLeagueData] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reportDialog, setReportDialog] = useState(false);
  const [selectedManagers, setSelectedManagers] = useState({ manager1: '', manager2: '' });
  const [generatingReport, setGeneratingReport] = useState(false);

  useEffect(() => {
    fetchAnalytics();
  }, [leagueId]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`http://localhost:8000/api/league/${leagueId}/overview`);
      if (!response.ok) {
        throw new Error(`Failed to fetch analytics: ${response.status}`);
      }

      const data = await response.json();
      setLeagueData(data);
      
      // Calculate analytics from standings
      const standings = data.standings.standings.results || [];
      calculateAnalytics(standings);
      
    } catch (err) {
      console.error('Error fetching analytics:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const calculateAnalytics = (standings) => {
    if (!standings.length) return;

    // Calculate various analytics
    const totalManagers = standings.length;
    const totalMatches = standings.reduce((sum, team) => sum + (team.matches_played || 0), 0) / 2; // Divide by 2 since each match involves 2 teams
    const avgPointsFor = standings.reduce((sum, team) => sum + (team.points_for || 0), 0) / totalManagers;
    const avgPointsAgainst = standings.reduce((sum, team) => sum + (team.points_against || 0), 0) / totalManagers;
    
    // Find highest/lowest performers
    const topScorer = standings.reduce((max, team) => 
      (team.points_for || 0) > (max.points_for || 0) ? team : max, standings[0]);
    const bottomScorer = standings.reduce((min, team) => 
      (team.points_for || 0) < (min.points_for || 0) ? team : min, standings[0]);
    
    // Most/least wins
    const mostWins = standings.reduce((max, team) => 
      (team.matches_won || 0) > (max.matches_won || 0) ? team : max, standings[0]);
    const leastWins = standings.reduce((min, team) => 
      (team.matches_won || 0) < (min.matches_won || 0) ? team : min, standings[0]);

    // Form analysis (wins vs total)
    const inForm = standings.filter(team => 
      (team.matches_played || 0) > 0 && 
      ((team.matches_won || 0) / (team.matches_played || 1)) > 0.6
    ).length;

    const outOfForm = standings.filter(team => 
      (team.matches_played || 0) > 0 && 
      ((team.matches_won || 0) / (team.matches_played || 1)) < 0.3
    ).length;

    setAnalytics({
      totalManagers,
      totalMatches,
      avgPointsFor: Math.round(avgPointsFor),
      avgPointsAgainst: Math.round(avgPointsAgainst),
      topScorer,
      bottomScorer,
      mostWins,
      leastWins,
      inForm,
      outOfForm
    });
  };

  const handleGenerateReport = async () => {
    if (!selectedManagers.manager1 || !selectedManagers.manager2) {
      alert('Please select both managers for the report');
      return;
    }

    try {
      setGeneratingReport(true);
      
      const response = await fetch(`http://localhost:8000/api/report/generate/h2h/${selectedManagers.manager1}/${selectedManagers.manager2}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          league_id: leagueId,
          format: 'pdf'
        })
      });

      if (!response.ok) {
        throw new Error('Failed to generate report');
      }

      const result = await response.json();
      
      // Download the generated report
      if (result.pdf_path) {
        const downloadResponse = await fetch(`http://localhost:8000/api/report/download/${result.pdf_path}`);
        if (downloadResponse.ok) {
          const blob = await downloadResponse.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `H2H_Report_${selectedManagers.manager1}_vs_${selectedManagers.manager2}.pdf`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
        }
      }

      setReportDialog(false);
      setSelectedManagers({ manager1: '', manager2: '' });
      
    } catch (err) {
      console.error('Error generating report:', err);
      alert('Failed to generate report');
    } finally {
      setGeneratingReport(false);
    }
  };

  const StatCard = ({ title, value, subtitle, icon, color = 'primary' }) => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography variant="h4" color={color} gutterBottom>
              {value}
            </Typography>
            <Typography variant="h6" gutterBottom>
              {title}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box color={`${color}.main`}>
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading analytics...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        Error loading analytics: {error}
      </Alert>
    );
  }

  if (!analytics) {
    return (
      <Alert severity="info" sx={{ mt: 2 }}>
        No analytics data available
      </Alert>
    );
  }

  const standings = leagueData?.standings?.standings?.results || [];

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">League Analytics</Typography>
        <Button
          variant="outlined"
          startIcon={<Download />}
          onClick={() => setReportDialog(true)}
        >
          Generate H2H Report
        </Button>
      </Box>

      {/* Overview Stats */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Managers"
            value={analytics.totalManagers}
            icon={<EmojiEvents size={40} />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Matches Played"
            value={analytics.totalMatches}
            icon={<Timeline size={40} />}
            color="secondary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Avg Points For"
            value={analytics.avgPointsFor}
            subtitle="Per manager"
            icon={<TrendingUp size={40} />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Avg Points Against"
            value={analytics.avgPointsAgainst}
            subtitle="Per manager"
            icon={<TrendingDown size={40} />}
            color="warning"
          />
        </Grid>
      </Grid>

      {/* Performance Analysis */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              <Assessment sx={{ mr: 1, verticalAlign: 'middle' }} />
              Top Performers
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Box mb={2}>
              <Typography variant="subtitle2" color="primary" gutterBottom>
                Highest Scorer
              </Typography>
              <Typography variant="body1">
                <strong>{analytics.topScorer.player_name || `Manager ${analytics.topScorer.entry}`}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {analytics.topScorer.points_for} points for • {analytics.topScorer.entry_name}
              </Typography>
            </Box>

            <Box mb={2}>
              <Typography variant="subtitle2" color="primary" gutterBottom>
                Most Wins
              </Typography>
              <Typography variant="body1">
                <strong>{analytics.mostWins.player_name || `Manager ${analytics.mostWins.entry}`}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {analytics.mostWins.matches_won} wins • {analytics.mostWins.entry_name}
              </Typography>
            </Box>

            <Box>
              <Typography variant="subtitle2" color="success.main" gutterBottom>
                In Form Teams
              </Typography>
              <Chip 
                label={`${analytics.inForm} teams with 60%+ win rate`} 
                color="success" 
                variant="outlined" 
              />
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              <TrendingDown sx={{ mr: 1, verticalAlign: 'middle' }} />
              Struggling Teams
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Box mb={2}>
              <Typography variant="subtitle2" color="error" gutterBottom>
                Lowest Scorer
              </Typography>
              <Typography variant="body1">
                <strong>{analytics.bottomScorer.player_name || `Manager ${analytics.bottomScorer.entry}`}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {analytics.bottomScorer.points_for} points for • {analytics.bottomScorer.entry_name}
              </Typography>
            </Box>

            <Box mb={2}>
              <Typography variant="subtitle2" color="error" gutterBottom>
                Fewest Wins
              </Typography>
              <Typography variant="body1">
                <strong>{analytics.leastWins.player_name || `Manager ${analytics.leastWins.entry}`}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {analytics.leastWins.matches_won} wins • {analytics.leastWins.entry_name}
              </Typography>
            </Box>

            <Box>
              <Typography variant="subtitle2" color="warning.main" gutterBottom>
                Out of Form Teams
              </Typography>
              <Chip 
                label={`${analytics.outOfForm} teams with <30% win rate`} 
                color="warning" 
                variant="outlined" 
              />
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Report Generation Dialog */}
      <Dialog open={reportDialog} onClose={() => setReportDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Generate H2H Report</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Generate a detailed head-to-head analysis report between two managers.
          </Typography>
          
          <FormControl fullWidth margin="normal">
            <InputLabel>Manager 1</InputLabel>
            <Select
              value={selectedManagers.manager1}
              onChange={(e) => setSelectedManagers(prev => ({ ...prev, manager1: e.target.value }))}
            >
              {standings.map((manager) => (
                <MenuItem key={manager.entry} value={manager.entry}>
                  {manager.player_name || `Manager ${manager.entry}`} - {manager.entry_name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl fullWidth margin="normal">
            <InputLabel>Manager 2</InputLabel>
            <Select
              value={selectedManagers.manager2}
              onChange={(e) => setSelectedManagers(prev => ({ ...prev, manager2: e.target.value }))}
            >
              {standings.map((manager) => (
                <MenuItem key={manager.entry} value={manager.entry}>
                  {manager.player_name || `Manager ${manager.entry}`} - {manager.entry_name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReportDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleGenerateReport} 
            variant="contained"
            disabled={generatingReport || !selectedManagers.manager1 || !selectedManagers.manager2}
          >
            {generatingReport ? <CircularProgress size={20} /> : 'Generate Report'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Analytics;