import { useEffect, useRef, useCallback, useState } from 'react';

export const useWorker = () => {
  const workerRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    // Create worker
    workerRef.current = new Worker(
      new URL('../workers/calculations.worker.js', import.meta.url),
      { type: 'module' }
    );
    
    // Cleanup
    return () => {
      if (workerRef.current) {
        workerRef.current.terminate();
      }
    };
  }, []);
  
  const calculate = useCallback((type, data) => {
    return new Promise((resolve, reject) => {
      if (!workerRef.current) {
        reject(new Error('Worker not initialized'));
        return;
      }
      
      setLoading(true);
      setError(null);
      
      const handleMessage = (event) => {
        const { type: responseType, data: responseData, error: responseError } = event.data;
        
        if (responseType === 'SUCCESS') {
          setLoading(false);
          resolve(responseData);
        } else if (responseType === 'ERROR') {
          setLoading(false);
          setError(responseError);
          reject(new Error(responseError));
        }
        
        // Remove listener after handling
        workerRef.current.removeEventListener('message', handleMessage);
      };
      
      workerRef.current.addEventListener('message', handleMessage);
      workerRef.current.postMessage({ type, data });
    });
  }, []);
  
  const calculateExpectedPoints = useCallback((players, fixtures) => {
    return calculate('CALCULATE_EXPECTED_POINTS', { players, fixtures });
  }, [calculate]);
  
  const calculateTeamStats = useCallback((teamData, allPlayers) => {
    return calculate('CALCULATE_TEAM_STATS', { teamData, allPlayers });
  }, [calculate]);
  
  const calculateDifferentials = useCallback((team1, team2, allPlayers) => {
    return calculate('CALCULATE_DIFFERENTIALS', { team1, team2, allPlayers });
  }, [calculate]);
  
  const simulateMatch = useCallback((team1, team2, iterations = 1000) => {
    return calculate('SIMULATE_MATCH', { team1, team2, iterations });
  }, [calculate]);
  
  return {
    loading,
    error,
    calculateExpectedPoints,
    calculateTeamStats,
    calculateDifferentials,
    simulateMatch
  };
};