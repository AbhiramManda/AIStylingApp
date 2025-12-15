import React from "react";
import { useLocation } from "react-router-dom";
import SuggestionCard from "../components/SuggestionCard.jsx";
import Chats from "../components/Chats.jsx";

export default function Suggestions() {
  const { state } = useLocation();

  const suggestionData =
    state?.suggestions?.suggestion || state?.suggestions;

  if (!suggestionData) return <p>No suggestions found.</p>;

  return (
    <div className="suggestions-container">
      <h2>AI Styling Suggestions</h2>
      <SuggestionCard data={suggestionData} />

      {/* Chat box appears below suggestions so user can ask follow-up questions */}
      <div style={{ marginTop: "2rem" }}>
        <h3>Chat with your AI Stylist</h3>
        <Chats />
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
