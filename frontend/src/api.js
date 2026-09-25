// api.js - API calls to FastAPI backend
import axios from "axios";

// In dev → http://localhost:8000
// In prod (Vercel) → set VITE_API_URL in Vercel dashboard
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
});

/**
 * Send a chat question to the RAG backend.
 */
export async function sendQuestion({ question, subject, unit, marks = null }) {
  const payload = { question, subject, unit, semester: 7 };
  if (marks) payload.marks = marks;
  const res = await api.post("/chat", payload);
  return res.data;
}

/**
 * Button-driven: fetch ALL questions for subject + unit + marks.
 * No user text needed — direct Qdrant lookup.
 */
export async function fetchQuestions({ subject, unit, marks }) {
  const res = await api.post("/questions", { subject, unit, marks });
  return res.data;
}
