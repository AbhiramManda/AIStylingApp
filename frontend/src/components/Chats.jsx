import React, { useState, useEffect, useRef } from "react";

const API_BASE = "http://localhost:8000/api";

export default function Chat() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Load recent history on mount
  useEffect(() => {
    const loadHistory = async () => {
      const token = localStorage.getItem("token");
      if (!token) return; // No auth → skip
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
        const data = await res.json(); // [{message, response, ...}]
        const history = [];
        // Flatten each record into user + assistant messages (chronological)
        data
          .slice() // copy
          .reverse() // ensure oldest first for display
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

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const token = localStorage.getItem("token");
    if (!token) {
      setError("Please log in to chat.");
      return;
    }

    setError("");
    setMessages((prev) => [...prev, { role: "user", text: input }]);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message: input }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data?.detail || "Something went wrong. Please try again.");
        // remove the last optimistic user message if desired
        return;
      }

      setMessages((prev) => [...prev, { role: "ai", text: data.response }]);
      setInput("");
    } catch (err) {
      console.error("Error sending message:", err);
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto p-6">
      <div className="h-96 overflow-y-auto bg-gray-50 border rounded-lg p-4 space-y-3 shadow">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`p-3 rounded-lg max-w-[80%] ${
              msg.role === "user"
                ? "bg-blue-500 text-white self-end ml-auto"
                : "bg-gray-200 text-black"
            }`}
          >
            {msg.text}
          </div>
        ))}
        {loading && (
          <div className="text-gray-400 italic">Stylist is thinking...</div>
        )}
        {error && (
          <div className="text-red-600 text-sm bg-red-50 p-2 rounded">
            {error}
          </div>
        )}
        <div ref={messagesEndRef}></div>
      </div>

      <div className="flex mt-4 gap-2">
        <input
          className="flex-1 border rounded-lg px-3 py-2"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your prompt..."
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          disabled={loading}
        />
        <button
          className="bg-black text-white px-4 rounded-lg shadow disabled:opacity-60"
          onClick={sendMessage}
          disabled={loading}
        >
          {loading ? "Sending..." : "Send"}
        </button>
      </div>
    </div>
  );
}
