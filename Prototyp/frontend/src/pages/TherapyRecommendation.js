import React, { useState } from "react";
import { Box, Typography, Paper, Button, Alert, Snackbar } from "@mui/material";
import { Save as SaveIcon } from "@mui/icons-material";
import axios from "axios";
import TherapyRequestForm from "../components/TherapyRequest/TherapyRequestForm";
import TherapyResults from "../components/TherapyResults/TherapyResults";
import SaveRecommendationDialog from "../components/SaveRecommendation/SaveRecommendationDialog";
import { therapyAPI } from "../services/api";

const API_BASE =
  process.env.NODE_ENV === "production" ? "" : "http://localhost:8000";

function TherapyRecommendation() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Form data
  const [requestData, setRequestData] = useState(null);
  const [therapyRecommendation, setTherapyRecommendation] = useState(null);
  const [patientData, setPatientData] = useState(null);

  // Dialog states
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);

  const handleFormSubmit = async (formData) => {
    setLoading(true);
    setError(null);

    try {
      console.log("Submitting therapy request:", formData);

      const response = await axios.post(
        `${API_BASE}/therapy/recommend`,
        formData
      );
      const recommendation = response.data;

      console.log("Raw backend response:", recommendation);
      console.log(
        "therapy_options from backend:",
        recommendation.therapy_options
      );
      console.log(
        "therapy_options length:",
        recommendation.therapy_options?.length
      );

      // Transform backend response to match frontend expectations
      const transformedRecommendation = {
        ...recommendation,
        // Map therapy_options to recommendations for compatibility
        recommendations: recommendation.therapy_options || [],
        // Ensure therapy_options is also available
        therapy_options: recommendation.therapy_options || [],
      };

      console.log("Transformed recommendation:", transformedRecommendation);
      console.log(
        "Transformed recommendations length:",
        transformedRecommendation.recommendations?.length
      );

      setRequestData(formData);
      setTherapyRecommendation(transformedRecommendation);
      setPatientData(recommendation.patient_data || null);

      console.log(
        "Therapy recommendation received:",
        transformedRecommendation
      );
    } catch (err) {
      console.error("Error generating therapy recommendation:", err);

      let errorMessage = err.message;
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          errorMessage = err.response.data.detail
            .map((error) => `${error.loc?.join(".") || "field"}: ${error.msg}`)
            .join("; ");
        } else if (typeof err.response.data.detail === "string") {
          errorMessage = err.response.data.detail;
        } else if (err.response.data.detail.msg) {
          errorMessage = err.response.data.detail.msg;
        }
      } else if (err.response?.status === 503) {
        // Special handling for 503 Service Unavailable (Koyeb timeout)
        errorMessage =
          "Zeitüberschreitung: Die Therapie-Empfehlung wird noch verarbeitet. " +
          "Dies ist normal bei komplexen Anfragen und dauert normalerweise 1-3 Minuten. " +
          "Bitte warten Sie einen Moment und versuchen Sie es dann erneut. " +
          "Die Verarbeitung läuft im Hintergrund weiter.";
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveRecommendation = async (title) => {
    if (!requestData || !therapyRecommendation) {
      setError("Keine Daten zum Speichern verfügbar");
      return;
    }

    try {
      setLoading(true);

      const saveData = {
        title: title || undefined,
        request_data: requestData,
        therapy_recommendation: therapyRecommendation,
        patient_data: patientData,
      };

      await therapyAPI.saveRecommendation(saveData);

      setSuccess("Therapie-Empfehlung erfolgreich gespeichert!");
      setSaveDialogOpen(false);
    } catch (err) {
      console.error("Error saving therapy recommendation:", err);

      let errorMessage =
        "Fehler beim Speichern der Therapie-Empfehlung. Bitte versuchen Sie es erneut.";

      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (typeof detail === "string") {
          errorMessage = detail;
        } else if (Array.isArray(detail)) {
          errorMessage = detail.map((d) => d.msg || d).join(", ");
        } else if (detail.msg) {
          errorMessage = detail.msg;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleStartNew = () => {
    setRequestData(null);
    setTherapyRecommendation(null);
    setPatientData(null);
    setError(null);
    setSuccess(null);
  };

  const handleCloseSnackbar = () => {
    setError(null);
    setSuccess(null);
  };

  return (
    <Box sx={{ width: "100%" }}>
      {/* Header */}
      <Box sx={{ mb: 4, textAlign: "center" }}>
        <Typography
          variant="h4"
          component="h1"
          gutterBottom
          sx={{
            fontWeight: 700,
            color: "primary.main",
            mb: 2,
          }}
        >
          Therapie-Empfehlung
        </Typography>
        <Typography
          variant="h6"
          color="text.secondary"
          sx={{ maxWidth: 600, mx: "auto" }}
        >
          Geben Sie die Patientendaten und klinischen Parameter ein, um eine KI
          generierte Therapie-Empfehlung zu erhalten.
        </Typography>
      </Box>

      {/* Content */}
      <Box sx={{ width: "100%" }}>
        {/* Therapy Request Form - Always visible */}
        <TherapyRequestForm onSubmit={handleFormSubmit} loading={loading} />

        {/* Results - Show when available */}
        {therapyRecommendation && (
          <Box sx={{ mt: 4 }}>
            <TherapyResults
              therapyRecommendation={therapyRecommendation}
              patientData={patientData}
              requestData={requestData}
            />

            {/* Action Buttons */}
            <Paper
              sx={{
                p: 3,
                mt: 3,
                display: "flex",
                gap: 2,
                justifyContent: "center",
              }}
            >
              <Button
                variant="outlined"
                onClick={handleStartNew}
                sx={{ minWidth: 150 }}
              >
                Neue Anfrage
              </Button>
              <Button
                variant="contained"
                startIcon={<SaveIcon />}
                onClick={() => setSaveDialogOpen(true)}
                sx={{ minWidth: 150 }}
              >
                Speichern
              </Button>
            </Paper>
          </Box>
        )}
      </Box>

      {/* Save Dialog */}
      <SaveRecommendationDialog
        open={saveDialogOpen}
        onClose={() => setSaveDialogOpen(false)}
        onSave={handleSaveRecommendation}
        loading={loading}
      />

      {/* Snackbars for feedback */}
      <Snackbar
        open={!!error}
        autoHideDuration={error?.includes("⏱️") ? 10000 : 6000} // Longer for timeout messages
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert
          severity={error?.includes("⏱️") ? "warning" : "error"}
          onClose={handleCloseSnackbar}
          sx={{ width: "100%" }}
          action={
            error?.includes("⏱️") && requestData ? (
              <Button
                color="inherit"
                size="small"
                onClick={() => {
                  setError(null);
                  handleFormSubmit(requestData);
                }}
                disabled={loading}
              >
                Erneut versuchen
              </Button>
            ) : null
          }
        >
          {error}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!success}
        autoHideDuration={4000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert
          severity="success"
          onClose={handleCloseSnackbar}
          sx={{ width: "100%" }}
        >
          {success}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default TherapyRecommendation;
