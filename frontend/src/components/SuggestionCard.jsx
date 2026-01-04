import React from "react";

export default function SuggestionCard({ data }) {
  return (
    <div className="suggestion-card">
    <h3>Hairstyle: {data.hairstyle.style}</h3>
    <p>{data.hairstyle.description}</p>

    <h3>Beard: {data.beard.style}</h3>
    <p>{data.beard.description}</p>

    <h3>Outfit:</h3>
    {data.outfit.suggestions.map((o, i) => (
      <div key={i} style={{ marginBottom: "0.5rem" }}>
        <strong>{o.type}</strong>
        {o.season && <span style={{ marginLeft: "0.5rem", color: "#666", fontSize: "0.9em" }}>({o.season})</span>}
        {o.location && o.location !== "general" && (
          <span style={{ marginLeft: "0.5rem", color: "#666", fontSize: "0.9em" }}>📍 {o.location}</span>
        )}
        {o.description && <div style={{ fontSize: "0.9em", color: "#555", marginTop: "0.25rem" }}>{o.description}</div>}
        <div style={{ marginTop: "0.25rem" }}>{o.items.join(", ")}</div>
      </div>
    ))}
    <div style={{ marginTop: "1rem", padding: "0.5rem", backgroundColor: "#f0f0f0", borderRadius: "4px" }}>
      {data.season && <div><strong>Season:</strong> {data.season}</div>}
      {data.location && data.location !== "general" && (
        <div style={{ marginTop: "0.25rem" }}><strong>Location:</strong> {data.location}</div>
      )}
      {data.age && (
        <div style={{ marginTop: "0.25rem" }}><strong>Age:</strong> {data.age}</div>
      )}
    </div>
    <h3>Gender: {data.gender || "Unknown"}</h3>
    
    <h3>Skin tone: {data.skin_tone}</h3>
    <p>{data.explanation}</p>

    </div>
  );
}