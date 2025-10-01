import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

const API_BASE =
  process.env.NODE_ENV === "production" ? "" : "http://localhost:8000";

// Helper functions for date conversion
const convertToAmericanDate = (europeanDate) => {
  // Convert DD.MM.YYYY or DD/MM/YYYY to YYYY-MM-DD
  if (!europeanDate) return "";

  // Handle different separators
  let parts;
  if (europeanDate.includes(".")) {
    parts = europeanDate.split(".");
  } else if (europeanDate.includes("/")) {
    parts = europeanDate.split("/");
  } else if (europeanDate.includes("-") && europeanDate.length === 10) {
    // Already in YYYY-MM-DD format
    return europeanDate;
  } else {
    return europeanDate; // Return as-is if format not recognized
  }

  if (parts.length === 3) {
    const day = parts[0].padStart(2, "0");
    const month = parts[1].padStart(2, "0");
    const year = parts[2];
    return `${year}-${month}-${day}`;
  }

  return europeanDate;
};

const convertToEuropeanDate = (americanDate) => {
  // Convert YYYY-MM-DD to DD.MM.YYYY
  if (!americanDate) return "";

  const parts = americanDate.split("-");
  if (parts.length === 3) {
    const year = parts[0];
    const month = parts[1];
    const day = parts[2];
    return `${day}.${month}.${year}`;
  }

  return americanDate;
};

function App() {
  const [activeTab, setActiveTab] = useState("upload");
  const [uploadStatus, setUploadStatus] = useState(null);
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [guidelinesExpanded, setGuidelinesExpanded] = useState(false);
  const [guidelines, setGuidelines] = useState([]);
  const [deleteStatus, setDeleteStatus] = useState(null);
  const [queryTestResults, setQueryTestResults] = useState(null);

  const createStatus = (type, message) => ({ type, message });

  const getAlertClass = (status) => {
    if (!status) return "";
    switch (status.type) {
      case "error":
        return "alert-danger";
      case "warning":
        return "alert-warning";
      case "info":
        return "alert-info";
      default:
        return "alert-success";
    }
  };

  // Patient search states
  const [patientSearchType, setPatientSearchType] = useState("id"); // "id" or "name_birthdate"
  const [patientSearchForm, setPatientSearchForm] = useState({
    patient_id: "",
    given_name: "",
    family_name: "",
    birth_date: "",
  });
  const [patientSearchResults, setPatientSearchResults] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [patientSearchLoading, setPatientSearchLoading] = useState(false);
  const [patientDetailsLoading, setPatientDetailsLoading] = useState(false);

  // Available indications - organized by category for better UX
  const availableIndicationOptions = [
    // Respiratorische Infektionen
    {
      category: "Respiratorische Infektionen",
      options: [
        { value: "CAP", label: "CAP (Ambulant erworbene Pneumonie)" },
        { value: "HAP", label: "HAP (Nosokomial erworbene Pneumonie)" },
        {
          value: "AKUTE_EXAZERBATION_COPD",
          label: "AECOPD (Akute Exazerbation der COPD)",
        },
      ],
    },
    // HNO-Infektionen
    {
      category: "HNO-Infektionen",
      options: [
        { value: "OTITIS_EXTERNA_MALIGNA", label: "Otitis externa maligna" },
        {
          value: "OSTEOMYELITIS_SCHAEDELBASIS",
          label: "Osteomyelitis der Schädelbasis",
        },
        { value: "MASTOIDITIS", label: "Mastoiditis" },
        { value: "EPIGLOTTITIS", label: "Epiglottitis" },
        {
          value: "OHRMUSCHELPERICHONDRITIS",
          label: "Ohrmuschelperichondritis",
        },
        { value: "NASENFURUNKEL", label: "Nasenfurunkel" },
        { value: "PERITONSILLITIS", label: "Peritonsillitis" },
        { value: "PERITONSILLARABSZESS", label: "Peritonsillarabszess" },
        {
          value: "BAKTERIELLE_SINUSITIDEN_UND_KOMPLIKATIONEN",
          label: "Bakterielle Sinusitiden und deren Komplikationen",
        },
        { value: "SIALADENITIS", label: "Sialadenitis" },
        {
          value: "ZERVIKOFAZIALE_AKTINOMYKOSE",
          label: "Zervikofaziale Aktinomykose",
        },
      ],
    },
    // Dentale Infektionen
    {
      category: "Dentale Infektionen",
      options: [
        {
          value: "ODONTOGENE_INFEKTIONEN_AUSBREITUNGSTENDENZ",
          label: "Odontogene Infektionen mit Ausbreitungstendenz",
        },
        { value: "OSTEOMYELITIS_KIEFER", label: "Osteomyelitis der Kiefer" },
      ],
    },
    // Abdominale Infektionen
    {
      category: "Abdominale Infektionen",
      options: [
        { value: "PERITONITIS", label: "Peritonitis" },
        {
          value: "NEKROTISIERENDE_PANKREATITIS_INFIZIERTE_NEKROSEN",
          label: "Nekrotisierende Pankreatitis mit infizierten Nekrosen",
        },
        {
          value: "INVASIVE_INTRAABDOMINELLE_MYKOSEN",
          label: "Invasive intraabdominelle Mykosen",
        },
      ],
    },
    // Urogenitale Infektionen
    {
      category: "Urogenitale Infektionen",
      options: [
        {
          value: "AKUTE_UNKOMPLIZIERTE_PYELONEPHRITIS",
          label: "Akute unkomplizierte Pyelonephritis",
        },
        {
          value: "KOMPLIZIERTE_NOSOKOMIALE_HARNWEGSINFEKTION",
          label: "Komplizierte bzw. nosokomiale Harnwegsinfektion",
        },
        { value: "UROSEPSIS", label: "Urosepsis" },
        { value: "AKUTE_PROSTATITIS", label: "Akute Prostatitis" },
        { value: "PROSTATAABSZESS", label: "Prostataabszess" },
        { value: "AKUTE_EPIDIDYMITIS", label: "Akute Epididymitis" },
        { value: "EPIDIDYMOORCHITIS", label: "Epididymoorchitis" },
        { value: "ENDOMETRITIS", label: "Endometritis" },
        { value: "SALPINGITIS", label: "Salpingitis" },
        { value: "TUBOOVARIALABSZESS", label: "Tuboovarialabszess" },
        { value: "PELVEOPERITONITIS", label: "Pelveoperitonitis" },
      ],
    },
    // Haut- und Weichteilinfektionen
    {
      category: "Haut- und Weichteilinfektionen",
      options: [
        { value: "INFIZIERTE_BISSWUNDEN", label: "Infizierte Bisswunden" },
      ],
    },
    // Knochen- und Gelenkinfektionen
    {
      category: "Knochen- und Gelenkinfektionen",
      options: [
        {
          value: "HAEMATOGENE_OSTEOMYELITIS",
          label: "Hämatogene Osteomyelitis",
        },
        { value: "SPONDYLODISCITIS", label: "Spondylodiscitis" },
        {
          value: "POSTTRAUMATISCHE_POSTOPERATIVE_OSTEOMYELITIS",
          label: "Posttraumatische/postoperative Osteomyelitis",
        },
        { value: "STERNUMOSTEOMYELITIS", label: "Sternumosteomyelitis" },
        { value: "BAKTERIELLE_ARTHRITIS", label: "Bakterielle Arthritis" },
        {
          value: "ENDOPROTHESEN_FREMDKOERPER_ASSOZIIERTE_INFEKTIONEN",
          label: "Endoprothesen-/Fremdkörper-assoziierte Infektionen",
        },
      ],
    },
    // Systemische Infektionen
    {
      category: "Systemische Infektionen",
      options: [
        { value: "SEPSIS", label: "Sepsis" },
        {
          value: "BAKTERIELLE_ENDOKARDITIS",
          label: "Bakterielle Endokarditis",
        },
        { value: "BAKTERIELLE_MENINGITIS", label: "Bakterielle Meningitis" },
      ],
    },
    // Gastrointestinale Infektionen
    {
      category: "Gastrointestinale Infektionen",
      options: [
        {
          value: "BAKTERIELLE_GASTROINTESTINALE_INFEKTIONEN",
          label: "Bakterielle gastrointestinale Infektionen",
        },
      ],
    },
  ];

  // Flatten options for easier access
  const allIndicationOptions = availableIndicationOptions.flatMap(
    (group) => group.options
  );

  // Therapy recommendation states
  const [therapyForm, setTherapyForm] = useState({
    indication: "CAP", // Use a valid frontend value that gets mapped to backend
    severity: "MITTELSCHWER",
    infection_site: "",
    risk_factors: [],
    suspected_pathogens: "",
    free_text: "",
    patient_id: "",
  });
  const [therapyResults, setTherapyResults] = useState(null);

  // LLM Configuration states
  const [llmConfig, setLlmConfig] = useState({
    endpoint: "https://api.novita.ai/v3/openai/chat/completions",
    model: "openai/gpt-oss-120b",
    max_tokens: 32000,
    temperature: 0.6,
  });
  const [llmConfigSaved, setLlmConfigSaved] = useState(false);
  const [therapyLoading, setTherapyLoading] = useState(false);
  const [llmDebugExpanded, setLlmDebugExpanded] = useState(false);

  // Form states
  const [uploadFile, setUploadFile] = useState(null);
  const [guidelineId, setGuidelineId] = useState("");
  const [selectedIndications, setSelectedIndications] = useState([]); // Für Upload - keine Vorauswahl
  const [indicationSearch, setIndicationSearch] = useState("");
  const [indicationDropdownOpen, setIndicationDropdownOpen] = useState(false);
  const [searchForm, setSearchForm] = useState({
    indication: "OTITIS_EXTERNA_MALIGNA", // Use a valid indication value from the backend
    severity: "MITTELSCHWER",
    infection_site: "",
    risk_factors: [],
    suspected_pathogens: "",
    free_text: "",
  });

  useEffect(() => {
    loadStats();
    loadGuidelines();
    loadLlmConfig(); // Load current LLM configuration

    // Close dropdown when clicking outside
    const handleClickOutside = (event) => {
      if (!event.target.closest(".position-relative")) {
        setIndicationDropdownOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Debug: Monitor selectedIndications changes
  useEffect(() => {
    console.log("selectedIndications changed:", selectedIndications);
  }, [selectedIndications]);

  const loadStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/stats`);
      setStats(response.data);
    } catch (error) {
      console.error("Error loading stats:", error);
    }
  };

  const loadGuidelines = async () => {
    try {
      const response = await axios.get(`${API_BASE}/guidelines`);
      if (response.data.success) {
        setGuidelines(response.data.guidelines);
      }
    } catch (error) {
      console.error("Error loading guidelines:", error);
      setDeleteStatus(
        createStatus("error", "Fehler beim Laden der Leitlinien.")
      );
    }
  };

  const deleteGuideline = async (guidelineId) => {
    if (
      !window.confirm(
        `Sicher, dass Sie die Leitlinie "${guidelineId}" löschen möchten?`
      )
    ) {
      return;
    }

    try {
      setLoading(true);
      setDeleteStatus(null);
      const response = await axios.delete(
        `${API_BASE}/guidelines/${guidelineId}`
      );

      if (response.data.success) {
        setDeleteStatus(createStatus("success", response.data.message));
        loadGuidelines();
        loadStats();
      } else {
        setDeleteStatus(createStatus("error", response.data.message));
      }
    } catch (error) {
      setDeleteStatus(
        createStatus("error", `Fehler beim Löschen: ${error.message}`)
      );
    } finally {
      setLoading(false);
    }
  };

  const deleteAllGuidelines = async () => {
    if (
      !window.confirm(
        "ACHTUNG: Sollen ALLE Leitlinien und Embeddings gelöscht werden? Diese Aktion kann nicht rückgängig gemacht werden!"
      )
    ) {
      return;
    }

    try {
      setLoading(true);
      setDeleteStatus(null);
      const response = await axios.delete(`${API_BASE}/guidelines`);

      if (response.data.success) {
        setDeleteStatus(createStatus("success", response.data.message));
        setGuidelines([]);
        loadStats();
      } else {
        setDeleteStatus(createStatus("error", response.data.message));
      }
    } catch (error) {
      setDeleteStatus(
        createStatus("error", `Fehler beim Löschen: ${error.message}`)
      );
    } finally {
      setLoading(false);
    }
  };

  const testQueryGeneration = async (e) => {
    e.preventDefault();
    setLoading(true);
    setQueryTestResults(null);

    // Map form values to backend format
    const testPayload = {
      indication: searchForm.indication, // Use the actual selected indication value
      severity: searchForm.severity,
      infection_site: searchForm.infection_site || null,
      risk_factors: searchForm.risk_factors.map((factor) => factor),
      suspected_pathogens: searchForm.suspected_pathogens
        ? searchForm.suspected_pathogens
            .split(",")
            .map((s) => s.trim())
            .filter((s) => s)
        : [],
      free_text: searchForm.free_text || null,
    };

    try {
      const response = await axios.post(`${API_BASE}/test-query`, testPayload);
      setQueryTestResults(response.data);
    } catch (error) {
      setQueryTestResults({
        status: "error",
        message: error.response?.data?.detail || error.message,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleIndicationChange = (indication, checked) => {
    console.log("handleIndicationChange called:", { indication, checked });
    if (checked) {
      const newSelection = [...selectedIndications, indication];
      console.log("Adding indication, new selection:", newSelection);
      setSelectedIndications(newSelection);
    } else {
      const newSelection = selectedIndications.filter(
        (ind) => ind !== indication
      );
      console.log("Removing indication, new selection:", newSelection);
      setSelectedIndications(newSelection);
    }
  };

  const resetUploadForm = () => {
    setUploadFile(null);
    setGuidelineId("");
    setSelectedIndications([]); // Keine Vorauswahl nach Reset
    setIndicationSearch(""); // Auch die Suchleiste zurücksetzen
    setIndicationDropdownOpen(false); // Dropdown schließen
  };

  // Patient search functions
  const handlePatientSearch = async (e) => {
    e.preventDefault();
    setPatientSearchLoading(true);
    setPatientSearchResults([]);
    setSelectedPatient(null);

    try {
      const searchPayload = {
        search_type: patientSearchType,
        ...(patientSearchType === "id"
          ? { patient_id: patientSearchForm.patient_id }
          : {
              given_name: patientSearchForm.given_name,
              family_name: patientSearchForm.family_name,
              birth_date: convertToAmericanDate(patientSearchForm.birth_date),
            }),
      };

      const response = await axios.post(
        `${API_BASE}/patients/search`,
        searchPayload
      );

      if (response.data.success) {
        setPatientSearchResults(response.data.patients);
        if (response.data.patients.length === 0) {
          alert("Keine Patienten gefunden.");
        }
      } else {
        alert(`Fehler bei der Patientensuche: ${response.data.message}`);
      }
    } catch (error) {
      console.error("Patient search error:", error);
      alert(
        `Fehler bei der Patientensuche: ${
          error.response?.data?.detail || error.message
        }`
      );
    } finally {
      setPatientSearchLoading(false);
    }
  };

  const handlePatientSelect = async (patientId) => {
    setPatientDetailsLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/patients/${patientId}`);

      if (response.data.success) {
        setSelectedPatient(response.data.patient);
      } else {
        alert(`Fehler beim Laden der Patientendaten: ${response.data.message}`);
      }
    } catch (error) {
      console.error("Patient details error:", error);
      alert(
        `Fehler beim Laden der Patientendaten: ${
          error.response?.data?.detail || error.message
        }`
      );
    } finally {
      setPatientDetailsLoading(false);
    }
  };

  const resetPatientSearch = () => {
    setPatientSearchForm({
      patient_id: "",
      given_name: "",
      family_name: "",
      birth_date: "",
    });
    setPatientSearchResults([]);
    setSelectedPatient(null);
    setPatientDetailsLoading(false);
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) {
      setUploadStatus(
        createStatus("warning", "Bitte wählen Sie eine Datei aus.")
      );
      return;
    }

    // Validate indications
    if (selectedIndications.length === 0) {
      setUploadStatus(
        createStatus(
          "warning",
          "Bitte wählen Sie mindestens eine Indikation aus."
        )
      );
      return;
    }

    console.log("Selected indications:", selectedIndications);

    // Validate file type
    const fileName = uploadFile.name.toLowerCase();
    if (!fileName.endsWith(".txt") && !fileName.endsWith(".md")) {
      setUploadStatus(
        createStatus(
          "error",
          "Nur Dateien im .txt- oder .md-Format werden unterstützt."
        )
      );
      return;
    }

    setLoading(true);
    setUploadStatus(null);

    const formData = new FormData();
    formData.append("file", uploadFile);
    if (guidelineId) {
      formData.append("guideline_id", guidelineId);
    }
    // Use selected indications instead of hardcoded values
    const indicationsString = selectedIndications.join(",");
    console.log("Sending indications string:", indicationsString);
    formData.append("indications", indicationsString);

    try {
      const response = await axios.post(
        `${API_BASE}/upload/guideline`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      if (response.data.status === "success") {
        const fileType = response.data.file_type || "unbekannt";
        const message = `Erfolgreich verarbeitet (${fileType}): ${response.data.chunks_created} Chunks erstellt.`;
        setUploadStatus(createStatus("success", message));
        resetUploadForm(); // Use new reset function
        loadStats(); // Reload stats
        loadGuidelines(); // Reload guidelines list
      } else {
        setUploadStatus(
          createStatus("error", `Fehler: ${response.data.message}`)
        );
      }
    } catch (error) {
      setUploadStatus(
        createStatus(
          "error",
          `Upload-Fehler: ${error.response?.data?.detail || error.message}`
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setSearchResults(null);

    // Map frontend values to backend enum values
    const mapIndication = (indication) => {
      // Most indications have the same value in frontend and backend
      // Only special cases need explicit mapping
      const mapping = {
        CAP: "AMBULANT_ERWORBENE_PNEUMONIE",
        HAP: "NOSOKOMIAL_ERWORBENE_PNEUMONIE",
        AKUTE_EXAZERBATION_COPD: "AKUTE_EXAZERBATION_COPD", // Already matches
      };
      return mapping[indication] || indication; // Return as-is for new indications
    };

    const mapSeverity = (severity) => {
      // Backend expects these exact values
      return severity; // Already correct: LEICHT, MITTELSCHWER, SCHWER, SEPTISCH
    };

    const mapRiskFactors = (factors) => {
      const mapping = {
        ANTIBIOTISCHE_VORBEHANDLUNG: "ANTIBIOTISCHE_VORBEHANDLUNG",
        MRGN_VERDACHT: "MRGN_VERDACHT",
        MRSA_VERDACHT: "MRSA_VERDACHT",
        BEATMUNG: "BEATMUNG",
        KATHETER: "KATHETER",
      };
      return factors.map((factor) => mapping[factor] || factor);
    };

    const mapInfectionSite = (site) => {
      if (!site) return null;
      const mapping = {
        LUNGE: "LUNGE",
        BLUT: "BLUT",
        HARNTRAKT: "HARNTRAKT",
        ZNS: "ZNS",
        HAUT_WEICHTEILE: "HAUT_WEICHTEILE",
        GASTROINTESTINAL: "GASTROINTESTINAL",
        SYSTEMISCH: "SYSTEMISCH",
      };
      return mapping[site] || site;
    };

    // Prepare search payload with correct backend enum values
    const searchPayload = {
      indication: mapIndication(searchForm.indication),
      severity: mapSeverity(searchForm.severity),
      infection_site: mapInfectionSite(searchForm.infection_site),
      risk_factors: mapRiskFactors(searchForm.risk_factors),
      suspected_pathogens: searchForm.suspected_pathogens
        ? searchForm.suspected_pathogens
            .split(",")
            .map((s) => s.trim())
            .filter((s) => s)
        : [],
      free_text: searchForm.free_text || null,
    };

    try {
      console.log("Sending search payload:", searchPayload); // Debug log
      const response = await axios.post(`${API_BASE}/search`, searchPayload);
      setSearchResults(response.data);
    } catch (error) {
      console.error("Search error:", error);
      console.error("Error response:", error.response?.data); // Debug log

      // Better error handling for validation errors
      let errorMessage = error.message;
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          // Pydantic validation errors
          errorMessage = error.response.data.detail
            .map((err) => `${err.loc.join(".")}: ${err.msg}`)
            .join("; ");
        } else {
          errorMessage = error.response.data.detail;
        }
      }

      setSearchResults({
        error: errorMessage,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRiskFactorChange = (factor, checked) => {
    setSearchForm((prev) => ({
      ...prev,
      risk_factors: checked
        ? [...prev.risk_factors, factor]
        : prev.risk_factors.filter((f) => f !== factor),
    }));
  };

  // Therapy recommendation functions
  const handleTherapyRiskFactorChange = (factor, checked) => {
    setTherapyForm((prev) => ({
      ...prev,
      risk_factors: checked
        ? [...prev.risk_factors, factor]
        : prev.risk_factors.filter((f) => f !== factor),
    }));
  };

  const handleTherapyRecommendation = async (e) => {
    e.preventDefault();
    setTherapyLoading(true);
    setTherapyResults(null);

    // Map frontend values to backend enum values
    const mapIndication = (indication) => {
      // Most indications have the same value in frontend and backend
      // Only special cases need explicit mapping
      const mapping = {
        CAP: "AMBULANT_ERWORBENE_PNEUMONIE",
        HAP: "NOSOKOMIAL_ERWORBENE_PNEUMONIE",
        AKUTE_EXAZERBATION_COPD: "AKUTE_EXAZERBATION_COPD", // Already matches
      };
      return mapping[indication] || indication; // Return as-is for new indications
    };

    // Map form values to backend format
    const therapyPayload = {
      indication: mapIndication(therapyForm.indication), // Use the mapping function
      severity: therapyForm.severity,
      infection_site: therapyForm.infection_site || null,
      risk_factors: therapyForm.risk_factors.map((factor) => factor),
      suspected_pathogens: therapyForm.suspected_pathogens
        ? therapyForm.suspected_pathogens
            .split(",")
            .map((s) => s.trim())
            .filter((s) => s)
        : [],
      free_text: therapyForm.free_text || null,
      patient_id: therapyForm.patient_id || null,
    };

    try {
      console.log("Sending therapy recommendation payload:", therapyPayload);
      const response = await axios.post(
        `${API_BASE}/therapy/recommend`,
        therapyPayload
      );
      setTherapyResults(response.data);
    } catch (error) {
      console.error("Therapy recommendation error:", error);

      let errorMessage = error.message;
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail
            .map((err) => `${err.loc.join(".")}: ${err.msg}`)
            .join("; ");
        } else {
          errorMessage = error.response.data.detail;
        }
      }

      setTherapyResults({
        error: errorMessage,
      });
    } finally {
      setTherapyLoading(false);
    }
  };

  // LLM Configuration functions
  const handleLlmConfigChange = (field, value) => {
    setLlmConfig((prev) => ({
      ...prev,
      [field]: value,
    }));
    setLlmConfigSaved(false);
  };

  const saveLlmConfig = async () => {
    try {
      const response = await axios.post(
        `${API_BASE}/therapy/config`,
        llmConfig
      );
      console.log("LLM config saved:", response.data);
      setLlmConfigSaved(true);
      setTimeout(() => setLlmConfigSaved(false), 3000); // Clear message after 3 seconds
    } catch (error) {
      console.error("Error saving LLM config:", error);
      alert("Fehler beim Speichern der LLM-Konfiguration: " + error.message);
    }
  };

  const loadLlmConfig = async () => {
    try {
      const response = await axios.get(`${API_BASE}/therapy/config`);
      if (response.data.status === "success" && response.data.config) {
        setLlmConfig(response.data.config);
        console.log("LLM config loaded:", response.data.config);
      }
    } catch (error) {
      console.error("Error loading LLM config:", error);
      // Use default values if loading fails
    }
  };

  return (
    <div className="App admin-surface">
      <nav className="navbar navbar-expand-lg admin-navbar shadow-sm">
        <div className="container py-3">
          <div>
            <span className="navbar-brand mb-1">ABS-CDSS Admin Konsole</span>
            <p className="navbar-subtitle mb-0">
              Leitlinienverwaltung und Debuggingoberfläche
            </p>
          </div>
        </div>
      </nav>

      <div className="container admin-content">
        {/* Stats Card */}
        {stats && (
          <div className="card admin-card mb-4 mt-4">
            <div className="card-body">
              <h5 className="card-title">Systemstatus</h5>
              <div className="row">
                <div className="col-md-3">
                  <div className="text-center">
                    <h3 className="text-primary">{stats.total_guidelines}</h3>
                    <small>Leitlinien</small>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="text-center">
                    <h3 className="text-success">{stats.total_chunks}</h3>
                    <small>Text-Chunks</small>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="text-center">
                    <h3 className="text-info">{stats.index_size}</h3>
                    <small>Index-Einträge</small>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="text-center">
                    <h3 className="text-warning">CPU</h3>
                    <small>BERT Embeddings</small>
                  </div>
                </div>
              </div>
              {stats.guidelines.length > 0 && (
                <div className="mt-3">
                  <button
                    type="button"
                    className="btn btn-outline-secondary btn-sm w-100 d-flex justify-content-between align-items-center"
                    onClick={() =>
                      setGuidelinesExpanded((previous) => !previous)
                    }
                    aria-expanded={guidelinesExpanded}
                    aria-controls="available-guidelines-list"
                  >
                    <span>Verfügbare Leitlinien</span>
                    <span className="small text-muted">
                      {guidelinesExpanded ? "Einklappen" : "Anzeigen"}
                    </span>
                  </button>
                  {guidelinesExpanded && (
                    <ul
                      id="available-guidelines-list"
                      className="list-unstyled mt-2 mb-0"
                    >
                      {stats.guidelines.map((guideline, idx) => (
                        <li key={idx} className="small guideline-item">
                          <span className="guideline-accent" aria-hidden>
                            ●
                          </span>
                          <span>
                            {guideline.title} (
                            {guideline.indications.join(", ")})
                            {guideline.pages && (
                              <span className="text-muted">
                                {" "}
                                • {guideline.pages} Seiten
                              </span>
                            )}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <ul className="nav nav-tabs admin-tabs mb-4">
          <li className="nav-item">
            <button
              className={`nav-link admin-tab ${
                activeTab === "upload" ? "active" : ""
              }`}
              onClick={() => setActiveTab("upload")}
            >
              <span className="tab-indicator tab-upload" aria-hidden></span>
              <span>Leitlinien Upload</span>
            </button>
          </li>
          <li className="nav-item">
            <button
              className={`nav-link admin-tab ${
                activeTab === "manage" ? "active" : ""
              }`}
              onClick={() => {
                setActiveTab("manage");
                loadGuidelines();
              }}
            >
              <span className="tab-indicator tab-manage" aria-hidden></span>
              <span>Leitlinien verwalten</span>
            </button>
          </li>
          <li className="nav-item">
            <button
              className={`nav-link admin-tab ${
                activeTab === "patients" ? "active" : ""
              }`}
              onClick={() => setActiveTab("patients")}
            >
              <span className="tab-indicator tab-patients" aria-hidden></span>
              <span>Patienten</span>
            </button>
          </li>
          <li className="nav-item">
            <button
              className={`nav-link admin-tab ${
                activeTab === "therapy" ? "active" : ""
              }`}
              onClick={() => setActiveTab("therapy")}
            >
              <span className="tab-indicator tab-therapy" aria-hidden></span>
              <span>Therapieempfehlungen</span>
            </button>
          </li>
          <li className="nav-item">
            <button
              className={`nav-link admin-tab ${
                activeTab === "query-test" ? "active" : ""
              }`}
              onClick={() => setActiveTab("query-test")}
            >
              <span className="tab-indicator tab-query" aria-hidden></span>
              <span>Query-Test</span>
            </button>
          </li>
          <li className="nav-item">
            <button
              className={`nav-link admin-tab ${
                activeTab === "search" ? "active" : ""
              }`}
              onClick={() => setActiveTab("search")}
            >
              <span className="tab-indicator tab-search" aria-hidden></span>
              <span>RAG-Suche</span>
            </button>
          </li>
          <li className="nav-item">
            <button
              className={`nav-link admin-tab ${
                activeTab === "settings" ? "active" : ""
              }`}
              onClick={() => setActiveTab("settings")}
            >
              <span className="tab-indicator tab-settings" aria-hidden></span>
              <span>Einstellungen</span>
            </button>
          </li>
        </ul>

        {/* Upload Tab */}
        {activeTab === "upload" && (
          <div className="card admin-card">
            <div className="card-header">
              <h5>Leitlinien-Upload und Verarbeitung</h5>
            </div>
            <div className="card-body">
              <form onSubmit={handleFileUpload}>
                <div className="mb-3">
                  <label htmlFor="file" className="form-label">
                    Leitlinie (.txt oder .md Datei)
                  </label>
                  <input
                    type="file"
                    className="form-control"
                    id="file"
                    accept=".txt,.md"
                    onChange={(e) => setUploadFile(e.target.files[0])}
                    required
                  />
                  <div className="form-text">
                    Unterstützte Dateien: .txt (UTF-8), .md (Markdown mit
                    Seitenumbrüchen durch ---)
                  </div>
                </div>

                <div className="mb-3">
                  <label htmlFor="guidelineId" className="form-label">
                    Leitlinien-ID (optional)
                  </label>
                  <input
                    type="text"
                    className="form-control"
                    id="guidelineId"
                    value={guidelineId}
                    onChange={(e) => setGuidelineId(e.target.value)}
                    placeholder="z.B. AWMF_020-020l_CAP_S3_2021"
                  />
                  <div className="form-text">
                    Wird automatisch aus Dateinamen generiert, falls leer
                  </div>
                </div>

                <div className="mb-3">
                  <label className="form-label">Indikationen</label>
                  <div className="form-text mb-2">
                    Wählen Sie die Indikationen aus, für die diese Leitlinie
                    relevant ist:
                  </div>

                  {/* Searchable Dropdown */}
                  <div className="position-relative">
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Indikationen suchen oder auswählen..."
                      value={indicationSearch}
                      onChange={(e) => setIndicationSearch(e.target.value)}
                      onFocus={() => setIndicationDropdownOpen(true)}
                    />
                    <button
                      type="button"
                      className="btn btn-outline-secondary btn-sm position-absolute"
                      style={{
                        right: "5px",
                        top: "50%",
                        transform: "translateY(-50%)",
                      }}
                      onClick={() =>
                        setIndicationDropdownOpen(!indicationDropdownOpen)
                      }
                    >
                      ▼
                    </button>

                    {indicationDropdownOpen && (
                      <div
                        className="card position-absolute w-100 mt-1"
                        style={{ zIndex: 1000 }}
                      >
                        <div
                          className="card-body p-2"
                          style={{ maxHeight: "200px", overflowY: "auto" }}
                        >
                          {/* Select All Option */}
                          <div className="form-check mb-2 border-bottom pb-2">
                            <input
                              className="form-check-input"
                              type="checkbox"
                              id="select-all-indications"
                              checked={
                                selectedIndications.length ===
                                allIndicationOptions.length
                              }
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedIndications(
                                    allIndicationOptions.map((ind) => ind.value)
                                  );
                                } else {
                                  setSelectedIndications([]);
                                }
                              }}
                            />
                            <label
                              className="form-check-label fw-bold"
                              htmlFor="select-all-indications"
                            >
                              🔘 Alle auswählen
                            </label>
                          </div>

                          {/* Grouped and Filtered Indications */}
                          {availableIndicationOptions.map((group) => {
                            // Filter group options based on search
                            const filteredOptions = group.options.filter(
                              (indication) =>
                                indication.label
                                  .toLowerCase()
                                  .includes(indicationSearch.toLowerCase()) ||
                                indication.value
                                  .toLowerCase()
                                  .includes(indicationSearch.toLowerCase()) ||
                                group.category
                                  .toLowerCase()
                                  .includes(indicationSearch.toLowerCase())
                            );

                            // Only show group if it has matching options
                            if (filteredOptions.length === 0) return null;

                            return (
                              <div key={group.category} className="mb-3">
                                {/* Category Header */}
                                <div className="fw-bold text-primary border-bottom mb-2">
                                  📋 {group.category}
                                </div>

                                {/* Category Options */}
                                {filteredOptions.map((indication) => (
                                  <div
                                    key={indication.value}
                                    className="form-check ms-3"
                                  >
                                    <input
                                      className="form-check-input"
                                      type="checkbox"
                                      id={`indication-${indication.value}`}
                                      checked={selectedIndications.includes(
                                        indication.value
                                      )}
                                      onChange={(e) =>
                                        handleIndicationChange(
                                          indication.value,
                                          e.target.checked
                                        )
                                      }
                                    />
                                    <label
                                      className="form-check-label"
                                      htmlFor={`indication-${indication.value}`}
                                      style={{ fontSize: "0.9em" }}
                                    >
                                      {indication.label}
                                    </label>
                                  </div>
                                ))}
                              </div>
                            );
                          })}

                          {/* No results message */}
                          {availableIndicationOptions.every(
                            (group) =>
                              group.options.filter(
                                (indication) =>
                                  indication.label
                                    .toLowerCase()
                                    .includes(indicationSearch.toLowerCase()) ||
                                  indication.value
                                    .toLowerCase()
                                    .includes(indicationSearch.toLowerCase()) ||
                                  group.category
                                    .toLowerCase()
                                    .includes(indicationSearch.toLowerCase())
                              ).length === 0
                          ) && (
                            <div className="text-muted text-center py-2">
                              Keine Indikationen gefunden
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Selected indications display */}
                  {selectedIndications.length > 0 && (
                    <div className="mt-2">
                      <small className="text-muted">
                        Ausgewählte Indikationen:
                      </small>
                      <div className="d-flex flex-wrap gap-1 mt-2">
                        {selectedIndications.map((indicationValue) => {
                          const indication = allIndicationOptions.find(
                            (ind) => ind.value === indicationValue
                          );
                          return (
                            <span
                              key={indicationValue}
                              className="badge bg-success"
                            >
                              {indication ? indication.label : indicationValue}
                              <button
                                type="button"
                                className="btn-close btn-close-white ms-1"
                                style={{ fontSize: "0.6em" }}
                                onClick={() => {
                                  setSelectedIndications(
                                    selectedIndications.filter(
                                      (ind) => ind !== indicationValue
                                    )
                                  );
                                }}
                              ></button>
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {selectedIndications.length === 0 && (
                    <div className="text-warning mt-2">
                      Mindestens eine Indikation muss ausgewählt werden.
                    </div>
                  )}
                </div>

                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={loading || selectedIndications.length === 0}
                >
                  {loading ? (
                    <>
                      <span
                        className="spinner-border spinner-border-sm me-2"
                        role="status"
                      ></span>
                      Verarbeitung...
                    </>
                  ) : (
                    `Upload starten (${selectedIndications.join(", ")})`
                  )}
                </button>
              </form>

              {uploadStatus && (
                <div className={`alert mt-3 ${getAlertClass(uploadStatus)}`}>
                  {uploadStatus.message}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Manage Tab */}
        {activeTab === "manage" && (
          <div className="card admin-card">
            <div className="card-header">
              <h5>Leitlinien verwalten</h5>
            </div>
            <div className="card-body">
              <div className="row mb-4">
                <div className="col-md-6">
                  <button
                    className="btn btn-outline-info w-100"
                    onClick={loadGuidelines}
                    disabled={loading}
                  >
                    Liste aktualisieren
                  </button>
                </div>
                <div className="col-md-6">
                  <button
                    className="btn btn-danger w-100"
                    onClick={deleteAllGuidelines}
                    disabled={loading}
                  >
                    Alle Leitlinien löschen
                  </button>
                </div>
              </div>

              {deleteStatus && (
                <div className={`alert ${getAlertClass(deleteStatus)}`}>
                  {deleteStatus.message}
                </div>
              )}

              {guidelines.length === 0 ? (
                <div className="text-center text-muted">
                  <p>Keine Leitlinien vorhanden.</p>
                  <p>
                    Verwenden Sie den Upload-Tab, um Leitlinien hinzuzufügen.
                  </p>
                </div>
              ) : (
                <div className="table-responsive">
                  <table className="table table-striped">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Titel</th>
                        <th>Indikationen</th>
                        <th>Seiten</th>
                        <th>Aktionen</th>
                      </tr>
                    </thead>
                    <tbody>
                      {guidelines.map((guideline) => (
                        <tr key={guideline.id}>
                          <td>
                            <code className="small">{guideline.id}</code>
                          </td>
                          <td>{guideline.title}</td>
                          <td>
                            {guideline.indications.map((indication, index) => (
                              <span
                                key={index}
                                className="badge bg-primary me-1 mb-1"
                                style={{ fontSize: "0.75em" }}
                              >
                                {allIndicationOptions.find(
                                  (opt) => opt.value === indication
                                )?.label || indication}
                              </span>
                            ))}
                          </td>
                          <td>
                            <span className="badge bg-secondary">
                              {guideline.pages || 0} Seiten
                            </span>
                          </td>
                          <td>
                            <button
                              className="btn btn-sm btn-outline-danger"
                              onClick={() => deleteGuideline(guideline.id)}
                              disabled={loading}
                            >
                              Löschen
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Patients Tab */}
        {activeTab === "patients" && (
          <div className="row">
            <div className="col-md-4">
              <div className="card">
                <div className="card-header">
                  <h5>Patientensuche</h5>
                </div>
                <div className="card-body">
                  <form onSubmit={handlePatientSearch}>
                    <div className="mb-3">
                      <label className="form-label">Suchtyp</label>
                      <div className="form-check">
                        <input
                          className="form-check-input"
                          type="radio"
                          name="searchType"
                          id="searchById"
                          value="id"
                          checked={patientSearchType === "id"}
                          onChange={(e) => setPatientSearchType(e.target.value)}
                        />
                        <label
                          className="form-check-label"
                          htmlFor="searchById"
                        >
                          Suche nach Patienten-ID
                        </label>
                      </div>
                      <div className="form-check">
                        <input
                          className="form-check-input"
                          type="radio"
                          name="searchType"
                          id="searchByName"
                          value="name_birthdate"
                          checked={patientSearchType === "name_birthdate"}
                          onChange={(e) => setPatientSearchType(e.target.value)}
                        />
                        <label
                          className="form-check-label"
                          htmlFor="searchByName"
                        >
                          Suche nach Name + Geburtsdatum
                        </label>
                      </div>
                    </div>

                    {patientSearchType === "id" && (
                      <div className="mb-3">
                        <label htmlFor="patientId" className="form-label">
                          Patienten-ID
                        </label>
                        <input
                          type="text"
                          className="form-control"
                          id="patientId"
                          value={patientSearchForm.patient_id}
                          onChange={(e) =>
                            setPatientSearchForm((prev) => ({
                              ...prev,
                              patient_id: e.target.value,
                            }))
                          }
                          placeholder="z.B. cfsb1758022576326"
                          required
                        />
                      </div>
                    )}

                    {patientSearchType === "name_birthdate" && (
                      <>
                        <div className="mb-3">
                          <label htmlFor="givenName" className="form-label">
                            Vorname
                          </label>
                          <input
                            type="text"
                            className="form-control"
                            id="givenName"
                            value={patientSearchForm.given_name}
                            onChange={(e) =>
                              setPatientSearchForm((prev) => ({
                                ...prev,
                                given_name: e.target.value,
                              }))
                            }
                            placeholder="z.B. Dieter"
                            required
                          />
                        </div>
                        <div className="mb-3">
                          <label htmlFor="familyName" className="form-label">
                            Nachname
                          </label>
                          <input
                            type="text"
                            className="form-control"
                            id="familyName"
                            value={patientSearchForm.family_name}
                            onChange={(e) =>
                              setPatientSearchForm((prev) => ({
                                ...prev,
                                family_name: e.target.value,
                              }))
                            }
                            placeholder="z.B. Diabetes"
                            required
                          />
                        </div>
                        <div className="mb-3">
                          <label htmlFor="birthDate" className="form-label">
                            Geburtsdatum
                          </label>
                          <input
                            type="date"
                            className="form-control"
                            id="birthDate"
                            value={patientSearchForm.birth_date}
                            onChange={(e) =>
                              setPatientSearchForm((prev) => ({
                                ...prev,
                                birth_date: e.target.value,
                              }))
                            }
                            required
                          />
                        </div>
                      </>
                    )}

                    <div className="d-grid gap-2">
                      <button
                        type="submit"
                        className="btn btn-primary"
                        disabled={patientSearchLoading}
                      >
                        {patientSearchLoading ? (
                          <>
                            <span className="spinner-border spinner-border-sm me-2"></span>
                            Suche läuft...
                          </>
                        ) : (
                          "Patientensuche starten"
                        )}
                      </button>
                      <button
                        type="button"
                        className="btn btn-outline-secondary"
                        onClick={resetPatientSearch}
                      >
                        Formular zurücksetzen
                      </button>
                    </div>
                  </form>

                  {/* Patient Search Results */}
                  {patientSearchResults.length > 0 && (
                    <div className="mt-4">
                      <h6>Suchergebnisse ({patientSearchResults.length})</h6>
                      <div className="list-group">
                        {patientSearchResults.map((patient) => (
                          <button
                            key={patient.patient_id}
                            type="button"
                            className="list-group-item list-group-item-action"
                            onClick={() =>
                              handlePatientSelect(patient.patient_id)
                            }
                            disabled={patientDetailsLoading}
                          >
                            <div className="d-flex w-100 justify-content-between">
                              <h6 className="mb-1">{patient.name}</h6>
                              <small>ID: {patient.patient_id}</small>
                            </div>
                            <p className="mb-1">
                              {patient.gender}
                              {patient.age && ` • ${patient.age} Jahre`}
                            </p>
                            {patient.birth_date && (
                              <small>
                                Geboren:{" "}
                                {convertToEuropeanDate(patient.birth_date)}
                              </small>
                            )}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="col-md-8">
              <div className="card">
                <div className="card-header">
                  <h5>Patientendaten</h5>
                </div>
                <div className="card-body">
                  {!selectedPatient && !patientDetailsLoading && (
                    <div className="text-center text-muted py-4">
                      <p>
                        Wählen Sie einen Patienten aus der Suchliste aus, um die
                        Daten anzuzeigen.
                      </p>
                    </div>
                  )}

                  {patientDetailsLoading && (
                    <div className="text-center py-4">
                      <div
                        className="spinner-border text-primary"
                        role="status"
                      >
                        <span className="visually-hidden">
                          Lade Patientendaten...
                        </span>
                      </div>
                      <p className="mt-2 text-muted">
                        Patientendaten werden geladen...
                      </p>
                    </div>
                  )}

                  {selectedPatient && !patientDetailsLoading && (
                    <div>
                      {loading && (
                        <div className="text-center mb-3">
                          <div className="spinner-border" role="status">
                            <span className="visually-hidden">Lädt...</span>
                          </div>
                        </div>
                      )}

                      <div className="row">
                        {/* Basic Info */}
                        <div className="col-md-6">
                          <div className="card mb-3">
                            <div className="card-header bg-primary text-white">
                              <h6 className="mb-0">Grunddaten</h6>
                            </div>
                            <div className="card-body">
                              <table className="table table-sm">
                                <tbody>
                                  <tr>
                                    <td>
                                      <strong>Name:</strong>
                                    </td>
                                    <td>{selectedPatient.name}</td>
                                  </tr>
                                  <tr>
                                    <td>
                                      <strong>Geschlecht:</strong>
                                    </td>
                                    <td>{selectedPatient.gender}</td>
                                  </tr>
                                  <tr>
                                    <td>
                                      <strong>Alter:</strong>
                                    </td>
                                    <td>
                                      {selectedPatient.age
                                        ? `${selectedPatient.age} Jahre`
                                        : "Unbekannt"}
                                    </td>
                                  </tr>
                                  <tr>
                                    <td>
                                      <strong>Geburtsdatum:</strong>
                                    </td>
                                    <td>
                                      {selectedPatient.birth_date
                                        ? convertToEuropeanDate(
                                            selectedPatient.birth_date
                                          )
                                        : "Unbekannt"}
                                    </td>
                                  </tr>
                                  <tr>
                                    <td>
                                      <strong>Größe:</strong>
                                    </td>
                                    <td>
                                      {selectedPatient.height
                                        ? `${selectedPatient.height} cm`
                                        : "Nicht verfügbar"}
                                    </td>
                                  </tr>
                                  <tr>
                                    <td>
                                      <strong>Gewicht:</strong>
                                    </td>
                                    <td>
                                      {selectedPatient.weight
                                        ? `${selectedPatient.weight} kg`
                                        : "Nicht verfügbar"}
                                    </td>
                                  </tr>
                                  <tr>
                                    <td>
                                      <strong>BMI:</strong>
                                    </td>
                                    <td>
                                      {selectedPatient.bmi
                                        ? selectedPatient.bmi
                                        : "Nicht berechenbar"}
                                    </td>
                                  </tr>
                                  <tr>
                                    <td>
                                      <strong>GFR:</strong>
                                    </td>
                                    <td>
                                      {selectedPatient.gfr
                                        ? `${selectedPatient.gfr} ml/min/1.73m²`
                                        : "Nicht verfügbar"}
                                    </td>
                                  </tr>
                                  <tr>
                                    <td>
                                      <strong>Schwangerschaft:</strong>
                                    </td>
                                    <td>{selectedPatient.pregnancy_status}</td>
                                  </tr>
                                </tbody>
                              </table>
                            </div>
                          </div>
                        </div>

                        {/* Medical Info */}
                        <div className="col-md-6">
                          {/* Conditions */}
                          <div className="card mb-3">
                            <div className="card-header bg-warning text-dark">
                              <h6 className="mb-0">Vorerkrankungen</h6>
                            </div>
                            <div className="card-body">
                              {selectedPatient.conditions.length > 0 ? (
                                <ul className="list-unstyled mb-0">
                                  {selectedPatient.conditions.map(
                                    (condition, idx) => (
                                      <li key={idx} className="mb-1">
                                        • {condition}
                                      </li>
                                    )
                                  )}
                                </ul>
                              ) : (
                                <span className="text-muted">
                                  Keine Vorerkrankungen dokumentiert
                                </span>
                              )}
                            </div>
                          </div>

                          {/* Allergies */}
                          <div className="card mb-3">
                            <div className="card-header bg-danger text-white">
                              <h6 className="mb-0">Allergien</h6>
                            </div>
                            <div className="card-body">
                              {selectedPatient.allergies.length > 0 ? (
                                <ul className="list-unstyled mb-0">
                                  {selectedPatient.allergies.map(
                                    (allergy, idx) => (
                                      <li key={idx} className="mb-1">
                                        • {allergy}
                                      </li>
                                    )
                                  )}
                                </ul>
                              ) : (
                                <span className="text-muted">
                                  Keine Allergien dokumentiert
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Medications */}
                        <div className="col-12">
                          <div className="card mb-3">
                            <div className="card-header bg-success text-white">
                              <h6 className="mb-0">Aktuelle Medikamente</h6>
                            </div>
                            <div className="card-body">
                              {selectedPatient.medications.length > 0 ? (
                                <div className="row">
                                  {selectedPatient.medications.map(
                                    (medication, idx) => (
                                      <div key={idx} className="col-md-6 mb-2">
                                        • {medication}
                                      </div>
                                    )
                                  )}
                                </div>
                              ) : (
                                <span className="text-muted">
                                  Keine aktuellen Medikamente dokumentiert
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Lab Values */}
                        <div className="col-12">
                          <div className="card">
                            <div className="card-header bg-info text-white">
                              <h6 className="mb-0">Laborwerte</h6>
                            </div>
                            <div className="card-body">
                              {selectedPatient.lab_values.length > 0 ? (
                                <div className="table-responsive">
                                  <table className="table table-sm table-striped">
                                    <thead>
                                      <tr>
                                        <th>Parameter</th>
                                        <th>Wert</th>
                                        <th>Einheit</th>
                                        <th>Code</th>
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {selectedPatient.lab_values.map(
                                        (lab, idx) => (
                                          <tr key={idx}>
                                            <td>{lab.name}</td>
                                            <td>
                                              <strong>{lab.value}</strong>
                                            </td>
                                            <td>{lab.unit}</td>
                                            <td>
                                              <code className="small">
                                                {lab.code}
                                              </code>
                                            </td>
                                          </tr>
                                        )
                                      )}
                                    </tbody>
                                  </table>
                                </div>
                              ) : (
                                <span className="text-muted">
                                  Keine Laborwerte verfügbar
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Therapy Recommendations Tab */}
        {activeTab === "therapy" && (
          <div className="row">
            <div className="col-md-4">
              <div className="card">
                <div className="card-header">
                  <h5>Therapie-Empfehlung anfragen</h5>
                </div>
                <div className="card-body">
                  <form onSubmit={handleTherapyRecommendation}>
                    <div className="mb-3">
                      <label className="form-label">Indikation</label>
                      <select
                        className="form-select"
                        value={therapyForm.indication}
                        onChange={(e) =>
                          setTherapyForm((prev) => ({
                            ...prev,
                            indication: e.target.value,
                          }))
                        }
                      >
                        {availableIndicationOptions.map((group) => (
                          <optgroup key={group.category} label={group.category}>
                            {group.options.map((indication) => (
                              <option
                                key={indication.value}
                                value={indication.value}
                              >
                                {indication.label}
                              </option>
                            ))}
                          </optgroup>
                        ))}
                      </select>
                    </div>

                    <div className="mb-3">
                      <label className="form-label">Schweregrad</label>
                      <select
                        className="form-select"
                        value={therapyForm.severity}
                        onChange={(e) =>
                          setTherapyForm((prev) => ({
                            ...prev,
                            severity: e.target.value,
                          }))
                        }
                      >
                        <option value="LEICHT">Leicht</option>
                        <option value="MITTELSCHWER">Mittelschwer</option>
                        <option value="SCHWER">Schwer</option>
                        <option value="SEPTISCH">Septisch</option>
                      </select>
                    </div>

                    <div className="mb-3">
                      <label className="form-label">
                        Infektionsort (optional)
                      </label>
                      <select
                        className="form-select"
                        value={therapyForm.infection_site}
                        onChange={(e) =>
                          setTherapyForm((prev) => ({
                            ...prev,
                            infection_site: e.target.value,
                          }))
                        }
                      >
                        <option value="">-- Nicht spezifiziert --</option>
                        <option value="LUNGE">Lunge</option>
                        <option value="BLUT">Blut</option>
                        <option value="HARNTRAKT">Harntrakt</option>
                        <option value="ZNS">ZNS</option>
                        <option value="HAUT_WEICHTEILE">Haut/Weichteile</option>
                      </select>
                    </div>

                    <div className="mb-3">
                      <label className="form-label">Risikofaktoren</label>
                      {[
                        {
                          key: "ANTIBIOTISCHE_VORBEHANDLUNG",
                          label: "Antibiotische Vorbehandlung",
                        },
                        { key: "MRGN_VERDACHT", label: "MRGN Verdacht" },
                        { key: "MRSA_VERDACHT", label: "MRSA Verdacht" },
                        { key: "BEATMUNG", label: "Beatmung" },
                        { key: "KATHETER", label: "Katheter" },
                      ].map((factor) => (
                        <div key={factor.key} className="form-check">
                          <input
                            className="form-check-input"
                            type="checkbox"
                            id={`therapy-${factor.key}`}
                            checked={therapyForm.risk_factors.includes(
                              factor.key
                            )}
                            onChange={(e) =>
                              handleTherapyRiskFactorChange(
                                factor.key,
                                e.target.checked
                              )
                            }
                          />
                          <label
                            className="form-check-label"
                            htmlFor={`therapy-${factor.key}`}
                          >
                            {factor.label}
                          </label>
                        </div>
                      ))}
                    </div>

                    <div className="mb-3">
                      <label className="form-label">
                        Verdachtskeime (optional)
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        value={therapyForm.suspected_pathogens}
                        onChange={(e) =>
                          setTherapyForm((prev) => ({
                            ...prev,
                            suspected_pathogens: e.target.value,
                          }))
                        }
                        placeholder="z.B. S. pneumoniae, H. influenzae"
                      />
                      <div className="form-text">Komma-getrennt</div>
                    </div>

                    <div className="mb-3">
                      <label className="form-label">
                        Patienten-ID (optional)
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        value={therapyForm.patient_id}
                        onChange={(e) =>
                          setTherapyForm((prev) => ({
                            ...prev,
                            patient_id: e.target.value,
                          }))
                        }
                        placeholder="z.B. cfsb1758022576326"
                      />
                      <div className="form-text">
                        Für patientenspezifische Empfehlungen
                      </div>
                    </div>

                    <div className="mb-3">
                      <label className="form-label">Freitext (optional)</label>
                      <textarea
                        className="form-control"
                        rows="3"
                        value={therapyForm.free_text}
                        onChange={(e) =>
                          setTherapyForm((prev) => ({
                            ...prev,
                            free_text: e.target.value,
                          }))
                        }
                        placeholder="Zusätzliche klinische Informationen..."
                      />
                    </div>

                    <button
                      type="submit"
                      className="btn btn-success w-100"
                      disabled={therapyLoading}
                    >
                      {therapyLoading ? (
                        <>
                          <span
                            className="spinner-border spinner-border-sm me-2"
                            role="status"
                          ></span>
                          Generiere Therapie-Empfehlungen...
                        </>
                      ) : (
                        "Therapie-Empfehlungen generieren"
                      )}
                    </button>
                  </form>
                </div>
              </div>
            </div>

            <div className="col-md-8">
              <div className="card">
                <div className="card-header">
                  <h5>Therapie-Empfehlungen</h5>
                </div>
                <div className="card-body">
                  {!therapyResults && !therapyLoading && (
                    <div className="text-muted text-center py-4">
                      <p>
                        Füllen Sie die Parameter aus und generieren Sie
                        Therapie-Empfehlungen
                      </p>
                      <p>
                        Das System wird relevante Leitlinien durchsuchen und
                        strukturierte Antibiotika-Empfehlungen erstellen.
                      </p>
                    </div>
                  )}

                  {therapyLoading && (
                    <div className="text-center py-4">
                      <div
                        className="spinner-border text-primary"
                        role="status"
                      >
                        <span className="visually-hidden">
                          Generiere Therapie-Empfehlungen...
                        </span>
                      </div>
                      <p className="mt-2 text-muted">
                        LLM erstellt strukturierte Therapie-Empfehlungen
                        basierend auf aktuellen Leitlinien...
                      </p>
                    </div>
                  )}

                  {therapyResults?.error && (
                    <div className="alert alert-danger">
                      <strong>Fehler:</strong> {therapyResults.error}
                    </div>
                  )}

                  {therapyResults && !therapyResults.error && (
                    <div>
                      {/* Context Information */}
                      {therapyResults.context_summary && (
                        <div className="mb-4">
                          <div className="card bg-light">
                            <div className="card-header">
                              <h6 className="mb-0">Klinischer Kontext</h6>
                            </div>
                            <div className="card-body">
                              <div className="row">
                                <div className="col-md-6">
                                  <small>
                                    <strong>RAG Ergebnisse:</strong>{" "}
                                    {
                                      therapyResults.context_summary
                                        .rag_results_count
                                    }
                                  </small>
                                </div>
                                <div className="col-md-6">
                                  <small>
                                    <strong>Dosierungstabellen:</strong>{" "}
                                    {
                                      therapyResults.context_summary
                                        .dosing_tables_count
                                    }
                                  </small>
                                </div>
                              </div>
                              {therapyResults.context_summary
                                .patient_available && (
                                <div className="mt-2">
                                  <span className="badge bg-info">
                                    Patientendaten verfügbar
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Patient Data Display */}
                      {therapyResults.patient_summary && (
                        <div className="alert alert-info mb-4">
                          <h6 className="alert-heading">
                            Aktuelle Patientendaten
                          </h6>
                          <div className="small">
                            {therapyResults.patient_summary
                              .split("\n")
                              .map((line, index) => (
                                <div key={index}>
                                  <span>{line}</span>
                                </div>
                              ))}
                          </div>
                        </div>
                      )}

                      {/* Therapy Recommendations */}
                      {therapyResults.recommendations &&
                        therapyResults.recommendations.length > 0 && (
                          <div className="mb-4">
                            <h6 className="text-primary">
                              Empfohlene Therapien (
                              {therapyResults.recommendations.length})
                            </h6>
                            {therapyResults.recommendations.map(
                              (recommendation, idx) => (
                                <div
                                  key={idx}
                                  className="card mb-3 border-success"
                                >
                                  <div className="card-header bg-success text-white">
                                    <div className="d-flex justify-content-between align-items-center">
                                      <div>
                                        <h6 className="mb-0">
                                          Option {idx + 1}:{" "}
                                          {recommendation.name}
                                        </h6>
                                      </div>
                                      <span className="badge bg-light text-success">
                                        Priorität: {recommendation.priority}
                                      </span>
                                    </div>
                                  </div>
                                  <div className="card-body">
                                    {/* Medications */}
                                    <div className="mb-3">
                                      <h6>Medikamente</h6>
                                      {recommendation.medications.map(
                                        (medication, medIdx) => (
                                          <div
                                            key={medIdx}
                                            className="border rounded p-3 mb-2"
                                          >
                                            {/* Medication Header */}
                                            <div className="row mb-3">
                                              <div className="col-12">
                                                <div className="mb-2">
                                                  <h6 className="text-primary mb-1">
                                                    {medication.active_ingredients.map(
                                                      (ingredient, ingIdx) => (
                                                        <span key={ingIdx}>
                                                          <strong>
                                                            {ingredient.name}
                                                          </strong>{" "}
                                                          {ingredient.strength}
                                                          {ingIdx <
                                                          medication
                                                            .active_ingredients
                                                            .length -
                                                            1
                                                            ? " + "
                                                            : ""}
                                                        </span>
                                                      )
                                                    )}
                                                  </h6>
                                                </div>
                                              </div>
                                            </div>

                                            {/* Structured Dosing Table - New Structure with Individual Dosing per Ingredient */}
                                            <div className="table-responsive">
                                              <table className="table table-sm table-bordered">
                                                <thead className="table-light">
                                                  <tr>
                                                    <th>Wirkstoff</th>
                                                    <th>Stärke</th>
                                                    <th>Häufigkeit</th>
                                                    <th>Therapiedauer</th>
                                                    <th>Applikationsweg</th>
                                                  </tr>
                                                </thead>
                                                <tbody>
                                                  {medication.active_ingredients.map(
                                                    (ingredient, ingIdx) => (
                                                      <tr key={ingIdx}>
                                                        <td>
                                                          <strong>
                                                            {ingredient.name}
                                                          </strong>
                                                        </td>
                                                        <td>
                                                          {ingredient.strength}
                                                        </td>
                                                        <td>
                                                          {ingredient.frequency_upper &&
                                                          ingredient.frequency_upper !==
                                                            ingredient.frequency_lower_bound
                                                            ? `${ingredient.frequency_lower_bound}-${ingredient.frequency_upper}x ${ingredient.frequency_unit}`
                                                            : `${ingredient.frequency_lower_bound}x ${ingredient.frequency_unit}`}
                                                        </td>
                                                        <td>
                                                          {ingredient.duration_lower_bound ? (
                                                            ingredient.duration_upper_bound &&
                                                            ingredient.duration_upper_bound !==
                                                              ingredient.duration_lower_bound ? (
                                                              `${ingredient.duration_lower_bound}-${ingredient.duration_upper_bound} ${ingredient.duration_unit}`
                                                            ) : (
                                                              `${ingredient.duration_lower_bound} ${ingredient.duration_unit}`
                                                            )
                                                          ) : (
                                                            <span className="text-muted">
                                                              Nicht spezifiziert
                                                            </span>
                                                          )}
                                                        </td>
                                                        <td>
                                                          {ingredient.route}
                                                        </td>
                                                      </tr>
                                                    )
                                                  )}
                                                </tbody>
                                              </table>
                                            </div>

                                            {/* Medication Notes */}
                                            {medication.notes && (
                                              <div className="mt-2">
                                                <small className="text-muted">
                                                  {medication.notes}
                                                </small>
                                              </div>
                                            )}

                                            {/* Medication-specific Clinical Guidance */}
                                            {medication.clinical_guidance && (
                                              <div className="mt-3">
                                                <h6 className="text-primary mb-3">
                                                  Klinische Hinweise für{" "}
                                                  {medication.active_ingredients
                                                    .map((ai) => ai.name)
                                                    .join(" / ")}
                                                </h6>
                                                <div className="row">
                                                  {/* Monitoring Parameters */}
                                                  {medication.clinical_guidance
                                                    .monitoring_parameters &&
                                                    medication.clinical_guidance
                                                      .monitoring_parameters
                                                      .length > 0 && (
                                                      <div className="col-md-4 mb-3">
                                                        <div className="card h-100 border-info">
                                                          <div className="card-header bg-info text-white">
                                                            <h6 className="mb-0">
                                                              Monitoring
                                                            </h6>
                                                          </div>
                                                          <div className="card-body">
                                                            <ul className="list-unstyled mb-0">
                                                              {medication.clinical_guidance.monitoring_parameters.map(
                                                                (
                                                                  param,
                                                                  paramIdx
                                                                ) => (
                                                                  <li
                                                                    key={
                                                                      paramIdx
                                                                    }
                                                                    className="small mb-1"
                                                                  >
                                                                    • {param}
                                                                  </li>
                                                                )
                                                              )}
                                                            </ul>
                                                          </div>
                                                        </div>
                                                      </div>
                                                    )}

                                                  {/* Relevant Side Effects */}
                                                  {medication.clinical_guidance
                                                    .relevant_side_effects &&
                                                    medication.clinical_guidance
                                                      .relevant_side_effects
                                                      .length > 0 && (
                                                      <div className="col-md-4 mb-3">
                                                        <div className="card h-100 border-warning">
                                                          <div className="card-header bg-warning text-dark">
                                                            <h6 className="mb-0">
                                                              Relevante
                                                              Nebenwirkungen
                                                            </h6>
                                                          </div>
                                                          <div className="card-body">
                                                            <ul className="list-unstyled mb-0">
                                                              {medication.clinical_guidance.relevant_side_effects.map(
                                                                (
                                                                  effect,
                                                                  effectIdx
                                                                ) => (
                                                                  <li
                                                                    key={
                                                                      effectIdx
                                                                    }
                                                                    className="small mb-1 text-warning"
                                                                  >
                                                                    • {effect}
                                                                  </li>
                                                                )
                                                              )}
                                                            </ul>
                                                          </div>
                                                        </div>
                                                      </div>
                                                    )}

                                                  {/* Drug Interactions */}
                                                  {medication.clinical_guidance
                                                    .drug_interactions &&
                                                    medication.clinical_guidance
                                                      .drug_interactions
                                                      .length > 0 && (
                                                      <div className="col-md-4 mb-3">
                                                        <div className="card h-100 border-danger">
                                                          <div className="card-header bg-danger text-white">
                                                            <h6 className="mb-0">
                                                              Arzneimittelinteraktionen
                                                            </h6>
                                                          </div>
                                                          <div className="card-body">
                                                            <ul className="list-unstyled mb-0">
                                                              {medication.clinical_guidance.drug_interactions.map(
                                                                (
                                                                  interaction,
                                                                  intIdx
                                                                ) => (
                                                                  <li
                                                                    key={intIdx}
                                                                    className="small mb-1 text-danger"
                                                                  >
                                                                    •{" "}
                                                                    {
                                                                      interaction
                                                                    }
                                                                  </li>
                                                                )
                                                              )}
                                                            </ul>
                                                          </div>
                                                        </div>
                                                      </div>
                                                    )}
                                                </div>

                                                {/* Additional Clinical Information */}
                                                {(medication.clinical_guidance
                                                  .pregnancy_considerations ||
                                                  medication.clinical_guidance
                                                    .deescalation_focus_info) && (
                                                  <div className="row mt-3">
                                                    {medication
                                                      .clinical_guidance
                                                      .pregnancy_considerations && (
                                                      <div className="col-12 mb-2">
                                                        <div className="alert alert-warning mb-2">
                                                          <strong>
                                                            Schwangerschaft:
                                                          </strong>{" "}
                                                          {
                                                            medication
                                                              .clinical_guidance
                                                              .pregnancy_considerations
                                                          }
                                                        </div>
                                                      </div>
                                                    )}

                                                    {medication
                                                      .clinical_guidance
                                                      .deescalation_focus_info && (
                                                      <div className="col-12 mb-2">
                                                        <div className="alert alert-info mb-2">
                                                          <strong>
                                                            Deeskalation/Fokussierung:
                                                          </strong>{" "}
                                                          {
                                                            medication
                                                              .clinical_guidance
                                                              .deescalation_focus_info
                                                          }
                                                        </div>
                                                      </div>
                                                    )}
                                                  </div>
                                                )}
                                              </div>
                                            )}
                                          </div>
                                        )
                                      )}
                                    </div>

                                    {/* Sources */}
                                    {recommendation.sources &&
                                      recommendation.sources.length > 0 && (
                                        <div className="mt-3">
                                          <h6>Quellen</h6>
                                          <div className="row">
                                            {recommendation.sources.map(
                                              (source, sourceIdx) => (
                                                <div
                                                  key={sourceIdx}
                                                  className="col-md-6 mb-2"
                                                >
                                                  <div className="border rounded p-2 bg-light">
                                                    <small>
                                                      <strong>
                                                        {source.guideline_id}
                                                      </strong>
                                                      {source.section && (
                                                        <span>
                                                          {" "}
                                                          • {source.section}
                                                        </span>
                                                      )}
                                                      {source.page && (
                                                        <span>
                                                          {" "}
                                                          • Seite {source.page}
                                                        </span>
                                                      )}
                                                      <br />
                                                      <span className="text-muted">
                                                        Relevanz:{" "}
                                                        {(
                                                          source.relevance_score *
                                                          100
                                                        ).toFixed(1)}
                                                        %
                                                      </span>
                                                    </small>
                                                  </div>
                                                </div>
                                              )
                                            )}
                                          </div>
                                        </div>
                                      )}

                                    {/* Clinical Guidance - displayed once per therapy option, AFTER all medications */}
                                    {recommendation.clinical_guidance && (
                                      <div className="mt-4">
                                        <h6 className="text-primary mb-3">
                                          Klinische Hinweise
                                        </h6>
                                        <div className="row">
                                          {/* Monitoring Parameters */}
                                          {recommendation.clinical_guidance
                                            .monitoring_parameters &&
                                            recommendation.clinical_guidance
                                              .monitoring_parameters.length >
                                              0 && (
                                              <div className="col-md-4 mb-3">
                                                <div className="card h-100 border-info">
                                                  <div className="card-header bg-info text-white">
                                                    <h6 className="mb-0">
                                                      Monitoring
                                                    </h6>
                                                  </div>
                                                  <div className="card-body">
                                                    <ul className="list-unstyled mb-0">
                                                      {recommendation.clinical_guidance.monitoring_parameters.map(
                                                        (param, paramIdx) => (
                                                          <li
                                                            key={paramIdx}
                                                            className="small mb-1"
                                                          >
                                                            • {param}
                                                          </li>
                                                        )
                                                      )}
                                                    </ul>
                                                  </div>
                                                </div>
                                              </div>
                                            )}

                                          {/* Relevant Side Effects */}
                                          {recommendation.clinical_guidance
                                            .relevant_side_effects &&
                                            recommendation.clinical_guidance
                                              .relevant_side_effects.length >
                                              0 && (
                                              <div className="col-md-4 mb-3">
                                                <div className="card h-100 border-warning">
                                                  <div className="card-header bg-warning text-dark">
                                                    <h6 className="mb-0">
                                                      Relevante Nebenwirkungen
                                                    </h6>
                                                  </div>
                                                  <div className="card-body">
                                                    <ul className="list-unstyled mb-0">
                                                      {recommendation.clinical_guidance.relevant_side_effects.map(
                                                        (effect, effectIdx) => (
                                                          <li
                                                            key={effectIdx}
                                                            className="small mb-1 text-warning"
                                                          >
                                                            • {effect}
                                                          </li>
                                                        )
                                                      )}
                                                    </ul>
                                                  </div>
                                                </div>
                                              </div>
                                            )}

                                          {/* Drug Interactions */}
                                          {recommendation.clinical_guidance
                                            .drug_interactions &&
                                            recommendation.clinical_guidance
                                              .drug_interactions.length > 0 && (
                                              <div className="col-md-4 mb-3">
                                                <div className="card h-100 border-danger">
                                                  <div className="card-header bg-danger text-white">
                                                    <h6 className="mb-0">
                                                      Arzneimittelinteraktionen
                                                    </h6>
                                                  </div>
                                                  <div className="card-body">
                                                    <ul className="list-unstyled mb-0">
                                                      {recommendation.clinical_guidance.drug_interactions.map(
                                                        (
                                                          interaction,
                                                          intIdx
                                                        ) => (
                                                          <li
                                                            key={intIdx}
                                                            className="small mb-1 text-danger"
                                                          >
                                                            • {interaction}
                                                          </li>
                                                        )
                                                      )}
                                                    </ul>
                                                  </div>
                                                </div>
                                              </div>
                                            )}
                                        </div>

                                        {/* Additional Clinical Information */}
                                        {(recommendation.clinical_guidance
                                          .pregnancy_considerations ||
                                          recommendation.clinical_guidance
                                            .deescalation_info ||
                                          recommendation.clinical_guidance
                                            .therapy_focus_info) && (
                                          <div className="row mt-3">
                                            {recommendation.clinical_guidance
                                              .pregnancy_considerations && (
                                              <div className="col-12 mb-2">
                                                <div className="alert alert-warning mb-2">
                                                  <strong>
                                                    Schwangerschaft:
                                                  </strong>{" "}
                                                  {
                                                    recommendation
                                                      .clinical_guidance
                                                      .pregnancy_considerations
                                                  }
                                                </div>
                                              </div>
                                            )}

                                            {recommendation.clinical_guidance
                                              .deescalation_focus_info && (
                                              <div className="col-12 mb-2">
                                                <div className="alert alert-info mb-2">
                                                  <strong>
                                                    Deeskalation/Fokussierung:
                                                  </strong>{" "}
                                                  {
                                                    recommendation
                                                      .clinical_guidance
                                                      .deescalation_focus_info
                                                  }
                                                </div>
                                              </div>
                                            )}
                                          </div>
                                        )}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              )
                            )}
                          </div>
                        )}

                      {/* General Clinical Notes */}
                      {therapyResults.general_notes && (
                        <div className="alert alert-info">
                          <h6>ℹ️ Allgemeine Hinweise:</h6>
                          <p className="mb-0">{therapyResults.general_notes}</p>
                        </div>
                      )}

                      {/* LLM Debug Information */}
                      {therapyResults.llm_debug && (
                        <div className="card mt-4">
                          <div className="card-header">
                            <button
                              className="btn btn-link text-decoration-none p-0 w-100 text-start"
                              type="button"
                              onClick={() =>
                                setLlmDebugExpanded(!llmDebugExpanded)
                              }
                            >
                              <h6 className="mb-0">
                                LLM Debug-Informationen{" "}
                                <small className="text-muted">
                                  (
                                  {llmDebugExpanded
                                    ? "Einklappen"
                                    : "Ausklappen"}
                                  )
                                </small>
                                <span className="float-end">
                                  {llmDebugExpanded ? "▲" : "▼"}
                                </span>
                              </h6>
                            </button>
                          </div>
                          {llmDebugExpanded && (
                            <div className="card-body">
                              {/* Model Information */}
                              {therapyResults.llm_debug.model && (
                                <div className="mb-3">
                                  <strong>🤖 Verwendetes Modell:</strong>
                                  <div className="bg-light p-2 rounded mt-1">
                                    <code>
                                      {therapyResults.llm_debug.model}
                                    </code>
                                  </div>
                                </div>
                              )}

                              {/* System Prompt */}
                              {therapyResults.llm_debug.system_prompt && (
                                <div className="mb-3">
                                  <strong>📋 System Prompt:</strong>
                                  <div
                                    className="bg-light p-3 rounded mt-1"
                                    style={{
                                      maxHeight: "300px",
                                      overflowY: "auto",
                                    }}
                                  >
                                    <pre
                                      className="mb-0"
                                      style={{
                                        fontSize: "0.875rem",
                                        whiteSpace: "pre-wrap",
                                        wordWrap: "break-word",
                                      }}
                                    >
                                      {therapyResults.llm_debug.system_prompt}
                                    </pre>
                                  </div>
                                </div>
                              )}

                              {/* User Prompt */}
                              {therapyResults.llm_debug.user_prompt && (
                                <div className="mb-3">
                                  <strong>
                                    👤 User Prompt (Klinischer Kontext):
                                  </strong>
                                  <div
                                    className="bg-light p-3 rounded mt-1"
                                    style={{
                                      maxHeight: "400px",
                                      overflowY: "auto",
                                    }}
                                  >
                                    <pre
                                      className="mb-0"
                                      style={{
                                        fontSize: "0.875rem",
                                        whiteSpace: "pre-wrap",
                                        wordWrap: "break-word",
                                      }}
                                    >
                                      {therapyResults.llm_debug.user_prompt}
                                    </pre>
                                  </div>
                                </div>
                              )}

                              <div className="text-muted">
                                <small>
                                  💡 Diese Informationen zeigen die exakten
                                  Prompts, die an das LLM gesendet wurden, um
                                  die Therapieempfehlungen zu generieren. Sie
                                  können zur Qualitätskontrolle und Verbesserung
                                  der Prompts verwendet werden.
                                </small>
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* LLM Processing Info */}
                      {therapyResults.processing_time_ms && (
                        <div className="text-muted text-center mt-3">
                          <small>
                            ⏱️ Verarbeitung: {therapyResults.processing_time_ms}
                            ms
                            {therapyResults.model_used &&
                              ` • Modell: ${therapyResults.model_used}`}
                          </small>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Query Test Tab */}
        {activeTab === "query-test" && (
          <div className="row">
            <div className="col-md-6">
              <div className="card">
                <div className="card-header">
                  <h5>Query-Generierung testen</h5>
                </div>
                <div className="card-body">
                  <form onSubmit={testQueryGeneration}>
                    <div className="mb-3">
                      <label className="form-label">Indikation</label>
                      <select
                        className="form-select"
                        value={searchForm.indication}
                        onChange={(e) =>
                          setSearchForm((prev) => ({
                            ...prev,
                            indication: e.target.value,
                          }))
                        }
                      >
                        {availableIndicationOptions.map((group) => (
                          <optgroup key={group.category} label={group.category}>
                            {group.options.map((indication) => (
                              <option
                                key={indication.value}
                                value={indication.value}
                              >
                                {indication.label}
                              </option>
                            ))}
                          </optgroup>
                        ))}
                      </select>
                    </div>

                    <div className="mb-3">
                      <label className="form-label">Schweregrad</label>
                      <select
                        className="form-select"
                        value={searchForm.severity}
                        onChange={(e) =>
                          setSearchForm((prev) => ({
                            ...prev,
                            severity: e.target.value,
                          }))
                        }
                      >
                        <option value="LEICHT">Leicht</option>
                        <option value="MITTELSCHWER">Mittelschwer</option>
                        <option value="SCHWER">Schwer</option>
                        <option value="SEPTISCH">Septisch</option>
                      </select>
                    </div>

                    <div className="mb-3">
                      <label className="form-label">Risikofaktoren</label>
                      {[
                        "ANTIBIOTISCHE_VORBEHANDLUNG",
                        "MRGN_VERDACHT",
                        "MRSA_VERDACHT",
                        "BEATMUNG",
                        "KATHETER",
                      ].map((factor) => (
                        <div key={factor} className="form-check">
                          <input
                            className="form-check-input"
                            type="checkbox"
                            id={factor}
                            checked={searchForm.risk_factors.includes(factor)}
                            onChange={(e) =>
                              handleRiskFactorChange(factor, e.target.checked)
                            }
                          />
                          <label className="form-check-label" htmlFor={factor}>
                            {factor.replace(/_/g, " ")}
                          </label>
                        </div>
                      ))}
                    </div>

                    <div className="mb-3">
                      <label className="form-label">Freitext (optional)</label>
                      <textarea
                        className="form-control"
                        rows="2"
                        value={searchForm.free_text}
                        onChange={(e) =>
                          setSearchForm((prev) => ({
                            ...prev,
                            free_text: e.target.value,
                          }))
                        }
                        placeholder="Zusätzliche Suchbegriffe..."
                      />
                    </div>

                    <button
                      type="submit"
                      className="btn btn-info w-100"
                      disabled={loading}
                    >
                      {loading ? (
                        <>
                          <span className="spinner-border spinner-border-sm me-2"></span>
                          Generiere Query...
                        </>
                      ) : (
                        "Query generieren"
                      )}
                    </button>
                  </form>
                </div>
              </div>
            </div>

            <div className="col-md-6">
              <div className="card">
                <div className="card-header">
                  <h5>Query-Analyse</h5>
                </div>
                <div className="card-body">
                  {queryTestResults ? (
                    queryTestResults.status === "success" ? (
                      <div>
                        <div className="mb-3">
                          <h6>MUST Terms (Kernkontext):</h6>
                          <div className="bg-light p-2 rounded">
                            {queryTestResults.query_analysis.must_terms.join(
                              ", "
                            )}
                          </div>
                        </div>

                        <div className="mb-3">
                          <h6>SHOULD Terms (Risikofaktoren):</h6>
                          <div className="bg-light p-2 rounded">
                            {queryTestResults.query_analysis.should_terms
                              .length > 0
                              ? queryTestResults.query_analysis.should_terms.join(
                                  ", "
                                )
                              : "Keine spezifischen Risikofaktoren"}
                          </div>
                        </div>

                        {queryTestResults.query_analysis.negative_terms &&
                          queryTestResults.query_analysis.negative_terms
                            .length > 0 && (
                            <div className="mb-3">
                              <h6>Negative Terms (Ausschluss):</h6>
                              <div className="bg-warning bg-opacity-25 p-2 rounded">
                                {queryTestResults.query_analysis.negative_terms.join(
                                  ", "
                                )}
                              </div>
                            </div>
                          )}

                        <div className="mb-3">
                          <h6>Boost Terms (Therapie/Dosierung):</h6>
                          <div className="bg-light p-2 rounded small">
                            {queryTestResults.query_analysis.boost_terms
                              .slice(0, 10)
                              .join(", ")}
                            ...
                          </div>
                        </div>

                        <div className="mb-3">
                          <h6>Finale Query:</h6>
                          <div
                            className="bg-secondary text-white p-2 rounded small"
                            style={{ maxHeight: "200px", overflow: "auto" }}
                          >
                            {queryTestResults.query_analysis.final_query}
                          </div>
                        </div>

                        <div className="row text-center">
                          <div className="col-4">
                            <div className="border p-2 rounded">
                              <strong>
                                {
                                  queryTestResults.query_analysis.term_counts
                                    .must
                                }
                              </strong>
                              <br />
                              <small>MUST</small>
                            </div>
                          </div>
                          <div className="col-4">
                            <div className="border p-2 rounded">
                              <strong>
                                {
                                  queryTestResults.query_analysis.term_counts
                                    .should
                                }
                              </strong>
                              <br />
                              <small>SHOULD</small>
                            </div>
                          </div>
                          <div className="col-4">
                            <div className="border p-2 rounded">
                              <strong>
                                {
                                  queryTestResults.query_analysis.term_counts
                                    .boost
                                }
                              </strong>
                              <br />
                              <small>BOOST</small>
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="alert alert-danger">
                        {queryTestResults.message}
                      </div>
                    )
                  ) : (
                    <div className="text-muted text-center">
                      <p>
                        Wählen Sie Parameter aus und klicken Sie "Query
                        generieren"
                      </p>
                      <p>
                        Dies zeigt die interne Query-Struktur ohne
                        Embeddings-Suche.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Search Tab */}
        {activeTab === "search" && (
          <div className="row">
            <div className="col-md-4">
              <div className="card">
                <div className="card-header">
                  <h5>Klinische Parameter</h5>
                </div>
                <div className="card-body">
                  <form onSubmit={handleSearch}>
                    <div className="mb-3">
                      <label className="form-label">Indikation</label>
                      <select
                        className="form-select"
                        value={searchForm.indication}
                        onChange={(e) =>
                          setSearchForm((prev) => ({
                            ...prev,
                            indication: e.target.value,
                          }))
                        }
                      >
                        {availableIndicationOptions.map((group) => (
                          <optgroup key={group.category} label={group.category}>
                            {group.options.map((indication) => (
                              <option
                                key={indication.value}
                                value={indication.value}
                              >
                                {indication.label}
                              </option>
                            ))}
                          </optgroup>
                        ))}
                      </select>
                    </div>

                    <div className="mb-3">
                      <label className="form-label">Schweregrad</label>
                      <select
                        className="form-select"
                        value={searchForm.severity}
                        onChange={(e) =>
                          setSearchForm((prev) => ({
                            ...prev,
                            severity: e.target.value,
                          }))
                        }
                      >
                        <option value="LEICHT">Leicht</option>
                        <option value="MITTELSCHWER">Mittelschwer</option>
                        <option value="SCHWER">Schwer</option>
                        <option value="SEPTISCH">Septisch</option>
                      </select>
                    </div>

                    <div className="mb-3">
                      <label className="form-label">
                        Infektionsort (optional)
                      </label>
                      <select
                        className="form-select"
                        value={searchForm.infection_site}
                        onChange={(e) =>
                          setSearchForm((prev) => ({
                            ...prev,
                            infection_site: e.target.value,
                          }))
                        }
                      >
                        <option value="">-- Nicht spezifiziert --</option>
                        <option value="LUNGE">Lunge</option>
                        <option value="BLUT">Blut</option>
                        <option value="HARNTRAKT">Harntrakt</option>
                        <option value="ZNS">ZNS</option>
                        <option value="HAUT_WEICHTEILE">Haut/Weichteile</option>
                      </select>
                    </div>

                    <div className="mb-3">
                      <label className="form-label">Risikofaktoren</label>
                      {[
                        {
                          key: "ANTIBIOTISCHE_VORBEHANDLUNG",
                          label: "Antibiotische Vorbehandlung",
                        },
                        { key: "MRGN_VERDACHT", label: "MRGN Verdacht" },
                        { key: "MRSA_VERDACHT", label: "MRSA Verdacht" },
                        { key: "BEATMUNG", label: "Beatmung" },
                        { key: "KATHETER", label: "Katheter" },
                      ].map((factor) => (
                        <div key={factor.key} className="form-check">
                          <input
                            className="form-check-input"
                            type="checkbox"
                            id={factor.key}
                            checked={searchForm.risk_factors.includes(
                              factor.key
                            )}
                            onChange={(e) =>
                              handleRiskFactorChange(
                                factor.key,
                                e.target.checked
                              )
                            }
                          />
                          <label
                            className="form-check-label"
                            htmlFor={factor.key}
                          >
                            {factor.label}
                          </label>
                        </div>
                      ))}
                    </div>

                    <div className="mb-3">
                      <label className="form-label">
                        Verdachtskeime (optional)
                      </label>
                      <input
                        type="text"
                        className="form-control"
                        value={searchForm.suspected_pathogens}
                        onChange={(e) =>
                          setSearchForm((prev) => ({
                            ...prev,
                            suspected_pathogens: e.target.value,
                          }))
                        }
                        placeholder="z.B. S. pneumoniae, H. influenzae"
                      />
                      <div className="form-text">Komma-getrennt</div>
                    </div>

                    <div className="mb-3">
                      <label className="form-label">Freitext (optional)</label>
                      <textarea
                        className="form-control"
                        rows="3"
                        value={searchForm.free_text}
                        onChange={(e) =>
                          setSearchForm((prev) => ({
                            ...prev,
                            free_text: e.target.value,
                          }))
                        }
                        placeholder="Zusätzliche Suchbegriffe..."
                      />
                    </div>

                    <button
                      type="submit"
                      className="btn btn-success w-100"
                      disabled={loading}
                    >
                      {loading ? (
                        <>
                          <span
                            className="spinner-border spinner-border-sm me-2"
                            role="status"
                          ></span>
                          Suche läuft...
                        </>
                      ) : (
                        "RAG Search starten"
                      )}
                    </button>
                  </form>
                </div>
              </div>
            </div>

            <div className="col-md-8">
              <div className="card">
                <div className="card-header">
                  <h5>Search Ergebnisse</h5>
                </div>
                <div className="card-body">
                  {!searchResults && (
                    <div className="text-muted text-center py-4">
                      Starten Sie eine Suche, um RAG-Ergebnisse zu sehen
                    </div>
                  )}

                  {searchResults?.error && (
                    <div className="alert alert-danger">
                      <strong>Fehler:</strong> {searchResults.error}
                    </div>
                  )}

                  {searchResults && !searchResults.error && (
                    <>
                      <div className="mb-3">
                        <strong>Query:</strong>{" "}
                        <code>{searchResults.query}</code>
                      </div>
                      <div className="mb-3 text-muted">
                        <small>
                          {searchResults.results.length} Ergebnisse von{" "}
                          {searchResults.total_chunks_searched} durchsuchten
                          Chunks ({searchResults.execution_time_ms.toFixed(1)}
                          ms)
                          {searchResults.dosing_tables &&
                            searchResults.dosing_tables.length > 0 && (
                              <>
                                {" "}
                                • {searchResults.dosing_tables.length}{" "}
                                Dosierungstabellen
                              </>
                            )}
                        </small>
                      </div>

                      {/* Dosing Tables Section */}
                      {searchResults.dosing_tables &&
                        searchResults.dosing_tables.length > 0 && (
                          <div className="mb-4">
                            <h6 className="text-primary">Dosierungstabellen</h6>
                            <div className="border rounded p-3 bg-light">
                              {searchResults.dosing_tables.map((table, idx) => (
                                <div
                                  key={idx}
                                  className="card mb-3 border-primary"
                                >
                                  <div className="card-header bg-primary text-white">
                                    <div className="d-flex justify-content-between align-items-start">
                                      <div>
                                        <span className="badge bg-light text-primary me-2">
                                          Score: {table.score.toFixed(3)}
                                        </span>
                                        <strong>Tabelle {idx + 1}</strong>
                                      </div>
                                      <button
                                        className="btn btn-sm btn-outline-light"
                                        type="button"
                                        onClick={(e) => {
                                          const content = e.target
                                            .closest(".card")
                                            .querySelector(
                                              ".dosing-table-content"
                                            );
                                          content.style.display =
                                            content.style.display === "none"
                                              ? "block"
                                              : "none";
                                          e.target.textContent =
                                            content.style.display === "none"
                                              ? "Tabelle zeigen"
                                              : "Tabelle verbergen";
                                        }}
                                      >
                                        Tabelle zeigen
                                      </button>
                                    </div>
                                    <div className="mt-2">
                                      <small>{table.table_name}</small>
                                    </div>
                                  </div>
                                  <div
                                    className="card-body dosing-table-content"
                                    style={{ display: "none" }}
                                  >
                                    <div className="table-responsive">
                                      <div
                                        dangerouslySetInnerHTML={{
                                          __html: table.table_html
                                            .replace(
                                              /DOSING TABLE \(LLM Format\):/g,
                                              ""
                                            )
                                            .replace(/END OF DOSING TABLE/g, "")
                                            .replace(/\| \*\*/g, "<th>")
                                            .replace(/\*\* \|/g, "</th>")
                                            .replace(/\| /g, "<td>")
                                            .replace(/ \|/g, "</td>")
                                            .replace(/\n/g, "</tr><tr>")
                                            .replace(/<tr><\/tr>/g, "")
                                            .replace(/^<\/tr>/, "")
                                            .replace(/<tr>$/, ""),
                                        }}
                                      />
                                    </div>
                                    {table.clinical_context &&
                                      Object.keys(table.clinical_context)
                                        .length > 0 && (
                                        <div className="mt-3">
                                          <h6>Klinischer Kontext:</h6>
                                          <div className="d-flex flex-wrap gap-2">
                                            {table.clinical_context
                                              .indication && (
                                              <span className="badge bg-info">
                                                {
                                                  table.clinical_context
                                                    .indication
                                                }
                                              </span>
                                            )}
                                            {table.clinical_context
                                              .severity && (
                                              <span className="badge bg-warning">
                                                {
                                                  table.clinical_context
                                                    .severity
                                                }
                                              </span>
                                            )}
                                            {table.clinical_context
                                              .infection_site && (
                                              <span className="badge bg-success">
                                                {
                                                  table.clinical_context
                                                    .infection_site
                                                }
                                              </span>
                                            )}
                                            {table.clinical_context.keywords &&
                                              table.clinical_context.keywords
                                                .length > 0 &&
                                              table.clinical_context.keywords.map(
                                                (keyword, kidx) => (
                                                  <span
                                                    key={kidx}
                                                    className="badge bg-secondary"
                                                  >
                                                    {keyword}
                                                  </span>
                                                )
                                              )}
                                          </div>
                                        </div>
                                      )}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                      {/* Regular Chunks Section */}
                      <h6 className="text-secondary">Leitlinien-Chunks</h6>
                      {searchResults.results.length === 0 ? (
                        <div className="alert alert-warning">
                          Keine relevanten Chunks gefunden. Versuchen Sie andere
                          Parameter.
                        </div>
                      ) : (
                        <div>
                          {searchResults.results.map((result, idx) => (
                            <div key={idx} className="card mb-3">
                              <div className="card-header">
                                <div className="d-flex justify-content-between align-items-start">
                                  <div>
                                    <span className="badge bg-primary me-2">
                                      Score: {result.score.toFixed(3)}
                                    </span>
                                    <strong>{result.guideline_id}</strong>
                                  </div>
                                  <button
                                    className="btn btn-sm btn-outline-secondary"
                                    type="button"
                                    onClick={(e) => {
                                      const content = e.target
                                        .closest(".card")
                                        .querySelector(".card-body");
                                      content.style.display =
                                        content.style.display === "none"
                                          ? "block"
                                          : "none";
                                      e.target.textContent =
                                        content.style.display === "none"
                                          ? "Zeigen"
                                          : "Verbergen";
                                    }}
                                  >
                                    Zeigen
                                  </button>
                                </div>
                                {(result.section_path || result.page) && (
                                  <div className="mt-1">
                                    <small className="text-muted">
                                      {result.section_path &&
                                        `${result.section_path}`}
                                      {result.page && ` • Seite ${result.page}`}
                                    </small>
                                  </div>
                                )}
                              </div>
                              <div
                                className="card-body"
                                style={{ display: "none" }}
                              >
                                <div className="bg-light p-3 rounded">
                                  <pre
                                    className="mb-0"
                                    style={{
                                      whiteSpace: "pre-wrap",
                                      fontSize: "0.9em",
                                    }}
                                  >
                                    {result.snippet}
                                  </pre>
                                </div>
                                <div className="mt-2">
                                  <small className="text-muted">
                                    <strong>Chunk ID:</strong> {result.chunk_id}
                                  </small>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Settings Tab */}
        {activeTab === "settings" && (
          <div className="card">
            <div className="card-header">
              <h5>LLM Konfiguration</h5>
            </div>
            <div className="card-body">
              <div className="mb-3">
                <label className="form-label">LLM Endpoint URL</label>
                <input
                  type="url"
                  className="form-control"
                  value={llmConfig.endpoint}
                  onChange={(e) =>
                    handleLlmConfigChange("endpoint", e.target.value)
                  }
                  placeholder="https://api.novita.ai/v3/openai/chat/completions"
                />
                <div className="form-text">
                  Novita AI oder OpenAI-kompatible API Endpoint URL
                </div>
              </div>

              <div className="mb-3">
                <label className="form-label">Model Name</label>
                <input
                  type="text"
                  className="form-control"
                  value={llmConfig.model}
                  onChange={(e) =>
                    handleLlmConfigChange("model", e.target.value)
                  }
                  placeholder="openai/gpt-oss-120b"
                />
                <div className="form-text">
                  Beispiele: openai/gpt-oss-120b,
                  meta-llama/llama-3.1-70b-instruct, gpt-4o, gpt-3.5-turbo
                </div>
              </div>

              <div className="row">
                <div className="col-md-6">
                  <div className="mb-3">
                    <label className="form-label">Max Tokens</label>
                    <input
                      type="number"
                      className="form-control"
                      value={llmConfig.max_tokens}
                      onChange={(e) =>
                        handleLlmConfigChange(
                          "max_tokens",
                          parseInt(e.target.value)
                        )
                      }
                      min="1000"
                      max="50000"
                    />
                    <div className="form-text">
                      Maximale Anzahl von Tokens für die Antwort (1000-50000)
                    </div>
                  </div>
                </div>
                <div className="col-md-6">
                  <div className="mb-3">
                    <label className="form-label">Temperature</label>
                    <input
                      type="number"
                      className="form-control"
                      value={llmConfig.temperature}
                      onChange={(e) =>
                        handleLlmConfigChange(
                          "temperature",
                          parseFloat(e.target.value)
                        )
                      }
                      min="0"
                      max="1"
                      step="0.1"
                    />
                    <div className="form-text">
                      Kreativität des LLM (0.0 = deterministisch, 1.0 = kreativ)
                    </div>
                  </div>
                </div>
              </div>

              <div className="d-flex gap-2">
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={saveLlmConfig}
                >
                  Konfiguration speichern
                </button>
                {llmConfigSaved && (
                  <div className="alert alert-success mb-0 py-2" role="alert">
                    Konfiguration erfolgreich gespeichert!
                  </div>
                )}
              </div>

              <hr />

              <div className="mt-4">
                <h6>Aktuelle Konfiguration</h6>
                <div className="bg-light p-3 rounded">
                  <pre style={{ fontSize: "0.875rem", marginBottom: 0 }}>
                    {JSON.stringify(llmConfig, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
