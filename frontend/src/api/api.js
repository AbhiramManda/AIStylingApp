import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000/api", // backend FastAPI endpoint
});

// attach token if exists
API.interceptors.request.use((req) => {
  const token = localStorage.getItem("token");
  if (token) req.headers.Authorization = `Bearer ${token}`;
  return req;
});

export const loginUser = (data) => API.post("/auth/login", data);
export const registerUser = (data) => API.post("/auth/register", data);
export const uploadImage = (formData) => API.post("/upload/image", formData);

// export const getSuggestions = (data) => API.post("/suggestions", data);
// Add this function
export const getSuggestions = async (data) => {
  const token = localStorage.getItem("token"); // stored after login
  return API.post("/suggestions", data, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
};

export default API; 