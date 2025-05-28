// Web Worker for heavy FPL calculations

// Calculate expected points based on fixtures and form
const calculateExpectedPoints = (players, fixtures) => {
  const expectedPoints = {};
  
  players.forEach(player => {
    let totalExpected = 0;
    const relevantFixtures = fixtures.filter(f => 
      f.team_h === player.team || f.team_a === player.team
    );
    
    relevantFixtures.forEach(fixture => {
      const isHome = fixture.team_h === player.team;
      const difficulty = isHome ? fixture.team_h_difficulty : fixture.team_a_difficulty;
      
      // Complex calculation based on form, difficulty, and position
      const formFactor = player.form ? parseFloat(player.form) : 0;
      const difficultyFactor = (6 - difficulty) / 5;
      const positionMultiplier = {
        1: 0.5,  // GK
        2: 0.7,  // DEF
        3: 1.0,  // MID
        4: 1.2   // FWD
      }[player.element_type] || 1;
      
      const expectedForFixture = 
        (formFactor * difficultyFactor * positionMultiplier * 2) + 2;
      
      totalExpected += expectedForFixture;
    });
    
    expectedPoints[player.id] = totalExpected / relevantFixtures.length || 0;
  });
  
  return expectedPoints;
};

// Calculate team statistics
const calculateTeamStats = (teamData, allPlayers) => {
  const stats = {
    totalValue: 0,
    totalPoints: 0,
    averagePoints: 0,
    positionBreakdown: { GK: 0, DEF: 0, MID: 0, FWD: 0 },
    topPerformers: [],
    underperformers: [],
    injuredPlayers: [],
    ownership: {}
  };
  
  teamData.picks.forEach(pick => {
    const player = allPlayers.find(p => p.id === pick.element);
    if (!player) return;
    
    stats.totalValue += player.now_cost;
    stats.totalPoints += player.total_points;
    
    // Position breakdown
    const position = ['GK', 'DEF', 'MID', 'FWD'][player.element_type - 1];
    stats.positionBreakdown[position]++;
    
    // Performance analysis
    const pointsPerMillion = player.total_points / (player.now_cost / 10);
    if (pointsPerMillion > 6) {
      stats.topPerformers.push({
        id: player.id,
        name: player.web_name,
        points: player.total_points,
        value: player.now_cost,
        pointsPerMillion
      });
    } else if (pointsPerMillion < 3) {
      stats.underperformers.push({
        id: player.id,
        name: player.web_name,
        points: player.total_points,
        value: player.now_cost,
        pointsPerMillion
      });
    }
    
    // Injury status
    if (player.chance_of_playing_next_round !== null && 
        player.chance_of_playing_next_round < 100) {
      stats.injuredPlayers.push({
        id: player.id,
        name: player.web_name,
        chance: player.chance_of_playing_next_round
      });
    }
    
    // Ownership
    stats.ownership[player.id] = player.selected_by_percent;
  });
  
  stats.averagePoints = stats.totalPoints / teamData.picks.length;
  stats.topPerformers.sort((a, b) => b.pointsPerMillion - a.pointsPerMillion);
  stats.underperformers.sort((a, b) => a.pointsPerMillion - b.pointsPerMillion);
  
  return stats;
};

// Calculate differential opportunities
const calculateDifferentials = (team1, team2, allPlayers) => {
  const team1Ids = new Set(team1.picks.map(p => p.element));
  const team2Ids = new Set(team2.picks.map(p => p.element));
  
  const differentials = {
    team1Unique: [],
    team2Unique: [],
    captainDifferential: null,
    viceCaptainDifferential: null
  };
  
  // Find unique players
  team1Ids.forEach(id => {
    if (!team2Ids.has(id)) {
      const player = allPlayers.find(p => p.id === id);
      if (player) {
        differentials.team1Unique.push({
          id: player.id,
          name: player.web_name,
          points: player.total_points,
          form: player.form
        });
      }
    }
  });
  
  team2Ids.forEach(id => {
    if (!team1Ids.has(id)) {
      const player = allPlayers.find(p => p.id === id);
      if (player) {
        differentials.team2Unique.push({
          id: player.id,
          name: player.web_name,
          points: player.total_points,
          form: player.form
        });
      }
    }
  });
  
  // Captain differentials
  const team1Captain = team1.picks.find(p => p.is_captain)?.element;
  const team2Captain = team2.picks.find(p => p.is_captain)?.element;
  
  if (team1Captain !== team2Captain) {
    differentials.captainDifferential = {
      team1: allPlayers.find(p => p.id === team1Captain),
      team2: allPlayers.find(p => p.id === team2Captain)
    };
  }
  
  return differentials;
};

// Monte Carlo simulation for match outcome
const simulateMatchOutcome = (team1Data, team2Data, iterations = 1000) => {
  const results = { team1Wins: 0, team2Wins: 0, draws: 0 };
  
  for (let i = 0; i < iterations; i++) {
    let team1Score = 0;
    let team2Score = 0;
    
    // Simulate each player's performance
    team1Data.picks.forEach(pick => {
      const expectedPoints = pick.expectedPoints || 4;
      const variance = expectedPoints * 0.5;
      const actualPoints = Math.max(0, expectedPoints + (Math.random() - 0.5) * variance * 2);
      team1Score += pick.is_captain ? actualPoints * 2 : actualPoints;
    });
    
    team2Data.picks.forEach(pick => {
      const expectedPoints = pick.expectedPoints || 4;
      const variance = expectedPoints * 0.5;
      const actualPoints = Math.max(0, expectedPoints + (Math.random() - 0.5) * variance * 2);
      team2Score += pick.is_captain ? actualPoints * 2 : actualPoints;
    });
    
    if (team1Score > team2Score) results.team1Wins++;
    else if (team2Score > team1Score) results.team2Wins++;
    else results.draws++;
  }
  
  return {
    team1WinProbability: (results.team1Wins / iterations) * 100,
    team2WinProbability: (results.team2Wins / iterations) * 100,
    drawProbability: (results.draws / iterations) * 100
  };
};

// Message handler
self.addEventListener('message', async (event) => {
  const { type, data } = event.data;
  
  try {
    let result;
    
    switch (type) {
      case 'CALCULATE_EXPECTED_POINTS':
        result = calculateExpectedPoints(data.players, data.fixtures);
        break;
        
      case 'CALCULATE_TEAM_STATS':
        result = calculateTeamStats(data.teamData, data.allPlayers);
        break;
        
      case 'CALCULATE_DIFFERENTIALS':
        result = calculateDifferentials(data.team1, data.team2, data.allPlayers);
        break;
        
      case 'SIMULATE_MATCH':
        result = simulateMatchOutcome(data.team1, data.team2, data.iterations);
        break;
        
      default:
        throw new Error(`Unknown calculation type: ${type}`);
    }
    
    self.postMessage({ type: 'SUCCESS', data: result });
  } catch (error) {
    self.postMessage({ type: 'ERROR', error: error.message });
  }
});