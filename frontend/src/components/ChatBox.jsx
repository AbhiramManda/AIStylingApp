import React, { useState } from "react";
import API from "../api/api";

export default function ChatBox() {
  const [messages, setMessages] = useState([
    { sender: "ai", text: "Hi! 👋 Describe your look or ask for style ideas!" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const newMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, newMessage]);
    setLoading(true);

    try {
      const res = await API.post("/suggestions/prompt", { prompt: input });
      const reply = res.data.explanation || res.data.hairstyle?.description || "Here are your suggestions!";
      setMessages((prev) => [...prev, { sender: "ai", text: reply }]);
    } catch (err) {
      console.error("Error:", err);
      setMessages((prev) => [...prev, { sender: "ai", text: "Sorry, something went wrong." }]);
    }

    setLoading(false);
    setInput("");
  };

  return (
    <div className="flex flex-col w-full max-w-lg mx-auto bg-white shadow-lg rounded-2xl p-4">
      <div className="flex flex-col space-y-3 overflow-y-auto h-96 p-2 border-b">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`p-2 rounded-lg max-w-[80%] ${
              msg.sender === "user"
                ? "bg-black text-white self-end"
                : "bg-gray-200 text-black self-start"
            }`}
          >
            {msg.text}
          </div>
        ))}
        {loading && (
          <div className="self-start text-gray-400 italic">Thinking...</div>
        )}
      </div>

      <form onSubmit={handleSend} className="flex mt-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your style question..."
          className="flex-1 border rounded-l-lg p-2 outline-none"
        />
        <button
          type="submit"
          className="bg-black text-white px-4 py-2 rounded-r-lg"
          disabled={loading}
        >
          Send
        </button>
      </form>
    </div>
  );
}
