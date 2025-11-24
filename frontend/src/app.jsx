import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import CameraCapture from "./pages/CameraCapture.jsx";
import Suggestions from "./pages/Suggestions.jsx";
import Navbar from "./components/Navbar.jsx";
import Footer from "./components/Footer.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
// import Alerts from "./components/Alert.jsx";
import UploadButton from "./components/UploadButton.jsx"
import ChatBox from "./components/ChatBox";





export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/camera" element={<CameraCapture />} />
        <Route path="/suggestions" element={<Suggestions />} />
        {/* <div className="min-h-screen bg-gray-50 flex justify-center items-center">
          <ChatBox/>
        </div> */}
      </Routes>
      <Footer />
    </BrowserRouter>

  );
}
