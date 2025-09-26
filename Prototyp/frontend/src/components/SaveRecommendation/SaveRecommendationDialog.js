import React, { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Typography,
  Box,
  CircularProgress,
} from "@mui/material";
import { Save as SaveIcon, Close as CloseIcon } from "@mui/icons-material";

function SaveRecommendationDialog({ open, onClose, onSave, loading = false }) {
  const [title, setTitle] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(title.trim() || null);
  };

  const handleClose = () => {
    setTitle("");
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={!loading ? handleClose : undefined}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: { borderRadius: 2 },
      }}
    >
      <form onSubmit={handleSubmit}>
        <DialogTitle
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
            bgcolor: "primary.50",
            borderBottom: 1,
            borderColor: "divider",
          }}
        >
          <SaveIcon color="primary" />
          Therapie-Empfehlung speichern
        </DialogTitle>

        <DialogContent sx={{ pt: 3 }}>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Sie können Ihre Therapie-Empfehlung mit einem optionalen Titel
              speichern. Gespeicherte Empfehlungen können jederzeit über
              "Gespeicherte Anfragen" abgerufen werden.
            </Typography>

            <TextField
              autoFocus
              fullWidth
              label="Titel (optional)"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="z.B. Patient Schmidt - Pneumonie"
              helperText="Lassen Sie das Feld leer für automatische Benennung"
              disabled={loading}
              inputProps={{ maxLength: 200 }}
              sx={{ mt: 1 }}
            />

            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ mt: 1, display: "block" }}
            >
              Die Empfehlung wird mit Datum und allen relevanten Daten
              gespeichert.
            </Typography>
          </Box>
        </DialogContent>

        <DialogActions sx={{ p: 3, pt: 1, gap: 1 }}>
          <Button
            onClick={handleClose}
            disabled={loading}
            startIcon={<CloseIcon />}
          >
            Abbrechen
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={loading}
            startIcon={
              loading ? (
                <CircularProgress size={16} color="inherit" />
              ) : (
                <SaveIcon />
              )
            }
            sx={{ minWidth: 120 }}
          >
            {loading ? "Speichere..." : "Speichern"}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}

export default SaveRecommendationDialog;
