import React, { useState } from "react";
import {
  Box,
  Paper,
  Typography,
  Grid,
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
  // Struktur entsprechend dem Admin-Frontend (App.js)
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

  const [patientSearchResults, setPatientSearchResults] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [patientSearchLoading, setPatientSearchLoading] = useState(false);
  const [patientSearchError, setPatientSearchError] = useState(null);
  const [showPatientSearch, setShowPatientSearch] = useState(false);

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handlePatientSearchInputChange = (field, value) => {
    setPatientSearchError(null);
    setPatientSearch((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handlePatientSearch = async () => {
    setPatientSearchLoading(true);
    setPatientSearchError(null);
    setPatientSearchResults([]);

    try {
      const searchData = {
        search_type: patientSearch.searchType,
        ...(patientSearch.searchType === "id"
          ? {
              patient_id: patientSearch.patient_id,
            }
          : {
              given_name: patientSearch.given_name,
              family_name: patientSearch.family_name,
              birth_date: patientSearch.birth_date,
            }),
      };

      console.log("Patient search data:", searchData);
      const response = await patientAPI.searchPatients(searchData);
      console.log("Patient search response:", response);
      
      // Handle different response formats
      const results = response.patients || response || [];
      console.log("Patient search results:", results);
      setPatientSearchResults(results);

      if (results.length === 0) {
        setPatientSearchError("Keine Patienten gefunden");
      }
    } catch (error) {
      console.error("Patient search error:", error);
      console.error("Error response:", error.response);
      setPatientSearchError(
        error.response?.data?.detail || "Fehler bei der Patientensuche"
      );
    } finally {
      setPatientSearchLoading(false);
    }
  };

  const handleSelectPatient = (patient) => {
    setSelectedPatient(patient);
    setFormData((prev) => ({
      ...prev,
      patient_id: patient.patient_id,
    }));
    setShowPatientSearch(false);
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // Validation
    if (!formData.indication) {
      setPatientSearchError("Bitte wählen Sie eine Verdachtsdiagnose aus");
      return;
    }

    // Create payload in the same format as Admin-Frontend
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

  // Get indication label from value
  const getIndicationLabel = (value) => {
    for (const category of availableIndications) {
      const option = category.options.find((opt) => opt.value === value);
      if (option) return option.label;
    }
    return value;
  };

  return (
    <Box sx={{ width: "100%" }}>
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
                      color: formData.indication ? "text.primary" : "text.disabled",
                    },
                  }}
                >
                  {!formData.indication && (
                    <MenuItem value="" disabled sx={{ color: "text.disabled", fontStyle: "italic", display: 'none' }}>
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
                      vertical: 'bottom',
                      horizontal: 'left',
                    },
                    transformOrigin: {
                      vertical: 'top',
                      horizontal: 'left',
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
                onChange={(e) =>
                  handleInputChange("free_text", e.target.value)
                }
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
                onChange={(e) => handleInputChange("patient_id", e.target.value)}
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
                  <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
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
                        <MenuItem value="id">Nach ID</MenuItem>
                        <MenuItem value="name_birthdate">
                          Nach Name und Geburtsdatum
                        </MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>

                  {patientSearch.searchType === "id" ? (
                    <Grid item xs={12}>
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
                    </Grid>
                  ) : (
                    <>
                      <Grid item xs={12}>
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
                      </Grid>
                      <Grid item xs={12}>
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
                      </Grid>
                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          size="small"
                          label="Geburtsdatum"
                          type="date"
                          value={patientSearch.birth_date}
                          onChange={(e) =>
                            handlePatientSearchInputChange(
                              "birth_date",
                              e.target.value
                            )
                          }
                          InputLabelProps={{ shrink: true }}
                        />
                      </Grid>
                    </>
                  )}

                  <Grid item xs={12}>
                    <Button
                      fullWidth
                      variant="outlined"
                      onClick={handlePatientSearch}
                      disabled={patientSearchLoading}
                      startIcon={
                        patientSearchLoading ? (
                          <CircularProgress size={16} />
                        ) : (
                          <SearchIcon />
                        )
                      }
                    >
                      Suchen
                    </Button>
                  </Grid>

                  {patientSearchError && (
                    <Grid item xs={12}>
                      <Alert severity="warning" size="small">
                        {patientSearchError}
                      </Alert>
                    </Grid>
                  )}

                  {patientSearchResults.length > 0 && (
                    <Grid item xs={12}>
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        Gefundene Patienten:
                      </Typography>
                      {patientSearchResults.map((patient) => (
                        <Paper
                          key={patient.patient_id}
                          sx={{
                            p: 2,
                            mb: 1,
                            cursor: "pointer",
                            "&:hover": { bgcolor: "action.hover" },
                            border:
                              selectedPatient?.patient_id === patient.patient_id
                                ? 2
                                : 1,
                            borderColor:
                              selectedPatient?.patient_id === patient.patient_id
                                ? "primary.main"
                                : "divider",
                          }}
                          onClick={() => handleSelectPatient(patient)}
                        >
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {patient.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            ID: {patient.patient_id} | Geboren:{" "}
                            {patient.birth_date || "Unbekannt"}
                          </Typography>
                        </Paper>
                      ))}
                    </Grid>
                  )}
                </Grid>
              </AccordionDetails>
            </Accordion>

            {selectedPatient && (
              <Alert severity="success" sx={{ mt: 2 }}>
                Patient ausgewählt: {selectedPatient.name}
              </Alert>
            )}
          </Paper>
        </Grid>

        {/* Submit Button */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, display: "flex", justifyContent: "center" }}>
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
              sx={{ minWidth: 200, py: 1.5 }}
            >
              {loading
                ? "Analysiere Anfrage... (kann bis zu 3 Min dauern)"
                : "Therapie-Empfehlung erstellen"}
            </Button>
          </Paper>
        </Grid>
      </Grid>
    </form>
  );
}

export default TherapyRequestForm;
