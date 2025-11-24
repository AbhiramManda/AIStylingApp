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
      <div key={i}>
        <strong>{o.type}:</strong> {o.items.join(", ")}
      </div>
    ))}
    <h3>Gender: {data.gender || "Unknown"}</h3>
    
    <h3>Skin tone: {data.skin_tone}</h3>
    <p>{data.explanation}</p>

    </div>
  );
}