import React from 'react';
import { 
  Skeleton, 
  Box, 
  Card, 
  CardContent, 
  Stack, 
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper
} from '@mui/material';

// Battle Card Skeleton
export const BattleCardSkeleton = () => (
  <Card sx={{ mb: 2 }}>
    <CardContent>
      <Stack spacing={2}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ flex: 1 }}>
            <Skeleton variant="text" width="60%" height={32} />
            <Skeleton variant="text" width="40%" />
          </Box>
          <Skeleton variant="circular" width={60} height={60} />
          <Box sx={{ flex: 1, textAlign: 'right' }}>
            <Skeleton variant="text" width="60%" sx={{ ml: 'auto' }} height={32} />
            <Skeleton variant="text" width="40%" sx={{ ml: 'auto' }} />
          </Box>
        </Box>
        <Skeleton variant="rectangular" height={40} />
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Skeleton variant="rectangular" height={100} sx={{ flex: 1 }} />
          <Skeleton variant="rectangular" height={100} sx={{ flex: 1 }} />
        </Box>
      </Stack>
    </CardContent>
  </Card>
);

// Manager Card Skeleton
export const ManagerCardSkeleton = () => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Stack spacing={2}>
        <Skeleton variant="text" width="70%" height={32} />
        <Skeleton variant="text" width="50%" />
        <Box sx={{ pt: 2 }}>
          <Skeleton variant="rectangular" height={60} />
        </Box>
        <Stack direction="row" spacing={2}>
          <Skeleton variant="rectangular" width={100} height={40} />
          <Skeleton variant="rectangular" width={100} height={40} />
        </Stack>
      </Stack>
    </CardContent>
  </Card>
);

// League Table Skeleton
export const LeagueTableSkeleton = () => (
  <TableContainer component={Paper}>
    <Table>
      <TableHead>
        <TableRow>
          {[1, 2, 3, 4, 5, 6].map((col) => (
            <TableCell key={col}>
              <Skeleton variant="text" />
            </TableCell>
          ))}
        </TableRow>
      </TableHead>
      <TableBody>
        {[...Array(10)].map((_, index) => (
          <TableRow key={index}>
            {[1, 2, 3, 4, 5, 6].map((col) => (
              <TableCell key={col}>
                <Skeleton variant="text" />
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </TableContainer>
);

// Chart Skeleton (already defined in LazyChart.jsx)
export const ChartSkeleton = ({ width = '100%', height = 300 }) => (
  <Skeleton 
    variant="rectangular" 
    width={width} 
    height={height} 
    animation="wave"
    sx={{ borderRadius: 1 }}
  />
);

// H2H Comparison Skeleton
export const H2HComparisonSkeleton = () => (
  <Box>
    <Grid container spacing={3}>
      {/* Manager selection */}
      <Grid item xs={12}>
        <Paper sx={{ p: 3 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={5}>
              <Skeleton variant="rectangular" height={56} />
            </Grid>
            <Grid item xs={12} md={2} sx={{ textAlign: 'center' }}>
              <Skeleton variant="text" width="60%" sx={{ mx: 'auto' }} />
            </Grid>
            <Grid item xs={12} md={5}>
              <Skeleton variant="rectangular" height={56} />
            </Grid>
          </Grid>
        </Paper>
      </Grid>
      
      {/* Score comparison */}
      <Grid item xs={12}>
        <Paper sx={{ p: 3 }}>
          <Grid container spacing={2}>
            <Grid item xs={5}>
              <Skeleton variant="text" width="60%" height={40} sx={{ mx: 'auto' }} />
              <Skeleton variant="text" width="40%" sx={{ mx: 'auto' }} />
              <Skeleton variant="circular" width={120} height={120} sx={{ mx: 'auto', mt: 2 }} />
            </Grid>
            <Grid item xs={2}>
              <Skeleton variant="text" width="80%" height={60} sx={{ mx: 'auto', mt: 5 }} />
            </Grid>
            <Grid item xs={5}>
              <Skeleton variant="text" width="60%" height={40} sx={{ mx: 'auto' }} />
              <Skeleton variant="text" width="40%" sx={{ mx: 'auto' }} />
              <Skeleton variant="circular" width={120} height={120} sx={{ mx: 'auto', mt: 2 }} />
            </Grid>
          </Grid>
        </Paper>
      </Grid>
      
      {/* Squad comparison */}
      <Grid item xs={12}>
        <Paper sx={{ p: 3 }}>
          <Skeleton variant="text" width="30%" height={32} sx={{ mb: 2 }} />
          <Grid container spacing={2}>
            <Grid item xs={6}>
              {[...Array(5)].map((_, i) => (
                <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                  <Skeleton variant="circular" width={40} height={40} />
                  <Skeleton variant="text" width="60%" />
                </Box>
              ))}
            </Grid>
            <Grid item xs={6}>
              {[...Array(5)].map((_, i) => (
                <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                  <Skeleton variant="circular" width={40} height={40} />
                  <Skeleton variant="text" width="60%" />
                </Box>
              ))}
            </Grid>
          </Grid>
        </Paper>
      </Grid>
    </Grid>
  </Box>
);

// Live Battle Skeleton
export const LiveBattleSkeleton = () => (
  <Card>
    <CardContent>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Skeleton variant="rounded" width={80} height={24} />
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Skeleton variant="circular" width={24} height={24} />
          <Skeleton variant="circular" width={24} height={24} />
        </Box>
      </Box>
      
      <Grid container spacing={2} alignItems="center">
        <Grid item xs={5}>
          <Stack alignItems="center" spacing={1}>
            <Skeleton variant="text" width="80%" />
            <Skeleton variant="text" width="60%" />
            <Skeleton variant="text" width={80} height={60} />
            <Skeleton variant="rounded" width={100} height={20} />
          </Stack>
        </Grid>
        <Grid item xs={2}>
          <Skeleton variant="text" width="100%" sx={{ textAlign: 'center' }} />
        </Grid>
        <Grid item xs={5}>
          <Stack alignItems="center" spacing={1}>
            <Skeleton variant="text" width="80%" />
            <Skeleton variant="text" width="60%" />
            <Skeleton variant="text" width={80} height={60} />
            <Skeleton variant="rounded" width={100} height={20} />
          </Stack>
        </Grid>
      </Grid>
    </CardContent>
  </Card>
);

// Analytics Card Skeleton
export const AnalyticsCardSkeleton = () => (
  <Card>
    <CardContent>
      <Stack spacing={2}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Skeleton variant="circular" width={24} height={24} />
          <Skeleton variant="text" width="60%" />
        </Box>
        <Skeleton variant="text" width="30%" height={48} />
        <Skeleton variant="text" width="80%" />
        <Skeleton variant="rectangular" height={200} />
      </Stack>
    </CardContent>
  </Card>
);

// Stats Grid Skeleton
export const StatsGridSkeleton = () => (
  <Grid container spacing={2}>
    {[...Array(4)].map((_, i) => (
      <Grid item xs={12} sm={6} md={3} key={i}>
        <Card>
          <CardContent sx={{ textAlign: 'center' }}>
            <Skeleton variant="text" width="60%" sx={{ mx: 'auto' }} />
            <Skeleton variant="text" width="40%" height={48} sx={{ mx: 'auto' }} />
            <Skeleton variant="text" width="80%" sx={{ mx: 'auto' }} />
          </CardContent>
        </Card>
      </Grid>
    ))}
  </Grid>
);

// Analytics Dashboard Skeleton
export const AnalyticsDashboardSkeleton = () => (
  <Grid container spacing={3}>
    {/* Stat Cards */}
    <Grid item xs={12}>
      <Grid container spacing={2}>
        {[1, 2, 3, 4].map((item) => (
          <Grid item xs={12} sm={6} md={3} key={item}>
            <Card>
              <CardContent>
                <Skeleton variant="text" width="60%" />
                <Skeleton variant="text" width="40%" height={40} />
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Grid>
    
    {/* Charts */}
    <Grid item xs={12} md={6}>
      <Card>
        <CardContent>
          <Skeleton variant="text" width="40%" height={32} sx={{ mb: 2 }} />
          <ChartSkeleton height={300} />
        </CardContent>
      </Card>
    </Grid>
    <Grid item xs={12} md={6}>
      <Card>
        <CardContent>
          <Skeleton variant="text" width="40%" height={32} sx={{ mb: 2 }} />
          <ChartSkeleton height={300} />
        </CardContent>
      </Card>
    </Grid>
    
    {/* Table */}
    <Grid item xs={12}>
      <Card>
        <CardContent>
          <Skeleton variant="text" width="30%" height={32} sx={{ mb: 2 }} />
          <LeagueTableSkeleton />
        </CardContent>
      </Card>
    </Grid>
  </Grid>
);

// Player List Skeleton
export const PlayerListSkeleton = () => (
  <Stack spacing={1}>
    {[...Array(5)].map((_, index) => (
      <Box 
        key={index} 
        sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 2, 
          p: 1,
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 1
        }}
      >
        <Skeleton variant="circular" width={40} height={40} />
        <Box sx={{ flex: 1 }}>
          <Skeleton variant="text" width="60%" />
          <Skeleton variant="text" width="40%" height={16} />
        </Box>
        <Skeleton variant="text" width={60} />
      </Box>
    ))}
  </Stack>
);

// Form Chart Skeleton
export const FormChartSkeleton = () => (
  <Box>
    <Skeleton variant="text" width="30%" height={24} sx={{ mb: 2 }} />
    <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
      {[...Array(5)].map((_, i) => (
        <Skeleton key={i} variant="circular" width={30} height={30} />
      ))}
    </Box>
    <ChartSkeleton height={200} />
  </Box>
);

// Comparison View Skeleton
export const ComparisonViewSkeleton = () => (
  <Grid container spacing={3}>
    <Grid item xs={12} md={5}>
      <ManagerCardSkeleton />
    </Grid>
    <Grid item xs={12} md={2} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Skeleton variant="text" width={60} height={40} />
    </Grid>
    <Grid item xs={12} md={5}>
      <ManagerCardSkeleton />
    </Grid>
    <Grid item xs={12}>
      <Card>
        <CardContent>
          <Skeleton variant="text" width="40%" height={32} sx={{ mb: 2 }} />
          <ChartSkeleton height={400} />
        </CardContent>
      </Card>
    </Grid>
  </Grid>
);

// Generic List Skeleton
export const ListSkeleton = ({ items = 5, showAvatar = false }) => (
  <Stack spacing={2}>
    {[...Array(items)].map((_, index) => (
      <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        {showAvatar && <Skeleton variant="circular" width={40} height={40} />}
        <Box sx={{ flex: 1 }}>
          <Skeleton variant="text" width="80%" />
          <Skeleton variant="text" width="60%" height={16} />
        </Box>
      </Box>
    ))}
  </Stack>
);

// Tab Panel Skeleton
export const TabPanelSkeleton = () => (
  <Box sx={{ p: 3 }}>
    <Skeleton variant="text" width="40%" height={32} sx={{ mb: 3 }} />
    <Stack spacing={3}>
      <Skeleton variant="rectangular" height={100} />
      <Skeleton variant="rectangular" height={200} />
      <Grid container spacing={2}>
        <Grid item xs={6}>
          <Skeleton variant="rectangular" height={150} />
        </Grid>
        <Grid item xs={6}>
          <Skeleton variant="rectangular" height={150} />
        </Grid>
      </Grid>
    </Stack>
  </Box>
);

// Page Skeleton for lazy loading
export const PageSkeleton = () => (
  <Box sx={{ p: 3 }}>
    <Skeleton variant="text" width="40%" height={40} sx={{ mb: 3 }} />
    <Stack spacing={3}>
      <Skeleton variant="rectangular" height={100} />
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Skeleton variant="rectangular" height={300} />
        </Grid>
        <Grid item xs={12} md={6}>
          <Skeleton variant="rectangular" height={300} />
        </Grid>
      </Grid>
      <Skeleton variant="rectangular" height={200} />
    </Stack>
  </Box>
);

export default {
  BattleCardSkeleton,
  ManagerCardSkeleton,
  LeagueTableSkeleton,
  ChartSkeleton,
  AnalyticsDashboardSkeleton,
  PlayerListSkeleton,
  FormChartSkeleton,
  ComparisonViewSkeleton,
  ListSkeleton,
  TabPanelSkeleton,
  StatsGridSkeleton,
  PageSkeleton
};