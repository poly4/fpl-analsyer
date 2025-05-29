import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Slider,
  Button,
  Switch,
  FormControlLabel,
  Chip,
  Paper,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  useTheme,
  alpha
} from '@mui/material';
import {
  Casino,
  TrendingUp,
  TrendingDown,
  PlayArrow,
  Refresh,
  ExpandMore,
  ShowChart,
  Psychology,
  EmojiEvents,
  Warning,
  Lightbulb,
  Speed,
  Timeline,
  Tune,
  AutoFixHigh,
  ThreeDRotation
} from '@mui/icons-material';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import * as THREE from 'three';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Text3D, Center } from '@react-three/drei';

const ProbabilityVisualization3D = ({ predictions, scenarios }) => {
  const meshRef = useRef();
  const { camera } = useThree();
  
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.1;
    }
  });
  
  const probabilityData = useMemo(() => {
    const data = [];
    const manager1WinProb = predictions?.manager1_win_prob || 0.5;
    const manager2WinProb = predictions?.manager2_win_prob || 0.3;
    const drawProb = predictions?.draw_prob || 0.2;
    
    // Create 3D probability space
    for (let i = 0; i < 20; i++) {
      for (let j = 0; j < 20; j++) {
        const x = (i - 10) * 0.5;
        const z = (j - 10) * 0.5;
        const y = Math.sin(x * 0.5) * Math.cos(z * 0.5) * manager1WinProb * 5;
        
        data.push({
          position: [x, y, z],
          color: y > 0 ? 'hotpink' : 'lightblue',
          scale: Math.abs(y) + 0.1
        });
      }
    }
    
    return data;
  }, [predictions]);
  
  return (
    <group ref={meshRef}>
      {probabilityData.map((point, index) => (
        <mesh key={index} position={point.position} scale={point.scale}>
          <sphereGeometry args={[0.05, 8, 8]} />
          <meshStandardMaterial color={point.color} />
        </mesh>
      ))}
      
      <Center>
        {/* Temporarily disable Text3D which requires font loading */}
        <mesh position={[0, 2, 0]}>
          <boxGeometry args={[3, 0.5, 1]} />
          <meshStandardMaterial color="white" />
        </mesh>
      </Center>
    </group>
  );
};

const MonteCarloAnimation = ({ isRunning, currentRun, totalRuns }) => {
  const theme = useTheme();
  
  return (
    <Box
      sx={{
        position: 'relative',
        height: 200,
        bgcolor: alpha(theme.palette.primary.main, 0.1),
        borderRadius: 2,
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}
    >
      <AnimatePresence>
        {isRunning && (
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            style={{
              position: 'absolute',
              width: '100%',
              height: '100%',
              background: `linear-gradient(45deg, ${theme.palette.primary.main}20, ${theme.palette.secondary.main}20)`
            }}
          >
            <Box
              sx={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                textAlign: 'center'
              }}
            >
              <CircularProgress size={60} />
              <Typography variant="h6" sx={{ mt: 2 }}>
                Simulation {currentRun} / {totalRuns}
              </Typography>
            </Box>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Floating particles */}
      {Array.from({ length: 20 }).map((_, i) => (
        <motion.div
          key={i}
          initial={{ x: -100, y: Math.random() * 200, opacity: 0 }}
          animate={{
            x: 300,
            y: Math.random() * 200,
            opacity: [0, 1, 0],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            delay: i * 0.2,
            ease: "linear"
          }}
          style={{
            position: 'absolute',
            width: 4,
            height: 4,
            backgroundColor: theme.palette.primary.main,
            borderRadius: '50%'
          }}
        />
      ))}
    </Box>
  );
};

const ScenarioSlider = ({ scenario, value, onChange, disabled }) => {
  const theme = useTheme();
  
  return (
    <Paper elevation={2} sx={{ p: 3, mb: 2 }}>
      <Typography variant="h6" gutterBottom>
        {scenario.title}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {scenario.description}
      </Typography>
      
      <Box sx={{ px: 2 }}>
        <Slider
          value={value}
          onChange={onChange}
          min={scenario.min}
          max={scenario.max}
          step={scenario.step}
          disabled={disabled}
          valueLabelDisplay="auto"
          valueLabelFormat={(val) => `${val}${scenario.unit}`}
          sx={{
            '& .MuiSlider-thumb': {
              bgcolor: theme.palette.primary.main,
            },
            '& .MuiSlider-track': {
              bgcolor: theme.palette.primary.main,
            }
          }}
        />
      </Box>
      
      <Box display="flex" justifyContent="space-between" sx={{ mt: 1 }}>
        <Typography variant="caption">
          {scenario.min}{scenario.unit}
        </Typography>
        <Typography variant="caption">
          Current: {value}{scenario.unit}
        </Typography>
        <Typography variant="caption">
          {scenario.max}{scenario.unit}
        </Typography>
      </Box>
    </Paper>
  );
};

const PredictionCard = ({ prediction, title, color }) => {
  const theme = useTheme();
  
  return (
    <motion.div
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <Card
        elevation={4}
        sx={{
          background: `linear-gradient(135deg, ${color}20 0%, ${color}10 100%)`,
          border: `1px solid ${color}40`,
          height: '100%'
        }}
      >
        <CardContent>
          <Typography variant="h6" gutterBottom color={color}>
            {title}
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography variant="h4" fontWeight="bold">
                {prediction?.manager1_expected?.toFixed(1) || '0.0'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {prediction?.manager1_name || 'Manager 1'}
              </Typography>
            </Grid>
            
            <Grid item xs={6}>
              <Typography variant="h4" fontWeight="bold">
                {prediction?.manager2_expected?.toFixed(1) || '0.0'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {prediction?.manager2_name || 'Manager 2'}
              </Typography>
            </Grid>
          </Grid>
          
          <Divider sx={{ my: 2 }} />
          
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Chip
              label={`${((prediction?.manager1_win_prob || 0) * 100).toFixed(0)}%`}
              size="small"
              color="primary"
              variant="outlined"
            />
            <Typography variant="body2" color="text.secondary">
              Win Probability
            </Typography>
            <Chip
              label={`${((prediction?.manager2_win_prob || 0) * 100).toFixed(0)}%`}
              size="small"
              color="secondary"
              variant="outlined"
            />
          </Box>
          
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Confidence: {((prediction?.confidence || 0) * 100).toFixed(0)}%
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </motion.div>
  );
};

const StrategicRecommendations = ({ recommendations, onApplyRecommendation }) => {
  const getPriorityColor = (priority) => {
    const colors = {
      critical: 'error',
      high: 'warning',
      medium: 'info',
      low: 'default'
    };
    return colors[priority] || 'default';
  };
  
  const getRecommendationIcon = (type) => {
    const icons = {
      captain: <EmojiEvents />,
      transfer: <TrendingUp />,
      chip: <AutoFixHigh />,
      formation: <Tune />,
      differential: <Psychology />
    };
    return icons[type] || <Lightbulb />;
  };
  
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Strategic Recommendations
      </Typography>
      
      {recommendations.length === 0 ? (
        <Alert severity="info">
          No specific recommendations at this time. Your team looks well-balanced!
        </Alert>
      ) : (
        recommendations.map((rec, index) => (
          <Accordion key={index}>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Box display="flex" alignItems="center" sx={{ width: '100%' }}>
                <Box sx={{ mr: 2 }}>
                  {getRecommendationIcon(rec.type)}
                </Box>
                <Box flex={1}>
                  <Typography variant="subtitle1">
                    {rec.title}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Expected impact: +{rec.expected_impact.toFixed(1)} points
                  </Typography>
                </Box>
                <Chip
                  label={rec.priority}
                  color={getPriorityColor(rec.priority)}
                  size="small"
                />
              </Box>
            </AccordionSummary>
            
            <AccordionDetails>
              <Typography variant="body2" paragraph>
                {rec.description}
              </Typography>
              
              {rec.reasoning && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Reasoning:
                  </Typography>
                  <List dense>
                    {rec.reasoning.map((reason, idx) => (
                      <ListItem key={idx} sx={{ py: 0.5 }}>
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          <Lightbulb fontSize="small" />
                        </ListItemIcon>
                        <ListItemText primary={reason} />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
              
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="caption" color="text.secondary">
                  Confidence: {(rec.confidence * 100).toFixed(0)}% | Timeframe: {rec.timeframe}
                </Typography>
                
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => onApplyRecommendation(rec)}
                  startIcon={<PlayArrow />}
                >
                  Apply
                </Button>
              </Box>
            </AccordionDetails>
          </Accordion>
        ))
      )}
    </Box>
  );
};

export default function PredictiveSimulator({ manager1Id, manager2Id, gameweek }) {
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [isSimulating, setIsSimulating] = useState(false);
  const [currentRun, setCurrentRun] = useState(0);
  const [predictions, setPredictions] = useState(null);
  const [livePredictions, setLivePredictions] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [scenarioValues, setScenarioValues] = useState({});
  const [realTimeMode, setRealTimeMode] = useState(false);
  const [mlEnabled, setMlEnabled] = useState(true);
  
  const scenarioTemplates = [
    {
      id: 'captain_multiplier',
      title: 'Captain Performance',
      description: 'Adjust your captain\'s expected performance',
      min: 0,
      max: 30,
      step: 1,
      unit: ' pts',
      default: 12
    },
    {
      id: 'differential_impact',
      title: 'Differential Player Impact',
      description: 'Simulate differential players having exceptional games',
      min: 0,
      max: 25,
      step: 1,
      unit: ' pts',
      default: 8
    },
    {
      id: 'red_card_probability',
      title: 'Red Card Risk',
      description: 'Probability of key players getting red cards',
      min: 0,
      max: 20,
      step: 1,
      unit: '%',
      default: 2
    },
    {
      id: 'bonus_volatility',
      title: 'Bonus Point Volatility',
      description: 'How much bonus points deviate from predictions',
      min: 0,
      max: 10,
      step: 0.5,
      unit: ' pts',
      default: 3
    }
  ];
  
  useEffect(() => {
    // Initialize scenario values
    const initialValues = {};
    scenarioTemplates.forEach(scenario => {
      initialValues[scenario.id] = scenario.default;
    });
    setScenarioValues(initialValues);
  }, []);
  
  useEffect(() => {
    if (manager1Id && manager2Id && gameweek) {
      runPrediction();
      if (realTimeMode) {
        const interval = setInterval(runLivePrediction, 30000); // Every 30 seconds
        return () => clearInterval(interval);
      }
    }
  }, [manager1Id, manager2Id, gameweek, realTimeMode]);
  
  const runPrediction = async () => {
    setIsSimulating(true);
    
    try {
      // Simulate Monte Carlo with progress
      const totalRuns = 1000;
      for (let i = 0; i <= totalRuns; i += 50) {
        setCurrentRun(i);
        await new Promise(resolve => setTimeout(resolve, 50));
      }
      
      // Get prediction from API
      const response = await fetch(
        `/api/simulator/predict/${manager1Id}/${manager2Id}/${gameweek}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ml_enabled: mlEnabled,
            scenario_adjustments: scenarioValues
          })
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setPredictions(data.prediction);
        setScenarios(data.scenarios || []);
      }
      
      // Get strategic recommendations
      const recResponse = await fetch(
        `/api/strategy/recommendations/${manager1Id}/${manager2Id}/${gameweek}`
      );
      
      if (recResponse.ok) {
        const recData = await recResponse.json();
        setRecommendations(recData.recommendations || []);
      }
      
    } catch (error) {
      console.error('Error running prediction:', error);
    } finally {
      setIsSimulating(false);
      setCurrentRun(0);
    }
  };
  
  const runLivePrediction = async () => {
    try {
      const response = await fetch(
        `/api/simulator/live-predict/${manager1Id}/${manager2Id}/${gameweek}`
      );
      
      if (response.ok) {
        const data = await response.json();
        setLivePredictions(data.prediction);
      }
    } catch (error) {
      console.error('Error running live prediction:', error);
    }
  };
  
  const runScenarioAnalysis = async () => {
    setIsSimulating(true);
    
    try {
      const response = await fetch(
        `/api/simulator/scenarios/${manager1Id}/${manager2Id}/${gameweek}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            scenarios: Object.keys(scenarioValues).map(key => `${key}: ${scenarioValues[key]}`)
          })
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setScenarios(data.scenarios || []);
      }
    } catch (error) {
      console.error('Error running scenario analysis:', error);
    } finally {
      setIsSimulating(false);
    }
  };
  
  const handleScenarioChange = (scenarioId, value) => {
    setScenarioValues(prev => ({
      ...prev,
      [scenarioId]: value
    }));
  };
  
  const handleApplyRecommendation = (recommendation) => {
    // In a real app, this would apply the recommendation
    console.log('Applying recommendation:', recommendation);
  };
  
  const probabilityData = useMemo(() => {
    if (!predictions) return [];
    
    return [
      {
        name: predictions.manager1_name,
        probability: predictions.manager1_win_prob * 100,
        color: theme.palette.primary.main
      },
      {
        name: 'Draw',
        probability: predictions.draw_prob * 100,
        color: theme.palette.warning.main
      },
      {
        name: predictions.manager2_name,
        probability: predictions.manager2_win_prob * 100,
        color: theme.palette.secondary.main
      }
    ];
  }, [predictions, theme]);
  
  const scenarioComparisonData = useMemo(() => {
    return scenarios.map(scenario => ({
      name: scenario.scenario_name,
      manager1: scenario.manager1_points,
      manager2: scenario.manager2_points,
      probability: scenario.probability * 100
    }));
  }, [scenarios]);
  
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight="bold">
          Predictive Match Simulator
        </Typography>
        
        <Box display="flex" gap={2} alignItems="center">
          <FormControlLabel
            control={
              <Switch
                checked={realTimeMode}
                onChange={(e) => setRealTimeMode(e.target.checked)}
              />
            }
            label="Real-time Mode"
          />
          
          <FormControlLabel
            control={
              <Switch
                checked={mlEnabled}
                onChange={(e) => setMlEnabled(e.target.checked)}
              />
            }
            label="ML Enhanced"
          />
          
          <Button
            variant="contained"
            onClick={runPrediction}
            disabled={isSimulating}
            startIcon={isSimulating ? <CircularProgress size={20} /> : <PlayArrow />}
          >
            {isSimulating ? 'Simulating...' : 'Run Simulation'}
          </Button>
        </Box>
      </Box>
      
      <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
        <Tab icon={<ShowChart />} label="Predictions" />
        <Tab icon={<Casino />} label="What-If Scenarios" />
        <Tab icon={<Psychology />} label="Strategic Advice" />
        <Tab icon={<ThreeDRotation />} label="3D Visualization" />
      </Tabs>
      
      {/* Predictions Tab */}
      {tabValue === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <PredictionCard
              prediction={predictions}
              title="Pre-Match Prediction"
              color={theme.palette.primary.main}
            />
          </Grid>
          
          {realTimeMode && livePredictions && (
            <Grid item xs={12} md={6}>
              <PredictionCard
                prediction={livePredictions}
                title="Live Adjusted Prediction"
                color={theme.palette.success.main}
              />
            </Grid>
          )}
          
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Win Probability Distribution
                </Typography>
                
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={probabilityData}
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="probability"
                      label={({name, probability}) => `${name}: ${probability.toFixed(1)}%`}
                    >
                      {probabilityData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <RechartsTooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
          
          {predictions?.key_differentials && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Key Differentials
                  </Typography>
                  
                  <List>
                    {predictions.key_differentials.map((diff, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <TrendingUp color={diff.team === 'team1' ? 'primary' : 'secondary'} />
                        </ListItemIcon>
                        <ListItemText
                          primary={diff.player_name}
                          secondary={`Expected: ${diff.expected_points.toFixed(1)} pts | Ceiling: ${diff.ceiling.toFixed(1)} pts`}
                        />
                        <ListItemSecondaryAction>
                          <Chip
                            label={`${diff.ownership.toFixed(1)}% owned`}
                            size="small"
                            variant="outlined"
                          />
                        </ListItemSecondaryAction>
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      )}
      
      {/* What-If Scenarios Tab */}
      {tabValue === 1 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Typography variant="h6" gutterBottom>
              Scenario Controls
            </Typography>
            
            {scenarioTemplates.map((scenario) => (
              <ScenarioSlider
                key={scenario.id}
                scenario={scenario}
                value={scenarioValues[scenario.id] || scenario.default}
                onChange={(e, value) => handleScenarioChange(scenario.id, value)}
                disabled={isSimulating}
              />
            ))}
            
            <Button
              variant="outlined"
              fullWidth
              onClick={runScenarioAnalysis}
              disabled={isSimulating}
              startIcon={<Casino />}
              sx={{ mt: 2 }}
            >
              Run Scenario Analysis
            </Button>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Monte Carlo Simulation
                </Typography>
                
                <MonteCarloAnimation
                  isRunning={isSimulating}
                  currentRun={currentRun}
                  totalRuns={1000}
                />
              </CardContent>
            </Card>
            
            {scenarioComparisonData.length > 0 && (
              <Card sx={{ mt: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Scenario Comparison
                  </Typography>
                  
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={scenarioComparisonData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <RechartsTooltip />
                      <Bar dataKey="manager1" fill={theme.palette.primary.main} name="Manager 1" />
                      <Bar dataKey="manager2" fill={theme.palette.secondary.main} name="Manager 2" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            )}
          </Grid>
        </Grid>
      )}
      
      {/* Strategic Advice Tab */}
      {tabValue === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <StrategicRecommendations
              recommendations={recommendations}
              onApplyRecommendation={handleApplyRecommendation}
            />
          </Grid>
        </Grid>
      )}
      
      {/* 3D Visualization Tab */}
      {tabValue === 3 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  3D Probability Space
                </Typography>
                
                <Box height={500} sx={{ bgcolor: 'black', borderRadius: 2, position: 'relative' }}>
                  {(() => {
                    try {
                      // Check if WebGL is supported
                      const canvas = document.createElement('canvas');
                      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                      
                      if (!gl) {
                        return (
                          <Box 
                            sx={{ 
                              display: 'flex', 
                              alignItems: 'center', 
                              justifyContent: 'center', 
                              height: '100%',
                              flexDirection: 'column',
                              gap: 2,
                              color: 'white'
                            }}
                          >
                            <Warning sx={{ fontSize: 60 }} />
                            <Typography variant="h6">WebGL Not Supported</Typography>
                            <Typography variant="body2" align="center">
                              Your browser doesn't support 3D visualization.
                              Try using a modern browser like Chrome, Firefox, or Edge.
                            </Typography>
                          </Box>
                        );
                      }
                      
                      return (
                        <React.Suspense 
                          fallback={
                            <Box 
                              sx={{ 
                                display: 'flex', 
                                alignItems: 'center', 
                                justifyContent: 'center', 
                                height: '100%' 
                              }}
                            >
                              <CircularProgress />
                            </Box>
                          }
                        >
                          <Canvas 
                            camera={{ position: [0, 5, 10] }}
                            onCreated={({ gl }) => {
                              gl.setClearColor('#000000');
                            }}
                            onError={(error) => {
                              console.error('Canvas error:', error);
                            }}
                          >
                            <ambientLight intensity={0.5} />
                            <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} />
                            <pointLight position={[-10, -10, -10]} />
                            
                            <ProbabilityVisualization3D
                              predictions={predictions}
                              scenarios={scenarios}
                            />
                            
                            <OrbitControls enablePan={true} enableZoom={true} enableRotate={true} />
                          </Canvas>
                        </React.Suspense>
                      );
                    } catch (error) {
                      console.error('3D Visualization error:', error);
                      return (
                        <Box 
                          sx={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            justifyContent: 'center', 
                            height: '100%',
                            flexDirection: 'column',
                            gap: 2,
                            color: 'white'
                          }}
                        >
                          <Warning sx={{ fontSize: 60 }} />
                          <Typography variant="h6">3D Visualization Error</Typography>
                          <Typography variant="body2" align="center">
                            Unable to load 3D visualization.
                            {error.message && ` Error: ${error.message}`}
                          </Typography>
                        </Box>
                      );
                    }
                  })()}
                </Box>
                
                <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                  Interactive 3D visualization of prediction probability space. Use mouse to rotate and zoom.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
}