// const uploadPhoto = async () => {
//   if (!captured) return;

//   try {
//     const blob = await fetch(captured).then((r) => r.blob());
//     const formData = new FormData();
//     formData.append("file", blob, "photo.jpg");

//     const uploadRes = await uploadImage(formData);
//     const imageUrl = uploadRes.data.url;

//     const suggestionsRes = await getSuggestions({
//       image_url: imageUrl,
//       body_type: "slim"
//     });

//     navigate("/suggestions", {
//       state: { suggestions: suggestionsRes.data }
//     });
//   } catch (err) {
//     console.error(err);
//   }
// };



import React, { useState, useRef } from "react";
// import { uploadImage } from "../api/api";
import { uploadImage, getSuggestions } from "../api/api.js";
import { useNavigate } from "react-router-dom";

export default function CameraCapture() {
  const videoRef = useRef(null);
  const [captured, setCaptured] = useState(null);
  const navigate = useNavigate();

  const startCamera = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    videoRef.current.srcObject = stream;
  };

  const capturePhoto = () => {
    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(videoRef.current, 0, 0);
    const dataUrl = canvas.toDataURL("image/jpeg");
    setCaptured(dataUrl);
  };

  // const uploadPhoto = async () => {
  //   const blob = await fetch(captured).then((res) => res.blob());
  //   const formData = new FormData();
  //   formData.append("file", blob, "photo.jpg");
  //   await uploadImage(formData);
  //   navigate("/suggestions");
  // };
  const uploadPhoto = async () => {
    if (!captured) return;
  
    try {
      const blob = await fetch(captured).then((res) => res.blob());
      const formData = new FormData();
      formData.append("file", blob, "photo.jpg");
  
      let imageUrl;
      try {
        const uploadRes = await uploadImage(formData);
        imageUrl = uploadRes.data.url;
        console.log("Uploaded image URL:", imageUrl);
      } catch (uploadErr) {
        console.error("Upload error:", uploadErr.response || uploadErr);
        alert("Upload failed");
        return;
      }
  
      try {
        // Location will be auto-detected from image analysis, but include stored location if available
        const userLocation = localStorage.getItem("userLocation");
        const payload = {
          image_url: imageUrl,
          body_type: "slim", // required by backend
        };
        // Only include location if manually set (auto-detected location is handled by backend)
        if (userLocation && userLocation.trim()) {
          payload.location = userLocation.trim();
        }
        // Age will be auto-detected from image (AgeRange)
        const suggestionsRes = await getSuggestions(payload);
        console.log("Suggestions received:", suggestionsRes.data);
        navigate("/suggestions", { state: { suggestions: suggestionsRes.data } });
        // localStorage.setItem("uploadedImage", imageUrl);
        // navigate("/suggestions");
      } catch (suggestErr) {
        console.error("Suggestions error:", suggestErr.response || suggestErr);
        alert("Suggestions failed");
        return;
      }
  
    } catch (err) {
      console.error("Unexpected error:", err);
      alert("Unexpected error");
    }
  };
  

  return (
    <div className="camera-container">
      {!captured ? (
        <>
          <video ref={videoRef} autoPlay className="camera-feed"></video>
          <button onClick={startCamera}>Start Camera</button>
          <button onClick={capturePhoto}>Capture</button>
        </>
      ) : (
        <>
          <img src={captured} alt="Captured" className="preview" />
          <button onClick={uploadPhoto}>Upload</button>
          <button onClick={() => setCaptured(null)}>Retake</button>
        </>
      )}
    </div>
  );
}
