// Minimal test app to debug black screen
import React from 'react';

console.log('🔥 Simple Test App Loading...');

function App() {
  console.log('🎯 App component rendering...');
  
  return (
    <div style={{ 
      background: 'white', 
      color: 'black', 
      padding: '20px',
      minHeight: '100vh',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h1>🚀 FPL H2H Analyzer - Debug Test</h1>
      <p>✅ React is working!</p>
      <p>✅ App is mounting!</p>
      <p>🔍 If you can see this, the black screen issue is fixed.</p>
      
      <div style={{ marginTop: '20px', padding: '10px', border: '1px solid #ccc' }}>
        <h3>Debug Info:</h3>
        <ul>
          <li>URL: {window.location.href}</li>
          <li>API Base: {import.meta.env.VITE_API_URL || '/api'}</li>
          <li>Timestamp: {new Date().toISOString()}</li>
        </ul>
      </div>
    </div>
  );
}

export default App;