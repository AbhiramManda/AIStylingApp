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



import React, { useState, useRef, useEffect } from "react";
// import { uploadImage } from "../api/api";
import { uploadImage, getSuggestions } from "../api/api.js";
import { useNavigate } from "react-router-dom";

export default function CameraCapture() {
  const videoRef = useRef(null);
  const [captured, setCaptured] = useState(null);
  const navigate = useNavigate();
  const [locationDetecting, setLocationDetecting] = useState(false);

  // Detect location on mount (before user uploads image)
  useEffect(() => {
    const detectLocation = async () => {
      // Skip if location already exists
      if (localStorage.getItem("userLocation")) {
        return;
      }

      setLocationDetecting(true);
      try {
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(
            async (position) => {
              try {
                // Use reverse geocoding to get location name
                let detectedLocation = "";
                
                // Try OpenStreetMap Nominatim first
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
                  const city = data.city || data.locality;
                  const state = data.principalSubdivision || data.administrativeArea;
                  if (city) {
                    detectedLocation = state ? `${city}, ${state}` : city;
                  } else {
                    detectedLocation = data.principalSubdivision || data.locality || data.countryName || "";
                  }
                }
                
                if (detectedLocation) {
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
        // Get location (should be detected by now, or wait a moment if still detecting)
        let userLocation = localStorage.getItem("userLocation");
        if (!userLocation && locationDetecting) {
          // Wait a bit for location detection to complete
          await new Promise(resolve => setTimeout(resolve, 2000));
          userLocation = localStorage.getItem("userLocation");
        }
        
        const payload = {
          image_url: imageUrl,
          body_type: "slim", // required by backend
        };
        // Include location if detected
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
