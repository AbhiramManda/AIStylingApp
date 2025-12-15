import React from "react";
import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="navbar">
      <h2>AI Personal Stylist</h2>
      <div>
        <Link to="/camera">Camera</Link>
        <Link to="/suggestions">Suggestions</Link>
        <Link to="/chat">Chat</Link>
        <Link to="/">Logout</Link>
      </div>
    </nav>
  );
}
