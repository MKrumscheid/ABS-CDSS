import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Snackbar,
  CircularProgress,
} from "@mui/material";
import {
  BookmarkBorder as SavedIcon,
  Visibility as ViewIcon,
  Delete as DeleteIcon,
  AccessTime as TimeIcon,
  Person as PersonIcon,
  LocalHospital as HospitalIcon,
} from "@mui/icons-material";
import { format, parseISO } from "date-fns";
import { de } from "date-fns/locale";
import { therapyAPI } from "../services/api";
import TherapyResults from "../components/TherapyResults/TherapyResults";

function SavedRequests() {
  const [savedRecommendations, setSavedRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Detail view states
  const [selectedRecommendation, setSelectedRecommendation] = useState(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);

  // Delete states
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  useEffect(() => {
    loadSavedRecommendations();
  }, []);

  const loadSavedRecommendations = async () => {
    setLoading(true);
    setError(null);

    try {
      const recommendations = await therapyAPI.getSavedRecommendations();
      console.log("API response:", recommendations); // Debug log

      // Ensure we have an array
      if (Array.isArray(recommendations)) {
        setSavedRecommendations(recommendations);
      } else {
        console.error("API response is not an array:", recommendations);
        setSavedRecommendations([]);
        setError("Unerwartetes Datenformat vom Server");
      }
    } catch (err) {
      console.error("Error loading saved recommendations:", err);
      setError("Fehler beim Laden der gespeicherten Empfehlungen");
      setSavedRecommendations([]); // Ensure we have an empty array on error
    } finally {
      setLoading(false);
    }
  };

  const handleViewRecommendation = async (id) => {
    setDetailLoading(true);
    setError(null);

    try {
      const recommendation = await therapyAPI.getSavedRecommendation(id);
      setSelectedRecommendation(recommendation);
      setDetailDialogOpen(true);
    } catch (err) {
      console.error("Error loading recommendation details:", err);
      setError("Fehler beim Laden der Empfehlungsdetails");
    } finally {
      setDetailLoading(false);
    }
  };

  const handleDeleteRecommendation = async () => {
    if (!itemToDelete) return;

    setDeleteLoading(true);

    try {
      await therapyAPI.deleteSavedRecommendation(itemToDelete.id);
      setSavedRecommendations((prev) =>
        prev.filter((item) => item.id !== itemToDelete.id)
      );
      setSuccess("Empfehlung erfolgreich gelöscht");
      setDeleteDialogOpen(false);
      setItemToDelete(null);
    } catch (err) {
      console.error("Error deleting recommendation:", err);
      setError("Fehler beim Löschen der Empfehlung");
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleDeleteClick = (recommendation) => {
    setItemToDelete(recommendation);
    setDeleteDialogOpen(true);
  };

  const formatDate = (dateString) => {
    try {
      return format(parseISO(dateString), "dd.MM.yyyy HH:mm", { locale: de });
    } catch (err) {
      return dateString;
    }
  };

  const handleCloseSnackbar = () => {
    setError(null);
    setSuccess(null);
  };

  if (loading) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: 400,
        }}
      >
        <CircularProgress size={40} />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Lade gespeicherte Empfehlungen...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ width: "100%" }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography
          variant="h4"
          gutterBottom
          sx={{ fontWeight: 600, color: "primary.main" }}
        >
          Gespeicherte Anfragen
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Übersicht über alle gespeicherten Therapie-Empfehlungen
        </Typography>
      </Box>

      {/* Summary Stats */}
      <Paper
        sx={{
          p: 3,
          mb: 3,
          bgcolor: "primary.50",
          border: 1,
          borderColor: "primary.200",
        }}
      >
        <Grid container spacing={3} alignItems="center">
          <Grid item>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <SavedIcon color="primary" sx={{ fontSize: 32 }} />
              <Box>
                <Typography
                  variant="h5"
                  sx={{ fontWeight: 600, color: "primary.main" }}
                >
                  {savedRecommendations.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Gespeicherte Empfehlungen
                </Typography>
              </Box>
            </Box>
          </Grid>
          {savedRecommendations.length > 0 && (
            <Grid item>
              <Button
                variant="outlined"
                onClick={loadSavedRecommendations}
                disabled={loading}
              >
                Aktualisieren
              </Button>
            </Grid>
          )}
        </Grid>
      </Paper>

      {/* Content */}
      {savedRecommendations.length === 0 ? (
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <Paper sx={{ p: 6, textAlign: "center" }}>
              <SavedIcon
                sx={{ fontSize: 64, color: "text.secondary", mb: 2 }}
              />
              <Typography variant="h6" gutterBottom color="text.secondary">
                Keine gespeicherten Empfehlungen
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                Speichern Sie Ihre ersten Therapie-Empfehlungen, um sie hier
                wiederzufinden.
              </Typography>
              <Button variant="contained" href="/therapy">
                Neue Empfehlung erstellen
              </Button>
            </Paper>
          </Grid>
        </Grid>
      ) : (
        <Grid container spacing={2}>
          {savedRecommendations.map((recommendation) => (
            <Grid item xs={12} key={recommendation.id}>
              <Card
                sx={{
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
                  "&:hover": { boxShadow: 6 },
                }}
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  {/* Header */}
                  <Typography
                    variant="h6"
                    sx={{
                      fontWeight: 600,
                      lineHeight: 1.2,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      display: "-webkit-box",
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: "vertical",
                      mb: 2,
                    }}
                  >
                    {recommendation.title || `Empfehlung #${recommendation.id}`}
                  </Typography>

                  {/* Indication */}
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 1,
                      mb: 2,
                    }}
                  >
                    <HospitalIcon color="primary" sx={{ fontSize: 18 }} />
                    <Typography
                      variant="body2"
                      color="text.primary"
                      sx={{ fontWeight: 500 }}
                    >
                      {recommendation.indication_display}
                    </Typography>
                  </Box>

                  {/* Patient ID */}
                  {recommendation.patient_id && (
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 1,
                        mb: 2,
                      }}
                    >
                      <PersonIcon color="action" sx={{ fontSize: 18 }} />
                      <Typography variant="body2" color="text.secondary">
                        Patient ID: {recommendation.patient_id}
                      </Typography>
                    </Box>
                  )}

                  {/* Date */}
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 1,
                      mb: 2,
                    }}
                  >
                    <TimeIcon color="action" sx={{ fontSize: 18 }} />
                    <Typography variant="body2" color="text.secondary">
                      {formatDate(recommendation.created_at)}
                    </Typography>
                  </Box>

                  <Chip
                    label={`ID: ${recommendation.id}`}
                    size="small"
                    variant="outlined"
                    sx={{ fontSize: "0.75rem" }}
                  />
                </CardContent>

                <CardActions sx={{ p: 2, pt: 0 }}>
                  <Box
                    sx={{
                      display: "flex",
                      flexDirection: "column",
                      width: "100%",
                      gap: 1,
                    }}
                  >
                    <Button
                      size="small"
                      startIcon={
                        detailLoading ? (
                          <CircularProgress size={16} />
                        ) : (
                          <ViewIcon />
                        )
                      }
                      onClick={() =>
                        handleViewRecommendation(recommendation.id)
                      }
                      disabled={detailLoading}
                      fullWidth
                      variant="outlined"
                    >
                      {detailLoading ? "Lade..." : "Ansehen"}
                    </Button>

                    <Button
                      size="small"
                      startIcon={
                        deleteLoading && itemToDelete === recommendation.id ? (
                          <CircularProgress size={16} />
                        ) : (
                          <DeleteIcon />
                        )
                      }
                      onClick={() => handleDeleteClick(recommendation)}
                      disabled={
                        deleteLoading && itemToDelete === recommendation.id
                      }
                      fullWidth
                      variant="outlined"
                      color="error"
                      sx={{
                        borderColor: "error.main",
                        color: "error.main",
                        "&:hover": {
                          borderColor: "error.dark",
                          backgroundColor: "error.50",
                        },
                      }}
                    >
                      {deleteLoading && itemToDelete === recommendation.id
                        ? "Lösche..."
                        : "Löschen"}
                    </Button>
                  </Box>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Detail Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="lg"
        fullWidth
        PaperProps={{ sx: { minHeight: "80vh" } }}
      >
        <DialogTitle
          sx={{
            borderBottom: 1,
            borderColor: "divider",
            display: "flex",
            alignItems: "center",
            gap: 1,
          }}
        >
          <SavedIcon color="primary" />
          {selectedRecommendation?.title ||
            `Empfehlung #${selectedRecommendation?.id}`}
          <Chip
            label={
              selectedRecommendation
                ? formatDate(selectedRecommendation.created_at)
                : ""
            }
            size="small"
            sx={{ ml: "auto" }}
          />
        </DialogTitle>
        <DialogContent sx={{ p: 0 }}>
          {selectedRecommendation && (
            <Box sx={{ p: 3 }}>
              <TherapyResults
                therapyRecommendation={
                  selectedRecommendation.therapy_recommendation
                }
                patientData={selectedRecommendation.patient_data}
                requestData={selectedRecommendation.request_data}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => setDetailDialogOpen(false)}>Schließen</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => !deleteLoading && setDeleteDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ color: "error.main" }}>
          Empfehlung löschen
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            Möchten Sie die Empfehlung "
            {itemToDelete?.title || `#${itemToDelete?.id}`}" wirklich löschen?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Diese Aktion kann nicht rückgängig gemacht werden.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button
            onClick={() => setDeleteDialogOpen(false)}
            disabled={deleteLoading}
          >
            Abbrechen
          </Button>
          <Button
            onClick={handleDeleteRecommendation}
            disabled={deleteLoading}
            color="error"
            variant="contained"
            startIcon={
              deleteLoading ? (
                <CircularProgress size={16} color="inherit" />
              ) : (
                <DeleteIcon />
              )
            }
          >
            {deleteLoading ? "Lösche..." : "Löschen"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbars */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert
          severity="error"
          onClose={handleCloseSnackbar}
          sx={{ width: "100%" }}
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

export default SavedRequests;
