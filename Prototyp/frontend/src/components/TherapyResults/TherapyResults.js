import React, { useState } from "react";
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Collapse,
} from "@mui/material";
import {
  ExpandMore as ExpandMoreIcon,
  Medication as MedicationIcon,
  Person as PersonIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  LocalHospital as HospitalIcon,
} from "@mui/icons-material";

function TherapyResults({ therapyRecommendation, patientData, requestData }) {
  const [showPatientDetails, setShowPatientDetails] = useState(false);

  if (!therapyRecommendation) {
    return null;
  }

  const formatFrequency = (activeIngredient) => {
    if (
      activeIngredient.frequency_upper_bound &&
      activeIngredient.frequency_upper_bound !==
        activeIngredient.frequency_lower_bound
    ) {
      return `${activeIngredient.frequency_lower_bound}-${activeIngredient.frequency_upper_bound}x ${activeIngredient.frequency_unit}`;
    }
    return `${activeIngredient.frequency_lower_bound}x ${activeIngredient.frequency_unit}`;
  };

  const formatDuration = (activeIngredient) => {
    if (!activeIngredient.duration_lower_bound) {
      return "Therapiedauer nicht spezifiziert";
    }

    if (
      activeIngredient.duration_upper_bound &&
      activeIngredient.duration_upper_bound !==
        activeIngredient.duration_lower_bound
    ) {
      return `${activeIngredient.duration_lower_bound}-${activeIngredient.duration_upper_bound} ${activeIngredient.duration_unit}`;
    }
    return `${activeIngredient.duration_lower_bound} ${activeIngredient.duration_unit}`;
  };

  const getIndicationDisplay = () => {
    if (requestData?.indication) {
      // Mapping from backend enum values to display names (same as backend)
      const indicationDisplayNames = {
        // Respiratory infections
        AMBULANT_ERWORBENE_PNEUMONIE: "CAP (Ambulant erworbene Pneumonie)",
        NOSOKOMIAL_ERWORBENE_PNEUMONIE: "HAP (Nosokomial erworbene Pneumonie)",
        AKUTE_EXAZERBATION_COPD: "AECOPD (Akute Exazerbation der COPD)",

        // ENT infections
        OTITIS_EXTERNA_MALIGNA: "Otitis externa maligna",
        OSTEOMYELITIS_SCHAEDELBASIS: "Osteomyelitis der Schädelbasis",
        MASTOIDITIS: "Mastoiditis",
        EPIGLOTTITIS: "Epiglottitis",
        OHRMUSCHELPERICHONDRITIS: "Ohrmuschelperichondritis",
        NASENFURUNKEL: "Nasenfurunkel",
        PERITONSILLITIS: "Peritonsillitis",
        PERITONSILLARABSZESS: "Peritonsillarabszess",
        BAKTERIELLE_SINUSITIDEN_UND_KOMPLIKATIONEN:
          "Bakterielle Sinusitiden und deren Komplikationen",
        SIALADENITIS: "Sialadenitis",
        ZERVIKOFAZIALE_AKTINOMYKOSE: "Zervikofaziale Aktinomykose",

        // Dental
        ODONTOGENE_INFEKTIONEN_AUSBREITUNGSTENDENZ:
          "Odontogene Infektionen mit Ausbreitungstendenz",
        OSTEOMYELITIS_KIEFER: "Osteomyelitis der Kiefer",

        // Abdominal infections
        PERITONITIS: "Peritonitis",
        NEKROTISIERENDE_PANKREATITIS_INFIZIERTE_NEKROSEN:
          "Nekrotisierende Pankreatitis mit infizierten Nekrosen",
        INVASIVE_INTRAABDOMINELLE_MYKOSEN: "Invasive intraabdominelle Mykosen",

        // Urogenital infections
        AKUTE_UNKOMPLIZIERTE_PYELONEPHRITIS:
          "Akute unkomplizierte Pyelonephritis",
        KOMPLIZIERTE_NOSOKOMIALE_HARNWEGSINFEKTION:
          "Komplizierte bzw. nosokomiale Harnwegsinfektion",
        UROSEPSIS: "Urosepsis",
        TUBOOVARIALABSZESS: "Tubo-ovarialer Abszess",

        // Genital infections
        ACUTE_PROSTATITIS: "Akute Prostatitis",
        EPIDIDYMITIS: "Epididymitis",
        FOURNIER_GANGRÄN: "Fournier'sche Gangrän",

        // Bone and joint infections
        AKUTE_HAEMATOGENE_OSTEOMYELITIS: "Akute hämatogene Osteomyelitis",
        CHRONISCHE_OSTEOMYELITIS: "Chronische Osteomyelitis",
        DIABETISCHES_FUSSSYNDROM_MIT_OSTEOMYELITIS:
          "Diabetisches Fußsyndrom mit Osteomyelitis",
        SPONDYLODISCITIS: "Spondylodiszitis",
        STERNUMOSTEOMYELITIS: "Sternum-Osteomyelitis",
        INFIZIERTE_ENDOPROTHESE: "Infizierte Endoprothese",
        SEPTISCHE_ARTHRITIS: "Septische Arthritis",

        // CNS infections
        AKUTE_BAKTERIELLE_MENINGITIS: "Akute bakterielle Meningitis",
        BAKTERIELLE_MENINGOENZEPHALITIS: "Bakterielle Meningoenzephalitis",
        HIRNABSZESS: "Hirnabszess",
        EPIDURAL_SUBDURAL_EMPYEM: "Epidurales/subdurales Empyem",

        // Cardiovascular infections
        AKUTE_INFEKTIOESE_ENDOKARDITIS: "Akute infektiöse Endokarditis",
        PERIKARDITIS_PURULENT: "Purulente Perikarditis",

        // Soft tissue infections
        NEKROTISIERENDE_FASZIITIS: "Nekrotisierende Fasziitis",
        SCHWERE_WEICHTEILINFEKTION: "Schwere Weichteilinfektion",

        // Other
        INVASIVE_MYKOSEN: "Invasive Mykosen",
        NEUTROPENISCHES_FIEBER: "Neutropenisches Fieber",
      };

      return (
        indicationDisplayNames[requestData.indication] ||
        requestData.indication.replace(/_/g, " ")
      );
    }
    return "Unbekannt";
  };

  const getSeverityDisplay = () => {
    const severityMap = {
      LEICHT: "Leicht",
      MITTELSCHWER: "Mittelschwer",
      SCHWER: "Schwer",
      SEPTISCH: "Septisch",
    };
    return (
      severityMap[requestData?.severity] ||
      requestData?.severity ||
      "Nicht angegeben"
    );
  };

  return (
    <Box sx={{ width: "100%" }}>
      {/* Header Summary */}
      <Paper
        sx={{
          p: 3,
          mb: 3,
          bgcolor: "primary.50",
          border: 1,
          borderColor: "primary.200",
        }}
      >
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={8}>
            <Typography
              variant="h5"
              sx={{ fontWeight: 600, color: "primary.main", mb: 1 }}
            >
              Therapie-Empfehlung
            </Typography>
            <Typography variant="body1" sx={{ mb: 1 }}>
              <strong>Indikation:</strong> {getIndicationDisplay()}
            </Typography>
            <Typography variant="body1">
              <strong>Schweregrad:</strong> {getSeverityDisplay()}
            </Typography>
          </Grid>
          <Grid
            item
            xs={12}
            md={4}
            sx={{ textAlign: { xs: "left", md: "right" } }}
          >
            <Chip
              label={`Vertrauenslevel: ${
                therapyRecommendation.confidence_level || "Unbekannt"
              }`}
              color="success"
              sx={{ mb: 1, fontWeight: 500 }}
            />
            <Typography variant="body2" color="text.secondary">
              {therapyRecommendation.therapy_options?.length || 0}{" "}
              Therapieoptionen
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Warnings */}
      {therapyRecommendation.warnings &&
        therapyRecommendation.warnings.length > 0 && (
          <Alert severity="warning" sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              Wichtige Hinweise
            </Typography>
            <List dense>
              {therapyRecommendation.warnings.map((warning, index) => (
                <ListItem key={index} sx={{ pl: 0, py: 0.5 }}>
                  <ListItemText
                    primary={warning}
                    primaryTypographyProps={{
                      color: "warning.dark",
                      fontWeight: 500,
                    }}
                  />
                </ListItem>
              ))}
            </List>
          </Alert>
        )}

      {/* Therapy Options */}
      <Typography
        variant="h6"
        sx={{ mb: 2, display: "flex", alignItems: "center", gap: 1 }}
      >
        <MedicationIcon color="primary" />
        Therapieoptionen ({therapyRecommendation.therapy_options?.length || 0})
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        {therapyRecommendation.therapy_options?.map((option, index) => (
          <Grid item xs={12} key={index}>
            <Card
              sx={{
                border: 1,
                borderColor: index === 0 ? "success.main" : "divider",
                bgcolor: index === 0 ? "success.50" : "background.paper",
              }}
            >
              <CardContent>
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    mb: 2,
                  }}
                >
                  <Typography
                    variant="h6"
                    sx={{
                      fontWeight: 600,
                      color: index === 0 ? "success.main" : "text.primary",
                    }}
                  >
                    Option {index + 1}
                    {index === 0 && (
                      <Chip
                        label="Empfohlen"
                        size="small"
                        color="success"
                        sx={{ ml: 1 }}
                      />
                    )}
                  </Typography>
                </Box>

                {/* Active Ingredients */}
                <Box sx={{ mb: 2 }}>
                  <Typography
                    variant="subtitle1"
                    sx={{ fontWeight: 500, mb: 1 }}
                  >
                    Wirkstoffe:
                  </Typography>
                  <Grid container spacing={1}>
                    {option.active_ingredients?.map((ingredient, idx) => (
                      <Grid item xs={12} key={idx}>
                        <Paper sx={{ p: 2, bgcolor: "grey.50", width: "100%" }}>
                          <Typography
                            variant="h6"
                            sx={{
                              fontWeight: 600,
                              color: "primary.main",
                              mb: 1,
                            }}
                          >
                            {ingredient.name}
                          </Typography>
                          <Box
                            sx={{ display: "flex", flexWrap: "wrap", gap: 2 }}
                          >
                            <Typography
                              variant="body2"
                              sx={{ minWidth: "150px" }}
                            >
                              <strong>Dosierung:</strong> {ingredient.strength}
                            </Typography>
                            <Typography
                              variant="body2"
                              sx={{ minWidth: "150px" }}
                            >
                              <strong>Häufigkeit:</strong>{" "}
                              {formatFrequency(ingredient)}
                            </Typography>
                            <Typography
                              variant="body2"
                              sx={{ minWidth: "150px" }}
                            >
                              <strong>Dauer:</strong>{" "}
                              {formatDuration(ingredient)}
                            </Typography>
                            <Typography
                              variant="body2"
                              sx={{ minWidth: "100px" }}
                            >
                              <strong>Applikation:</strong> {ingredient.route}
                            </Typography>
                          </Box>
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                </Box>

                {/* Notes */}
                {option.notes && (
                  <Box sx={{ mb: 2 }}>
                    <Typography
                      variant="subtitle2"
                      sx={{ fontWeight: 500, mb: 1 }}
                    >
                      Anmerkungen:
                    </Typography>
                    <Typography
                      variant="body2"
                      sx={{ bgcolor: "info.50", p: 2, borderRadius: 1 }}
                    >
                      {option.notes}
                    </Typography>
                  </Box>
                )}

                {/* Clinical Guidance */}
                {option.clinical_guidance && (
                  <Accordion>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
                        Klinische Hinweise
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Grid container spacing={2}>
                        {/* Monitoring Parameters */}
                        {option.clinical_guidance.monitoring_parameters
                          ?.length > 0 && (
                          <Grid item xs={12} md={6}>
                            <Typography
                              variant="subtitle2"
                              sx={{ fontWeight: 500, mb: 1 }}
                            >
                              <ScheduleIcon
                                sx={{
                                  verticalAlign: "middle",
                                  mr: 1,
                                  fontSize: 18,
                                }}
                              />
                              Monitoring:
                            </Typography>
                            <List dense>
                              {option.clinical_guidance.monitoring_parameters.map(
                                (param, idx) => (
                                  <ListItem key={idx} sx={{ pl: 0 }}>
                                    <ListItemIcon sx={{ minWidth: 32 }}>
                                      <CheckCircleIcon
                                        sx={{
                                          fontSize: 16,
                                          color: "success.main",
                                        }}
                                      />
                                    </ListItemIcon>
                                    <ListItemText
                                      primary={param}
                                      primaryTypographyProps={{
                                        variant: "body2",
                                      }}
                                    />
                                  </ListItem>
                                )
                              )}
                            </List>
                          </Grid>
                        )}

                        {/* Side Effects */}
                        {option.clinical_guidance.relevant_side_effects
                          ?.length > 0 && (
                          <Grid item xs={12} md={6}>
                            <Typography
                              variant="subtitle2"
                              sx={{ fontWeight: 500, mb: 1 }}
                            >
                              <WarningIcon
                                sx={{
                                  verticalAlign: "middle",
                                  mr: 1,
                                  fontSize: 18,
                                  color: "warning.main",
                                }}
                              />
                              Nebenwirkungen:
                            </Typography>
                            <List dense>
                              {option.clinical_guidance.relevant_side_effects.map(
                                (effect, idx) => (
                                  <ListItem key={idx} sx={{ pl: 0 }}>
                                    <ListItemIcon sx={{ minWidth: 32 }}>
                                      <WarningIcon
                                        sx={{
                                          fontSize: 16,
                                          color: "warning.main",
                                        }}
                                      />
                                    </ListItemIcon>
                                    <ListItemText
                                      primary={effect}
                                      primaryTypographyProps={{
                                        variant: "body2",
                                      }}
                                    />
                                  </ListItem>
                                )
                              )}
                            </List>
                          </Grid>
                        )}

                        {/* Deescalation Info */}
                        {option.clinical_guidance.deescalation_focus_info && (
                          <Grid item xs={12}>
                            <Typography
                              variant="subtitle2"
                              sx={{ fontWeight: 500, mb: 1 }}
                            >
                              <InfoIcon
                                sx={{
                                  verticalAlign: "middle",
                                  mr: 1,
                                  fontSize: 18,
                                  color: "info.main",
                                }}
                              />
                              Deeskalation:
                            </Typography>
                            <Typography
                              variant="body2"
                              sx={{ bgcolor: "info.50", p: 2, borderRadius: 1 }}
                            >
                              {option.clinical_guidance.deescalation_focus_info}
                            </Typography>
                          </Grid>
                        )}
                      </Grid>
                    </AccordionDetails>
                  </Accordion>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Therapy Rationale */}
      {therapyRecommendation.therapy_rationale && (
        <Paper sx={{ p: 3, mb: 3, bgcolor: "info.50" }}>
          <Typography
            variant="h6"
            sx={{ fontWeight: 600, mb: 2, color: "info.main" }}
          >
            <InfoIcon sx={{ verticalAlign: "middle", mr: 1 }} />
            Begründung der Therapieempfehlung
          </Typography>
          <Typography variant="body1">
            {therapyRecommendation.therapy_rationale}
          </Typography>
        </Paper>
      )}

      {/* Source Citations */}
      {therapyRecommendation.source_citations?.length > 0 && (
        <Accordion sx={{ mb: 3 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Quellenangaben ({therapyRecommendation.source_citations.length})
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            {therapyRecommendation.source_citations.map((citation, index) => (
              <Paper key={index} sx={{ p: 2, mb: 2, bgcolor: "grey.50" }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
                  {citation.guideline_title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  ID: {citation.guideline_id} | Seite: {citation.page_number} |
                  Relevanz: {(citation.relevance_score * 100).toFixed(0)}%
                </Typography>
                {citation.section && (
                  <Typography variant="body2" sx={{ mt: 0.5 }}>
                    <strong>Abschnitt:</strong> {citation.section}
                  </Typography>
                )}
              </Paper>
            ))}
          </AccordionDetails>
        </Accordion>
      )}

      {/* Patient Data */}
      {(patientData || therapyRecommendation.patient_summary) && (
        <Paper sx={{ p: 3 }}>
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              mb: 2,
            }}
          >
            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                display: "flex",
                alignItems: "center",
                gap: 1,
              }}
            >
              <PersonIcon color="primary" />
              Patientendaten
            </Typography>
            <IconButton
              onClick={() => setShowPatientDetails(!showPatientDetails)}
            >
              {showPatientDetails ? <VisibilityOffIcon /> : <VisibilityIcon />}
            </IconButton>
          </Box>

          <Collapse in={showPatientDetails}>
            {/* Show patient_summary if available */}
            {therapyRecommendation.patient_summary && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 500, mb: 1 }}>
                  Patientenübersicht:
                </Typography>
                <Box
                  sx={{
                    bgcolor: "info.50",
                    p: 2,
                    borderRadius: 1,
                    border: 1,
                    borderColor: "info.200",
                  }}
                >
                  {therapyRecommendation.patient_summary
                    .split("\n")
                    .map((line, index) => {
                      if (
                        line.startsWith("Alter:") ||
                        line.startsWith("Gewicht:")
                      ) {
                        return (
                          <Typography
                            key={index}
                            variant="body2"
                            sx={{ mb: 0.5, fontWeight: 500 }}
                          >
                            {line}
                          </Typography>
                        );
                      } else if (line.startsWith("Anamnese/Vorerkrankungen:")) {
                        return (
                          <Box key={index} sx={{ mb: 1 }}>
                            <Typography
                              variant="body2"
                              sx={{ fontWeight: 500, color: "primary.main" }}
                            >
                              Anamnese/Vorerkrankungen:
                            </Typography>
                            <Typography variant="body2" sx={{ pl: 1, mt: 0.5 }}>
                              {line
                                .replace("Anamnese/Vorerkrankungen:", "")
                                .trim()}
                            </Typography>
                          </Box>
                        );
                      } else if (line.startsWith("Allergien:")) {
                        return (
                          <Box key={index} sx={{ mb: 1 }}>
                            <Typography
                              variant="body2"
                              sx={{ fontWeight: 500, color: "warning.main" }}
                            >
                              Allergien:
                            </Typography>
                            <Typography variant="body2" sx={{ pl: 1, mt: 0.5 }}>
                              {line.replace("Allergien:", "").trim()}
                            </Typography>
                          </Box>
                        );
                      } else if (line.startsWith("Aktuelle Medikation:")) {
                        return (
                          <Box key={index} sx={{ mb: 1 }}>
                            <Typography
                              variant="body2"
                              sx={{ fontWeight: 500, color: "secondary.main" }}
                            >
                              Aktuelle Medikation:
                            </Typography>
                            <Typography variant="body2" sx={{ pl: 1, mt: 0.5 }}>
                              {line.replace("Aktuelle Medikation:", "").trim()}
                            </Typography>
                          </Box>
                        );
                      }
                      return null;
                    })
                    .filter(Boolean)}
                </Box>
              </Box>
            )}

            {patientData && (
              <Grid container spacing={2}>
                {/* Basic Patient Info */}
                <Grid item xs={12}>
                  <Typography
                    variant="subtitle2"
                    sx={{ fontWeight: 500, mb: 1 }}
                  >
                    Grunddaten:
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6} sm={3}>
                      <Typography variant="body2">
                        <strong>Name:</strong>
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {patientData.name || "Nicht verfügbar"}
                      </Typography>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Typography variant="body2">
                        <strong>ID:</strong>
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {patientData.patient_id || "Nicht verfügbar"}
                      </Typography>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Typography variant="body2">
                        <strong>Geschlecht:</strong>
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {patientData.gender || "Nicht verfügbar"}
                      </Typography>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Typography variant="body2">
                        <strong>Geburtsdatum:</strong>
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {patientData.birth_date || "Nicht verfügbar"}
                      </Typography>
                    </Grid>
                  </Grid>
                </Grid>
              </Grid>
            )}
          </Collapse>
        </Paper>
      )}
    </Box>
  );
}

export default TherapyResults;
