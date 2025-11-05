import React, { useState, useEffect } from "react";
import axios from "axios";
import "./RagStatusBanner.css";

const API_BASE =
  process.env.NODE_ENV === "production" ? "" : "http://localhost:8000";

const RagStatusBanner = () => {
  const [ragStatus, setRagStatus] = useState(null);
  const [visible, setVisible] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRagStatus = async () => {
      try {
        const response = await axios.get(`${API_BASE}/rag-status`);
        setRagStatus(response.data);
        setLoading(false);
      } catch (error) {
        console.error("Failed to fetch RAG status:", error);
        setLoading(false);
      }
    };

    fetchRagStatus();
    // Check status every 30 seconds
    const interval = setInterval(fetchRagStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !ragStatus || !visible) {
    return null;
  }

  return (
    <div
      className={`rag-status-banner ${
        ragStatus.rag_enabled ? "rag-enabled" : "rag-disabled"
      }`}
    >
      <div className="rag-status-content">
        <span className="rag-status-icon">
          {ragStatus.rag_enabled ? "✓" : "⚠"}
        </span>
        <span className="rag-status-text">{ragStatus.mode}</span>
      </div>
      <button
        className="rag-status-close"
        onClick={() => setVisible(false)}
        aria-label="Banner schließen"
      >
        ×
      </button>
    </div>
  );
};

export default RagStatusBanner;
