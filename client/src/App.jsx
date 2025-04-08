import { useState } from "react";
import './App.css';

function App() {
  const [selectedStates, setSelectedStates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [downloadedFiles, setDownloadedFiles] = useState([]);
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [logs, setLogs] = useState([]);
  const [minPopulation, setMinPopulation] = useState(50000);

  
  const states = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
    "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan",
    "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
    "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia",
    "Wisconsin", "Wyoming"
  ];

  const handleStateChange = (event) => {
    const state = event.target.value;
    setSelectedStates((prevSelectedStates) =>
      prevSelectedStates.includes(state)
        ? prevSelectedStates.filter((item) => item !== state)
        : [...prevSelectedStates, state]
    );
  };

  const handlePopulationChange = (e) => {
    const value = parseInt(e.target.value) || 0;
    setMinPopulation(Math.max(0, value)); // Ensure it doesn't go below 0
  };

  // Filter states based on search term
  const filteredStates = states.filter(state => 
    state.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectAllStates = () => {
    setSelectedStates([...states]);
  };

  const clearAllStates = () => {
    setSelectedStates([]);
  };

  const handleSubmit = async () => {
    if (!apiKey) {
      setError("Please enter your API key");
      return;
    }
  
    setLoading(true);
    setError(null);
    setDownloadedFiles([]);
    setLogs([]);
  
    try {
      // const response = await fetch("http://127.0.0.1:8000/api/scrape", {
      const response = await fetch("/api/scrape", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          states: selectedStates, 
          api_key: apiKey,
          min_population: minPopulation 
        }),
      });
  
      if (!response.ok || !response.body) {
        throw new Error("Failed to connect to server");
      }
  
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      const processStream = async () => {
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
  
            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n\n').filter(line => line.trim() !== '');
  
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = JSON.parse(line.substring(6));
                
                switch (data.type) {
                  case 'log':
                    setLogs(prev => [...prev, data.message]);
                    break;
                  case 'error':
                    setError(data.message);
                    setLoading(false);
                    return;
                  case 'complete':
                    const files = selectedStates.map(state => ({
                      name: `scraped_population_and_job_data_${state.toLowerCase().replace(' ', '_')}.xlsx`,
                      state: state
                    }));
                    setDownloadedFiles(files);
                    setLoading(false);
                    break;
                }
              }
            }
          }
        } catch (error) {
          setError(error.message);
          setLoading(false);
        }
      };
  
      // Don't await this so the UI stays responsive
      processStream();
      
    } catch (error) {
      setError(error.message);
      setLoading(false);
    }
  };

  const getDownloadUrl = async (filename) => {
    try {
      const response = await fetch(`/api/download/${filename}`);
      // const response = await fetch(`http://127.0.0.1:8000/api/download/${filename}`);
      if (!response.ok) {
        throw new Error('Failed to get download URL');
      }
      const data = await response.json();
      return data.url;
    } catch (error) {
      console.error("Error getting download URL:", error);
      return "#";
    }
  };

  return (
    <div className="app-container">
      <div className="app-content">
        <h1 className="app-title">Market Research</h1>

        <div className="content-columns">
          {/* User Input */}
          <div className="user-input-container">
            <div className="container-header">
              <span className="border-title">Input Target Data</span>
            </div>
            
            {/* API Key and Population Input Row */}
            <div className="input-row">
              {/* API Key Input */}
              <div className="api-key-container">
                <h2 className="api-key-input-title">
                  Enter Google Maps API Key: 
                </h2>
                <div className="api-key-input-wrapper">
                  <input
                    type={showApiKey ? "text" : "password"}
                    value={apiKey}
                    onChange={(e) => {
                      setApiKey(e.target.value);
                      setError(null);
                    }}
                    className={`api-key-input`}
                    placeholder="Google Maps API key"
                  />
                  <button 
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="api-key-toggle"
                    type="button"
                    aria-label={showApiKey ? "Hide API key" : "Show API key"}
                  >
                    {showApiKey ? 'HIDE' : 'SHOW'}
                  </button>
                </div>
              </div>

              {/* Population Input */}
              <div className="population-container">
                <h2 className="population-input-title">
                  Minimum Population Count:
                </h2>
                <div className="population-input-wrapper">
                  <input
                    type="number"
                    value={minPopulation}
                    onChange={handlePopulationChange}
                    className="population-input"
                    min="0"
                    step="1000"
                  />
                </div>
              </div>
            </div>
            
            {/* State Selection */}
            <h2 className="state-selection-title">Select States:
                <span className="state-counter">
                  ({selectedStates.length}/{states.length} selected)
                </span>
            </h2>

            <div className="state-search-container">
              <input
                type="text"
                placeholder="Search states..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="state-search-input"
              />
              {searchTerm && (
                <button 
                  onClick={() => setSearchTerm('')} 
                  className="clear-search-button"
                  aria-label="Clear search"
                >
                  ×
                </button>
              )}

              <div className="state-selection-actions">
                <button 
                  onClick={selectAllStates}
                  className="selection-action-button"
                  disabled={selectedStates.length === states.length}
                >
                  Select All
                </button>
                <button 
                  onClick={clearAllStates}
                  className="selection-action-button"
                  disabled={selectedStates.length === 0}
                >
                  Clear All
                </button>
              </div>
            </div>
            {/* Scrollable States Area */}
            <div className="states-scroll-container">
              <div className="state-checkbox-grid">
                {filteredStates.map((state) => (
                  <label key={state} className="state-checkbox-label">
                    <input
                      type="checkbox"
                      value={state}
                      checked={selectedStates.includes(state)}
                      onChange={handleStateChange}
                      className="state-checkbox-input"
                    />
                    {state}
                  </label>
                ))}
                {filteredStates.length === 0 && (
                  <div className="no-results">No matching states found</div>
                )}
              </div>
            </div>

            <div className="log-section">
              <div className="container-header">
                <span className="border-title">Processing Logs</span>
              </div>
              <div className="log-container">
                {logs.length > 0 ? (
                  <div className="log-output" ref={el => {
                    if (el) el.scrollTop = el.scrollHeight;
                  }}>
                    {logs.map((log, index) => (
                      <div key={index} className="log-entry">
                        {log}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="no-logs">
                    {loading ? "Waiting for logs..." : "No logs available"}
                  </div>
                )}
              </div>
            </div>

            {/* Generate Data Button */}
            <div className="submit-container">
              <button 
                onClick={handleSubmit} 
                disabled={loading || selectedStates.length === 0 || !apiKey}
                className="submit-button"
              >
                {loading ? 'Scraping...' : 'Generate Data'}
              </button>
              
              {/* Error message */}
              {error && !loading && (
                <div className="error-message">
                   <strong>Error:</strong> {error}
                </div>
              )}
            </div>
          </div>

          {/* Download Section */}
          {(
            <div className="download-section">
              <div className="container-header">
                <span className="border-title">Generated Files</span>
              </div>
              <div className="download-list">
                {downloadedFiles.map((file) => (
                  <div key={file.name} className="download-item">
                    <span className="download-item-name">{file.state} Data</span>
                    <a
                      href="#"
                      onClick={async (e) => {
                        e.preventDefault();
                        const url = await getDownloadUrl(file.name);
                        if (url && url !== "#") {
                          window.open(url, '_blank', 'noopener,noreferrer');
                        } else {
                          setError("Failed to get download URL");
                        }
                      }}
                      className="download-link"
                    >
                      Download
                    </a>
                  </div>
                ))}
              </div>

            </div>
          )}          
        </div>
      </div>
    </div>
  );
}

export default App;