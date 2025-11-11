import React, { useState } from "react";
import {
  Box,
  Paper,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  OutlinedInput,
  Button,
  Divider,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from "@mui/material";
import {
  ExpandMore as ExpandMoreIcon,
  Search as SearchIcon,
  Person as PersonIcon,
} from "@mui/icons-material";
import {
  availableIndications,
  severityOptions,
  riskFactorOptions,
  patientAPI,
} from "../../services/api";

function TherapyRequestForm({ onSubmit, loading }) {
  // Form state
  const [formData, setFormData] = useState({
    indication: "",
    severity: "MITTELSCHWER",
    infection_site: null,
    risk_factors: [],
    suspected_pathogens: "",
    free_text: "",
    patient_id: "",
    max_therapy_options: 5,
  });

  const [patientSearch, setPatientSearch] = useState({
    searchType: "id",
    patient_id: "",
    given_name: "",
    family_name: "",
    birth_date: "",
  });

  const [showPatientSearch, setShowPatientSearch] = useState(false);
  const [patientSearchLoading, setPatientSearchLoading] = useState(false);
  const [patientSearchResults, setPatientSearchResults] = useState([]);
  const [patientSearchError, setPatientSearchError] = useState(null);
  const [selectedPatient, setSelectedPatient] = useState(null);

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handlePatientSearchInputChange = (field, value) => {
    setPatientSearch((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handlePatientSearch = async () => {
    if (!patientSearch.searchType) {
      setPatientSearchError("Bitte wählen Sie einen Suchtyp aus");
      return;
    }

    if (patientSearch.searchType === "id" && !patientSearch.patient_id) {
      setPatientSearchError("Bitte geben Sie eine Patienten-ID ein");
      return;
    }

    if (
      patientSearch.searchType === "name_birthdate" &&
      (!patientSearch.given_name ||
        !patientSearch.family_name ||
        !patientSearch.birth_date)
    ) {
      setPatientSearchError(
        "Bitte geben Sie Vor-, Nachname und Geburtsdatum ein"
      );
      return;
    }

    setPatientSearchLoading(true);
    setPatientSearchError(null);
    setPatientSearchResults([]);

    try {
      console.log("Searching for patient with:", patientSearch);

      const searchParams = {
        search_type: patientSearch.searchType,
        ...(patientSearch.searchType === "id"
          ? { patient_id: patientSearch.patient_id }
          : {
              given_name: patientSearch.given_name,
              family_name: patientSearch.family_name,
              birth_date: patientSearch.birth_date,
            }),
      };

      console.log("Sending search params:", searchParams);
      const response = await patientAPI.searchPatients(searchParams);
      console.log("Patient search response:", response);

      // Handle different response formats
      const patients = response.patients || response || [];
      console.log("Extracted patients:", patients);

      if (patients.length === 0) {
        setPatientSearchError("Keine Patienten gefunden");
      } else {
        setPatientSearchResults(patients);
      }
    } catch (error) {
      console.error("Patient search error:", error);
      console.error("Response data:", error.response?.data);
      console.error("Response status:", error.response?.status);

      let errorMessage =
        "Fehler bei der Patientensuche. Bitte versuchen Sie es erneut.";

      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        if (typeof detail === "string") {
          errorMessage = detail;
        } else if (Array.isArray(detail)) {
          errorMessage = detail.map((d) => d.msg || d).join(", ");
        } else if (detail.msg) {
          errorMessage = detail.msg;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }

      setPatientSearchError(errorMessage);
    } finally {
      setPatientSearchLoading(false);
    }
  };

  const handlePatientSelect = (patient) => {
    console.log("Selected patient:", patient);
    setSelectedPatient(patient);
    setFormData((prev) => ({
      ...prev,
      patient_id: patient.patient_id,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const therapyPayload = {
      indication: formData.indication,
      severity: formData.severity,
      infection_site: formData.infection_site || null,
      risk_factors: formData.risk_factors.map((factor) => factor),
      suspected_pathogens: formData.suspected_pathogens
        ? formData.suspected_pathogens
            .split(",")
            .map((s) => s.trim())
            .filter((s) => s)
        : [],
      free_text: formData.free_text || null,
      patient_id: formData.patient_id || null,
      max_therapy_options: 5,
    };

    console.log("Submitting therapy payload:", therapyPayload);
    onSubmit(therapyPayload);
  };

  return (
    <Box sx={{ width: "100%", maxWidth: "1200px", mx: "auto" }}>
      <form onSubmit={handleSubmit}>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
          {/* 1. Klinische Parameter - Vollbreite Box */}
          <Paper sx={{ p: 3, width: "100%" }}>
            <Typography
              variant="h6"
              gutterBottom
              sx={{ display: "flex", alignItems: "center", gap: 1, mb: 3 }}
            >
              <SearchIcon color="primary" />
              Klinische Parameter
            </Typography>

            <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
              {/* Verdachtsdiagnose */}
              <FormControl fullWidth required>
                <InputLabel>Verdachtsdiagnose</InputLabel>
                <Select
                  value={formData.indication}
                  onChange={(e) =>
                    handleInputChange("indication", e.target.value)
                  }
                  label="Verdachtsdiagnose"
                  sx={{
                    "& .MuiSelect-select": {
                      color: formData.indication
                        ? "text.primary"
                        : "text.disabled",
                    },
                  }}
                >
                  {!formData.indication && (
                    <MenuItem
                      value=""
                      disabled
                      sx={{
                        color: "text.disabled",
                        fontStyle: "italic",
                        display: "none",
                      }}
                    >
                      Bitte wählen Sie eine Verdachtsdiagnose aus
                    </MenuItem>
                  )}
                  {availableIndications.map((category) => [
                    <MenuItem
                      key={category.category}
                      disabled
                      sx={{ fontWeight: 600, bgcolor: "grey.100" }}
                    >
                      {category.category}
                    </MenuItem>,
                    ...category.options.map((option) => (
                      <MenuItem
                        key={option.value}
                        value={option.value}
                        sx={{ pl: 3 }}
                      >
                        {option.label}
                      </MenuItem>
                    )),
                  ])}
                </Select>
              </FormControl>

              {/* Schweregrad */}
              <FormControl fullWidth>
                <InputLabel>Schweregrad</InputLabel>
                <Select
                  value={formData.severity}
                  onChange={(e) =>
                    handleInputChange("severity", e.target.value)
                  }
                  label="Schweregrad"
                >
                  {severityOptions.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Risikofaktoren */}
              <FormControl fullWidth>
                <InputLabel>Risikofaktoren</InputLabel>
                <Select
                  multiple
                  value={formData.risk_factors}
                  onChange={(e) =>
                    handleInputChange("risk_factors", e.target.value)
                  }
                  input={<OutlinedInput label="Risikofaktoren" />}
                  renderValue={(selected) => (
                    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                      {selected.map((value) => {
                        const option = riskFactorOptions.find(
                          (opt) => opt.value === value
                        );
                        return (
                          <Chip
                            key={value}
                            label={option?.label || value}
                            size="small"
                          />
                        );
                      })}
                    </Box>
                  )}
                  MenuProps={{
                    PaperProps: {
                      style: {
                        maxHeight: 300,
                        minWidth: 450,
                        width: "auto",
                      },
                    },
                    anchorOrigin: {
                      vertical: "bottom",
                      horizontal: "left",
                    },
                    transformOrigin: {
                      vertical: "top",
                      horizontal: "left",
                    },
                  }}
                >
                  {riskFactorOptions.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Verdachtskeime */}
              <TextField
                fullWidth
                label="Verdachtskeime (optional)"
                multiline
                rows={2}
                value={formData.suspected_pathogens}
                onChange={(e) =>
                  handleInputChange("suspected_pathogens", e.target.value)
                }
                placeholder="z.B. MRSA, E. coli, Pseudomonas..."
                InputProps={{
                  sx: {
                    "& input::placeholder": {
                      color: "text.secondary",
                      opacity: 0.7,
                    },
                    "& textarea::placeholder": {
                      color: "text.secondary",
                      opacity: 0.7,
                    },
                  },
                }}
              />

              {/* Zusätzliche Informationen */}
              <TextField
                fullWidth
                label="Zusätzliche Informationen (optional)"
                multiline
                rows={3}
                value={formData.free_text}
                onChange={(e) => handleInputChange("free_text", e.target.value)}
                placeholder="Weitere relevante Informationen zur Infektion, Vorerkrankungen, Allergien..."
                InputProps={{
                  sx: {
                    "& textarea::placeholder": {
                      color: "text.secondary",
                      opacity: 0.7,
                    },
                  },
                }}
              />
            </Box>
          </Paper>

          {/* 2. Patienteninformationen - Vollbreite Box */}
          <Paper sx={{ p: 3, width: "100%" }}>
            <Typography
              variant="h6"
              gutterBottom
              sx={{ display: "flex", alignItems: "center", gap: 1, mb: 3 }}
            >
              <PersonIcon color="primary" />
              Patienteninformationen
            </Typography>

            <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
              {/* Einfache Patienten-ID Eingabe */}
              <TextField
                fullWidth
                label="Patienten-ID"
                value={formData.patient_id}
                onChange={(e) =>
                  handleInputChange("patient_id", e.target.value)
                }
                placeholder="z.B. 12345"
                InputProps={{
                  sx: {
                    "& input::placeholder": {
                      color: "text.secondary",
                      opacity: 0.7,
                    },
                  },
                }}
              />

              <Divider sx={{ my: 1 }}>oder</Divider>

              {/* Erweiterte Patientensuche */}
              <Accordion
                expanded={showPatientSearch}
                onChange={(e, expanded) => setShowPatientSearch(expanded)}
                sx={{ width: "100%" }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="body2">
                    Erweiterte Patientensuche
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box
                    sx={{ display: "flex", flexDirection: "column", gap: 2 }}
                  >
                    {/* Suchtyp auswählen */}
                    <FormControl fullWidth size="small">
                      <InputLabel>Suchtyp</InputLabel>
                      <Select
                        value={patientSearch.searchType}
                        onChange={(e) =>
                          handlePatientSearchInputChange(
                            "searchType",
                            e.target.value
                          )
                        }
                        label="Suchtyp"
                      >
                        <MenuItem value="id">Nach Patienten-ID</MenuItem>
                        <MenuItem value="name_birthdate">
                          Nach Name und Geburtsdatum
                        </MenuItem>
                      </Select>
                    </FormControl>

                    {/* Eingabefelder basierend auf Suchtyp */}
                    {patientSearch.searchType === "id" ? (
                      <TextField
                        fullWidth
                        size="small"
                        label="Patienten-ID"
                        value={patientSearch.patient_id}
                        onChange={(e) =>
                          handlePatientSearchInputChange(
                            "patient_id",
                            e.target.value
                          )
                        }
                      />
                    ) : (
                      <>
                        <TextField
                          fullWidth
                          size="small"
                          label="Vorname"
                          value={patientSearch.given_name}
                          onChange={(e) =>
                            handlePatientSearchInputChange(
                              "given_name",
                              e.target.value
                            )
                          }
                        />
                        <TextField
                          fullWidth
                          size="small"
                          label="Nachname"
                          value={patientSearch.family_name}
                          onChange={(e) =>
                            handlePatientSearchInputChange(
                              "family_name",
                              e.target.value
                            )
                          }
                        />
                        <TextField
                          fullWidth
                          size="small"
                          label="Geburtsdatum (YYYY-MM-DD)"
                          type="date"
                          InputLabelProps={{ shrink: true }}
                          value={patientSearch.birth_date}
                          onChange={(e) =>
                            handlePatientSearchInputChange(
                              "birth_date",
                              e.target.value
                            )
                          }
                        />
                      </>
                    )}

                    {/* Such-Button */}
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={handlePatientSearch}
                      disabled={patientSearchLoading}
                      fullWidth
                      sx={{ mt: 1 }}
                    >
                      {patientSearchLoading ? (
                        <CircularProgress size={16} color="inherit" />
                      ) : (
                        "Patient suchen"
                      )}
                    </Button>

                    {/* Suchergebnisse */}
                    {patientSearchResults.length > 0 && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Gefundene Patienten:
                        </Typography>
                        {patientSearchResults.map((patient) => (
                          <Box
                            key={patient.patient_id}
                            sx={{
                              p: 1,
                              border: 1,
                              borderColor: "divider",
                              borderRadius: 1,
                              mb: 1,
                              cursor: "pointer",
                              bgcolor:
                                selectedPatient?.patient_id ===
                                patient.patient_id
                                  ? "primary.50"
                                  : "transparent",
                              "&:hover": {
                                bgcolor: "action.hover",
                              },
                            }}
                            onClick={() => handlePatientSelect(patient)}
                          >
                            <Typography variant="body2" fontWeight="medium">
                              {patient.name}
                            </Typography>
                            <Typography
                              variant="caption"
                              color="text.secondary"
                            >
                              ID: {patient.patient_id} | Geschlecht:{" "}
                              {patient.gender}
                              {patient.birth_date &&
                                ` | Geboren: ${patient.birth_date}`}
                              {patient.age && ` | Alter: ${patient.age} Jahre`}
                            </Typography>
                          </Box>
                        ))}
                      </Box>
                    )}

                    {/* Fehlerbehandlung */}
                    {patientSearchError && (
                      <Alert severity="warning" size="small">
                        {patientSearchError}
                      </Alert>
                    )}
                  </Box>
                </AccordionDetails>
              </Accordion>

              {/* Ausgewählter Patient anzeigen */}
              {selectedPatient && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  Patient ausgewählt: {selectedPatient.name}
                </Alert>
              )}
            </Box>
          </Paper>

          {/* 3. Submit Button - Vollbreite Box */}
          <Paper sx={{ p: 3, width: "100%", textAlign: "center" }}>
            <Button
              type="submit"
              variant="contained"
              size="large"
              disabled={loading || !formData.indication}
              startIcon={
                loading ? (
                  <CircularProgress size={16} color="inherit" />
                ) : (
                  <SearchIcon />
                )
              }
              sx={{ minWidth: 250, py: 1.5 }}
            >
              {loading
                ? "Analysiere Anfrage... (kann bis zu 3 Min dauern)"
                : "Therapie-Empfehlung erstellen"}
            </Button>
          </Paper>
        </Box>
      </form>
    </Box>
  );
}

export default TherapyRequestForm;
