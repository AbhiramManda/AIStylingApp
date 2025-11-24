import React, { useState } from "react";
import axios from "axios";
import LoadingSpinner from "../components/LoadingSpinner";
import AlertBox from "../components/AlertBox";

const UploadImage = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState({ type: "", message: "" });

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreview(URL.createObjectURL(file));
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setAlert({ type: "warning", message: "Please select an image first." });
      return;
    }

    setLoading(true);
    setAlert({ type: "", message: "" });

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await axios.post("http://localhost:8000/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setAlert({ type: "success", message: "Image uploaded successfully!" });
      console.log("Upload response:", res.data);
    } catch (err) {
      console.error("Upload failed:", err);
      setAlert({ type: "error", message: "Upload failed. Try again." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 p-6">
      <h2 className="text-2xl font-semibold mb-6 text-gray-800">
        Upload Your Photo
      </h2>

      {alert.message && (
        <AlertBox type={alert.type} message={alert.message} onClose={() => setAlert({ type: "", message: "" })} />
      )}

      <div className="w-full max-w-md bg-white shadow-md rounded-2xl p-6 flex flex-col items-center">
        <input
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          className="mb-4"
        />

        {preview && (
          <img
            src={preview}
            alt="Preview"
            className="w-48 h-48 object-cover rounded-xl mb-4 border"
          />
        )}

        <button
          onClick={handleUpload}
          disabled={loading}
          className="bg-blue-600 text-white px-5 py-2 rounded-xl hover:bg-blue-700 transition disabled:bg-gray-400"
        >
          {loading ? "Uploading..." : "Upload"}
        </button>

        {loading && (
          <div className="mt-4">
            <LoadingSpinner />
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadImage;
