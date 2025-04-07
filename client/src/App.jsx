import { useState } from "react";
import './App.css';

function App() {
  const [selectedStates, setSelectedStates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [downloadedFiles, setDownloadedFiles] = useState([]);
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [error, setError] = useState(null);
  const [apiError, setApiError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  
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
      setApiError(null);
      return;
    }
  
    setLoading(true);
    setError(null);
    setApiError(null);
    setDownloadedFiles([]);
    
    try {
      const response = await fetch("/api/scrape", {
      // const response = await fetch("http://127.0.0.1:8000/api/scrape", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json" // Explicitly request JSON
        },
        body: JSON.stringify({ states: selectedStates, api_key: apiKey }),
      });
  
      // First get the raw response text
      const responseText = await response.text();
      console.log(responseText)
      
      try {
        // Try to parse as JSON
        const result = responseText ? JSON.parse(responseText) : {};
        
        if (!response.ok) {
          if (result.detail && result.detail.includes("Google Maps API key")) {
            setApiError(result.detail);
          } else {
            setError(result.detail || "Failed to fetch data");
          }
          // Also log the raw response for debugging
          console.error('API Error Response:', {
            status: response.status,
            rawResponse: responseText,
            parsedResponse: result
          });
          return;
        }
  
        const files = selectedStates.map(state => ({
          name: `scraped_population_and_job_data_${state.toLowerCase().replace(' ', '_')}.xlsx`,
          state: state
        }));
        setDownloadedFiles(files);
        
      } catch (jsonError) {
        // JSON parsing failed
        const errorMsg = `Server returned non-JSON response (status ${response.status})`;
        setError(errorMsg);
        
        // Log detailed error information
        console.error('JSON Parsing Error:', {
          error: jsonError,
          status: response.status,
          headers: Object.fromEntries(response.headers.entries()),
          rawResponse: responseText,
          contentType: response.headers.get('content-type')
        });
        
        // Create a more detailed error message for debugging
        setError(prev => `${errorMsg}. Received: ${responseText.substring(0, 200)}${responseText.length > 200 ? '...' : ''}`);
      }
    } catch (networkError) {
      console.error("Network Error:", networkError);
      setError(networkError.message || "Failed to connect to server");
    } finally {
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
                      setApiError(null);
                    }}
                    className={`api-key-input ${apiError ? 'error' : ''}`}
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

              {/* API error message */}
              {apiError && (
                <p className="api-error">
                  {apiError}
                  <small>(Closest Metro Areas may not be generated)</small>
                </p>
              )}
            
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