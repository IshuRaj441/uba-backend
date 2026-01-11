import React, { useState, useEffect } from 'react';
import './App.css';
import { apiService } from './services/api';

function App() {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const data = await apiService.getStatus();
        console.log('Status data:', data); // Debug log
        
        // Handle the response structure from the backend
        const formattedStatus = {
          status: 'operational',
          version: data?.system?.flask_version || '1.0.0',
          environment: data?.system?.environment || 'development',
          lastUpdated: data?.system?.last_updated || new Date().toISOString()
        };
        
        setStatus(formattedStatus);
        setError(null);
      } catch (err) {
        console.error('Error fetching status:', err);
        // Set default values when the API call fails
        setStatus({
          status: 'degraded',
          version: 'unknown',
          environment: 'unknown',
          lastUpdated: new Date().toISOString()
        });
        setError('Unable to connect to the backend server. Some features may be limited.');
      } finally {
        setIsLoading(false);
      }
    };

    checkStatus();
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Universal Business Automator</h1>
        
        {isLoading ? (
          <div className="status">
            <div className="loading"></div>
            <p>Loading application status...</p>
          </div>
        ) : error ? (
          <div className="error">
            <h3>⚠️ Connection Issue</h3>
            <p>{error}</p>
            <p>Please verify that the backend server is running at <code>http://localhost:5000</code></p>
            <div className="status">
              <h4>Current System Status</h4>
              <p>Status: <span className="status-value">{status?.status || 'Unknown'}</span></p>
              <p>Version: <span className="status-value">{status?.version || 'N/A'}</span></p>
              <p>Environment: <span className="status-value">{status?.environment || 'N/A'}</span></p>
              {status?.lastUpdated && (
                <p className="last-updated">Last updated: {new Date(status.lastUpdated).toLocaleString()}</p>
              )}
            </div>
          </div>
        ) : (
          <div className="status">
            <h2>System Status</h2>
            <p>Status: <span className="status-value">{status?.status || 'Unknown'}</span></p>
            <p>Version: <span className="status-value">{status?.version || 'N/A'}</span></p>
            <p>Environment: <span className="status-value">{status?.environment || 'N/A'}</span></p>
            {status?.lastUpdated && (
              <p className="last-updated">Last updated: {new Date(status.lastUpdated).toLocaleString()}</p>
            )}
            <div className="system-info">
              <h3>Backend Information</h3>
              <p>The system is running in <strong>{status?.environment || 'development'}</strong> mode.</p>
              {status?.environment === 'development' && (
                <p className="note">ℹ️ Development mode may have reduced performance and additional logging enabled.</p>
              )}
            </div>
          </div>
        )}

        <div className="app-actions">
          <button className="btn primary">Get Started</button>
          <button className="btn secondary">View Documentation</button>
        </div>
      </header>
    </div>
  );
}

export default App;
