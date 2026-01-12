import React, { useState, useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import SuggestionCard from "../components/SuggestionCard.jsx";

const API_BASE = "http://localhost:8000/api";

export default function Suggestions() {
  const { state } = useLocation();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef(null);
  const [suggestionData, setSuggestionData] = useState(
    state?.suggestions?.suggestion || state?.suggestions
  );
  const [location, setLocation] = useState(
    suggestionData?.location || localStorage.getItem("userLocation") || ""
  );
  const [age, setAge] = useState(
    suggestionData?.age || (localStorage.getItem("userAge") ? parseInt(localStorage.getItem("userAge")) : null)
  );
  const [locationDetecting, setLocationDetecting] = useState(false);
  const [updatingSuggestions, setUpdatingSuggestions] = useState(false);

  // Auto-detect location on mount using GPS only (only if not already detected)
  useEffect(() => {
    const detectLocation = async () => {
      // Skip if location already exists (should be detected before reaching this page)
      if (localStorage.getItem("userLocation")) {
        return;
      }

      setLocationDetecting(true);
      try {
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(
            async (position) => {
              try {
                // Use reverse geocoding to get location name - try multiple services for accuracy
                let detectedLocation = "";
                
                // Try OpenStreetMap Nominatim first (free, accurate)
                try {
                  const osmResponse = await fetch(
                    `https://nominatim.openstreetmap.org/reverse?format=json&lat=${position.coords.latitude}&lon=${position.coords.longitude}&zoom=10&addressdetails=1`,
                    { headers: { 'User-Agent': 'AI-Styling-App' } }
                  );
                  const osmData = await osmResponse.json();
                  if (osmData && osmData.address) {
                    const city = osmData.address.city || osmData.address.town || osmData.address.village || osmData.address.municipality;
                    const state = osmData.address.state || osmData.address.region;
                    if (city) {
                      detectedLocation = state ? `${city}, ${state}` : city;
                    }
                  }
                } catch (osmErr) {
                  console.error("OSM geocoding error:", osmErr);
                }
                
                // Fallback to bigdatacloud if OSM fails
                if (!detectedLocation) {
                  const response = await fetch(
                    `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${position.coords.latitude}&longitude=${position.coords.longitude}&localityLanguage=en`
                  );
                  const data = await response.json();
                  
                  // Combine city and state/region for better accuracy
                  const city = data.city || data.locality;
                  const state = data.principalSubdivision || data.administrativeArea;
                  if (city) {
                    detectedLocation = state ? `${city}, ${state}` : city;
                  } else {
                    detectedLocation = data.principalSubdivision || data.locality || data.countryName || "";
                  }
                }
                
                if (detectedLocation) {
                  setLocation(detectedLocation);
                  localStorage.setItem("userLocation", detectedLocation);
                }
              } catch (err) {
                console.error("Error reverse geocoding:", err);
              }
              setLocationDetecting(false);
            },
            (error) => {
              console.error("Geolocation error:", error);
              setLocationDetecting(false);
            },
            { timeout: 10000, enableHighAccuracy: true, maximumAge: 300000 }
          );
        } else {
          console.warn("Geolocation is not supported by this browser");
          setLocationDetecting(false);
        }
      } catch (err) {
        console.error("Location detection error:", err);
        setLocationDetecting(false);
      }
    };

    detectLocation();
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Load recent history on mount
  useEffect(() => {
    const loadHistory = async () => {
      const token = localStorage.getItem("token");
      if (!token) return;
      try {
        const res = await fetch(`${API_BASE}/chat/history`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (!res.ok) {
          console.warn("Could not load history", await res.text());
          return;
        }
        const data = await res.json();
        const history = [];
        data
          .slice()
          .reverse()
          .forEach((item) => {
            history.push({ role: "user", text: item.message });
            history.push({ role: "ai", text: item.response });
          });
        setMessages(history);
      } catch (err) {
        console.error("Error loading history:", err);
      }
    };
    loadHistory();
  }, []);

  const updateSuggestionsForLocation = async () => {
    if (!suggestionData || !location || !location.trim() || updatingSuggestions) return;
    
    const token = localStorage.getItem("token");
    if (!token) {
      setError("Please log in to update suggestions.");
      return;
    }

    setUpdatingSuggestions(true);
    setError("");

    try {
      const requestBody = {
        message: `Update suggestions for location: ${location.trim()}${age ? ` and age: ${age}` : ""}`,
        current_suggestions: {
          ...suggestionData,
          location: location.trim(),
          ...(age ? { age } : {})
        },
        location: location.trim(),
        ...(age ? { age } : {})
      };

      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(requestBody),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data?.detail || "Failed to update suggestions.");
        return;
      }

      // Update suggestions if AI returned new ones
      if (data.updated_suggestions) {
        setSuggestionData(data.updated_suggestions);
        // Show a notification that suggestions were updated
        setMessages((prev) => [
          ...prev,
          { 
            role: "system", 
            text: `✨ Suggestions updated for ${location.trim()}!` 
          }
        ]);
      } else {
        // If no updated suggestions, try to update current suggestions with new location/age
        setSuggestionData({
          ...suggestionData,
          location: location.trim(),
          ...(age ? { age } : {})
        });
      }
    } catch (err) {
      console.error("Error updating suggestions:", err);
      setError("Failed to update suggestions. Please try again.");
    } finally {
      setUpdatingSuggestions(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const token = localStorage.getItem("token");
    if (!token) {
      setError("Please log in to chat.");
      return;
    }

    setError("");
    const userMessage = input;
    setMessages((prev) => [...prev, { role: "user", text: userMessage }]);
    setLoading(true);

    try {
      const requestBody = {
        message: userMessage,
      };
      
      // Include current suggestions if available
      if (suggestionData) {
        requestBody.current_suggestions = suggestionData;
      }
      
      // Include location if provided
      if (location && location.trim()) {
        requestBody.location = location.trim();
        // Save to localStorage
        localStorage.setItem("userLocation", location.trim());
      }
      
      // Include age if provided
      if (age && age > 0) {
        requestBody.age = age;
        // Save to localStorage
        localStorage.setItem("userAge", age.toString());
      }

      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(requestBody),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data?.detail || "Something went wrong. Please try again.");
        return;
      }

      setMessages((prev) => [...prev, { role: "ai", text: data.response }]);
      
      // Update suggestions if AI returned new ones
      if (data.updated_suggestions) {
        setSuggestionData(data.updated_suggestions);
        // Update location if it's in the updated suggestions
        if (data.updated_suggestions.location) {
          setLocation(data.updated_suggestions.location);
          localStorage.setItem("userLocation", data.updated_suggestions.location);
        }
        // Update age if it's in the updated suggestions
        if (data.updated_suggestions.age) {
          setAge(data.updated_suggestions.age);
          localStorage.setItem("userAge", data.updated_suggestions.age.toString());
        }
        // Show a notification that suggestions were updated
        setMessages((prev) => [
          ...prev,
          { 
            role: "system", 
            text: "✨ Your suggestions have been updated based on your request!" 
          }
        ]);
      }
      
      setInput("");
    } catch (err) {
      console.error("Error sending message:", err);
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (!suggestionData) return <p>No suggestions found.</p>;

  // Get current season for display
  const getCurrentSeason = () => {
    const month = new Date().getMonth() + 1; // 1-12
    if (month >= 12 || month <= 2) return "winter";
    if (month >= 3 && month <= 5) return "spring";
    if (month >= 6 && month <= 8) return "summer";
    return "fall";
  };

  const currentSeason = suggestionData?.season || getCurrentSeason();

  return (
    <div className="suggestions-container" style={{ maxWidth: "1200px", margin: "0 auto", padding: "2rem" }}>
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", marginBottom: "2rem" }}>
        <h2 style={{ margin: 0, textAlign: "center" }}>AI Styling Suggestions</h2>
        <div style={{ 
          marginLeft: "2rem",
          padding: "0.5rem 1rem", 
          backgroundColor: "#e0f2fe", 
          borderRadius: "8px",
          fontSize: "0.9rem",
          fontWeight: "500",
          color: "#0369a1"
        }}>
          Season: <span style={{ textTransform: "capitalize" }}>{currentSeason}</span>
        </div>
      </div>
      
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem", marginBottom: "2rem" }}>
        {/* Suggestions Card */}
        <div>
          <SuggestionCard data={suggestionData} />
        </div>

        {/* Integrated Chat */}
        <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
          <h3 style={{ marginBottom: "1rem", fontSize: "1.25rem" }}>Chat with your AI Stylist</h3>
          
          <div style={{ 
            height: "400px", 
            overflowY: "auto", 
            backgroundColor: "#f9fafb", 
            border: "1px solid #e5e7eb", 
            borderRadius: "8px", 
            padding: "1rem", 
            marginBottom: "1rem",
            display: "flex",
            flexDirection: "column",
            gap: "0.75rem"
          }}>
            {messages.length === 0 && (
              <div style={{ 
                color: "#6b7280", 
                fontStyle: "italic", 
                textAlign: "center",
                marginTop: "2rem"
              }}>
                Ask me anything about your styling suggestions!
              </div>
            )}
            {messages.map((msg, i) => (
              <div
                key={i}
                style={{
                  padding: "0.75rem",
                  borderRadius: "8px",
                  maxWidth: "80%",
                  backgroundColor: msg.role === "user" 
                    ? "#3b82f6" 
                    : msg.role === "system"
                    ? "#fef3c7"
                    : "#e5e7eb",
                  color: msg.role === "user" ? "white" : "black",
                  marginLeft: msg.role === "user" ? "auto" : "0",
                  alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                  fontWeight: msg.role === "system" ? "600" : "normal"
                }}
              >
                {msg.text}
              </div>
            ))}
            {loading && (
              <div style={{ color: "#6b7280", fontStyle: "italic" }}>
                Stylist is thinking...
              </div>
            )}
            {error && (
              <div style={{ 
                color: "#dc2626", 
                fontSize: "0.875rem", 
                backgroundColor: "#fef2f2", 
                padding: "0.5rem", 
                borderRadius: "4px" 
              }}>
                {error}
              </div>
            )}
            <div ref={messagesEndRef}></div>
          </div>

          <div style={{ display: "flex", gap: "0.5rem" }}>
            <input
              style={{
                flex: 1,
                border: "1px solid #d1d5db",
                borderRadius: "8px",
                padding: "0.5rem 0.75rem",
                outline: "none"
              }}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={`Ask about your suggestions... (e.g., "change casual outfit to ${currentSeason === "winter" ? "summer" : "winter"}")`}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              disabled={loading}
            />
            <button
              style={{
                backgroundColor: "#000",
                color: "white",
                padding: "0.5rem 1rem",
                borderRadius: "8px",
                border: "none",
                cursor: loading ? "not-allowed" : "pointer",
                opacity: loading ? 0.6 : 1
              }}
              onClick={sendMessage}
              disabled={loading}
            >
              {loading ? "Sending..." : "Send"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}



// import React, { useState, useEffect } from "react";
// import { getSuggestions } from "../api/api.js";
// import SuggestionCard from "../components/SuggestionCard.jsx";

// export default function Suggestions() {
//   const [suggestions, setSuggestions] = useState(null);

//   useEffect(() => {
//     async function fetchData() {
//       // const res = await getSuggestions({ user_id: 1 });
//       const imageUrl = localStorage.getItem("uploadedImage"); // or from state if you store it
//       const res = await getSuggestions({ image_url: imageUrl, body_type: "average" });

//       setSuggestions(res.data.suggestion);
//         }
        
//     fetchData();
//   }, []);

//   return (
//     <div className="suggestions-container">
//       <h2>AI Styling Suggestions</h2>
//       {suggestions ? (
//         <SuggestionCard data={suggestions} />
//       ) : (
//         <p>Loading suggestions...</p>
//       )}
//     </div>
//   );
// }
