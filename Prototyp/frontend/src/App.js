import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

const API_BASE =
  process.env.NODE_ENV === "production" ? "" : "http://localhost:8000";

function App() {
  const [activeTab, setActiveTab] = useState("upload");
  const [uploadStatus, setUploadStatus] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [guidelines, setGuidelines] = useState([]);
  const [deleteStatus, setDeleteStatus] = useState("");
  const [queryTestResults, setQueryTestResults] = useState(null);

  // Available indications - easily extensible
  const availableIndicationOptions = [
    {
      value: "CAP",
      label: "CAP (Ambulant erworbene Pneumonie)",
    },
    {
      value: "HAP",
      label: "HAP (Nosokomial erworbene Pneumonie)",
    },
    {
      value: "AKUTE_EXAZERBATION_COPD",
      label: "AECOPD (Akute Exazerbation der COPD)",
    },
  ];

  // Form states
  const [uploadFile, setUploadFile] = useState(null);
  const [guidelineId, setGuidelineId] = useState("");
  const [selectedIndications, setSelectedIndications] = useState([]); // Für Upload - keine Vorauswahl
  const [indicationSearch, setIndicationSearch] = useState("");
  const [indicationDropdownOpen, setIndicationDropdownOpen] = useState(false);
  const [searchForm, setSearchForm] = useState({
    indication: "CAP",
    severity: "MITTELSCHWER",
    infection_site: "",
    risk_factors: [],
    suspected_pathogens: "",
    free_text: "",
  });

  useEffect(() => {
    loadStats();
    loadGuidelines();
    
    // Close dropdown when clicking outside
    const handleClickOutside = (event) => {
      if (!event.target.closest('.position-relative')) {
        setIndicationDropdownOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Debug: Monitor selectedIndications changes
  useEffect(() => {
    console.log("🎯 selectedIndications changed:", selectedIndications);
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
      setDeleteStatus("❌ Fehler beim Laden der Leitlinien");
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
      const response = await axios.delete(
        `${API_BASE}/guidelines/${guidelineId}`
      );

      if (response.data.success) {
        setDeleteStatus(`✅ ${response.data.message}`);
        loadGuidelines();
        loadStats();
      } else {
        setDeleteStatus(`❌ ${response.data.message}`);
      }
    } catch (error) {
      setDeleteStatus(`❌ Fehler beim Löschen: ${error.message}`);
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
      const response = await axios.delete(`${API_BASE}/guidelines`);

      if (response.data.success) {
        setDeleteStatus(`✅ ${response.data.message}`);
        setGuidelines([]);
        loadStats();
      } else {
        setDeleteStatus(`❌ ${response.data.message}`);
      }
    } catch (error) {
      setDeleteStatus(`❌ Fehler beim Löschen: ${error.message}`);
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
      indication:
        searchForm.indication === "CAP"
          ? "AMBULANT_ERWORBENE_PNEUMONIE"
          : "NOSOKOMIAL_ERWORBENE_PNEUMONIE",
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
    console.log("🔄 handleIndicationChange called:", { indication, checked });
    if (checked) {
      const newSelection = [...selectedIndications, indication];
      console.log("➕ Adding indication, new selection:", newSelection);
      setSelectedIndications(newSelection);
    } else {
      const newSelection = selectedIndications.filter((ind) => ind !== indication);
      console.log("➖ Removing indication, new selection:", newSelection);
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

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) {
      setUploadStatus("Bitte wählen Sie eine Datei aus.");
      return;
    }

    // Validate indications
    if (selectedIndications.length === 0) {
      setUploadStatus("❌ Bitte wählen Sie mindestens eine Indikation aus.");
      return;
    }

    console.log("📋 Selected indications:", selectedIndications); // Debug log

    // Validate file type
    const fileName = uploadFile.name.toLowerCase();
    if (!fileName.endsWith(".txt") && !fileName.endsWith(".md")) {
      setUploadStatus("❌ Nur .txt und .md Dateien werden unterstützt.");
      return;
    }

    setLoading(true);
    setUploadStatus("");

    const formData = new FormData();
    formData.append("file", uploadFile);
    if (guidelineId) {
      formData.append("guideline_id", guidelineId);
    }
    // Use selected indications instead of hardcoded values
    const indicationsString = selectedIndications.join(",");
    console.log("📤 Sending indications string:", indicationsString); // Debug what we send
    console.log("📤 FormData indications:", indicationsString); // Debug FormData
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
        const message = `✅ Erfolgreich verarbeitet (${fileType}): ${response.data.chunks_created} Chunks erstellt`;
        setUploadStatus(message);
        resetUploadForm(); // Use new reset function
        loadStats(); // Reload stats
        loadGuidelines(); // Reload guidelines list
      } else {
        setUploadStatus(`❌ Fehler: ${response.data.message}`);
      }
    } catch (error) {
      setUploadStatus(
        `❌ Upload-Fehler: ${error.response?.data?.detail || error.message}`
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
      const mapping = {
        CAP: "AMBULANT_ERWORBENE_PNEUMONIE",
        HAP: "NOSOKOMIAL_ERWORBENE_PNEUMONIE",
      };
      return mapping[indication] || indication;
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

  return (
    <div className="App">
      <nav className="navbar navbar-expand-lg navbar-dark bg-primary">
        <div className="container">
          <span className="navbar-brand mb-0 h1">
            🏥 RAG Test Pipeline - Clinical Decision Support
          </span>
        </div>
      </nav>

      <div className="container mt-4">
        {/* Stats Card */}
        {stats && (
          <div className="card mb-4">
            <div className="card-body">
              <h5 className="card-title">📊 System Status</h5>
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
                  <strong>Verfügbare Leitlinien:</strong>
                  <ul className="list-unstyled mt-2">
                    {stats.guidelines.map((guideline, idx) => (
                      <li key={idx} className="small">
                        📄 {guideline.title} ({guideline.indications.join(", ")}
                        )
                        {guideline.pages && (
                          <span className="text-muted">
                            {" "}
                            • {guideline.pages} Seiten
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <ul className="nav nav-tabs mb-4">
          <li className="nav-item">
            <button
              className={`nav-link ${activeTab === "upload" ? "active" : ""}`}
              onClick={() => setActiveTab("upload")}
            >
              📁 Leitlinien Upload
            </button>
          </li>
          <li className="nav-item">
            <button
              className={`nav-link ${activeTab === "manage" ? "active" : ""}`}
              onClick={() => {
                setActiveTab("manage");
                loadGuidelines();
              }}
            >
              🗂️ Leitlinien Verwalten
            </button>
          </li>
          <li className="nav-item">
            <button
              className={`nav-link ${
                activeTab === "query-test" ? "active" : ""
              }`}
              onClick={() => setActiveTab("query-test")}
            >
              🧪 Query Test
            </button>
          </li>
          <li className="nav-item">
            <button
              className={`nav-link ${activeTab === "search" ? "active" : ""}`}
              onClick={() => setActiveTab("search")}
            >
              🔍 RAG Search Test
            </button>
          </li>
        </ul>

        {/* Upload Tab */}
        {activeTab === "upload" && (
          <div className="card">
            <div className="card-header">
              <h5>📄 Leitlinien-Upload und Verarbeitung</h5>
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
                      style={{ right: "5px", top: "50%", transform: "translateY(-50%)" }}
                      onClick={() => setIndicationDropdownOpen(!indicationDropdownOpen)}
                    >
                      ▼
                    </button>
                    
                    {indicationDropdownOpen && (
                      <div className="card position-absolute w-100 mt-1" style={{ zIndex: 1000 }}>
                        <div className="card-body p-2" style={{ maxHeight: "200px", overflowY: "auto" }}>
                          {/* Select All Option */}
                          <div className="form-check mb-2 border-bottom pb-2">
                            <input
                              className="form-check-input"
                              type="checkbox"
                              id="select-all-indications"
                              checked={selectedIndications.length === availableIndicationOptions.length}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedIndications(availableIndicationOptions.map(ind => ind.value));
                                } else {
                                  setSelectedIndications([]);
                                }
                              }}
                            />
                            <label className="form-check-label fw-bold" htmlFor="select-all-indications">
                              🔘 Alle auswählen
                            </label>
                          </div>
                          
                          {/* Filtered Indications */}
                          {availableIndicationOptions
                            .filter(indication => 
                              indication.label.toLowerCase().includes(indicationSearch.toLowerCase()) ||
                              indication.value.toLowerCase().includes(indicationSearch.toLowerCase())
                            )
                            .map((indication) => (
                              <div key={indication.value} className="form-check">
                                <input
                                  className="form-check-input"
                                  type="checkbox"
                                  id={`indication-${indication.value}`}
                                  checked={selectedIndications.includes(indication.value)}
                                  onChange={(e) =>
                                    handleIndicationChange(
                                      indication.value,
                                      e.target.checked
                                    )
                                  }
                                />
                                <label className="form-check-label" htmlFor={`indication-${indication.value}`}>
                                  {indication.label}
                                </label>
                              </div>
                            ))}
                          
                          {/* No results message */}
                          {availableIndicationOptions
                            .filter(indication => 
                              indication.label.toLowerCase().includes(indicationSearch.toLowerCase()) ||
                              indication.value.toLowerCase().includes(indicationSearch.toLowerCase())
                            ).length === 0 && (
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
                      <small className="text-muted">✅ Ausgewählt: </small>
                      <div className="d-flex flex-wrap gap-1 mt-1">
                        {selectedIndications.map((indicationValue) => {
                          const indication = availableIndicationOptions.find(ind => ind.value === indicationValue);
                          return (
                            <span key={indicationValue} className="badge bg-success">
                              {indication ? indication.label : indicationValue}
                              <button
                                type="button"
                                className="btn-close btn-close-white ms-1"
                                style={{ fontSize: "0.6em" }}
                                onClick={() => {
                                  setSelectedIndications(
                                    selectedIndications.filter((ind) => ind !== indicationValue)
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
                      ⚠️ Mindestens eine Indikation muss ausgewählt werden.
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
                    `🚀 Upload & Verarbeitung starten (${selectedIndications.join(
                      ", "
                    )})`
                  )}
                </button>
              </form>

              {uploadStatus && (
                <div
                  className={`alert mt-3 ${
                    uploadStatus.includes("❌")
                      ? "alert-danger"
                      : "alert-success"
                  }`}
                >
                  {uploadStatus}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Manage Tab */}
        {activeTab === "manage" && (
          <div className="card">
            <div className="card-header">
              <h5>🗂️ Leitlinien Verwaltung</h5>
            </div>
            <div className="card-body">
              <div className="row mb-4">
                <div className="col-md-6">
                  <button
                    className="btn btn-outline-info w-100"
                    onClick={loadGuidelines}
                    disabled={loading}
                  >
                    🔄 Liste aktualisieren
                  </button>
                </div>
                <div className="col-md-6">
                  <button
                    className="btn btn-danger w-100"
                    onClick={deleteAllGuidelines}
                    disabled={loading}
                  >
                    🗑️ ALLE Leitlinien löschen
                  </button>
                </div>
              </div>

              {deleteStatus && (
                <div
                  className={`alert ${
                    deleteStatus.includes("❌")
                      ? "alert-danger"
                      : "alert-success"
                  }`}
                >
                  {deleteStatus}
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
                            <span className="badge bg-primary me-1">
                              {guideline.indications.join(", ")}
                            </span>
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
                              🗑️ Löschen
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

        {/* Query Test Tab */}
        {activeTab === "query-test" && (
          <div className="row">
            <div className="col-md-6">
              <div className="card">
                <div className="card-header">
                  <h5>🧪 Query-Generierung testen</h5>
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
                        <option value="CAP">
                          Ambulant erworbene Pneumonie
                        </option>
                        <option value="HAP">
                          Nosokomial erworbene Pneumonie
                        </option>
                        <option value="AKUTE_EXAZERBATION_COPD">
                          Akute Exazerbation der COPD
                        </option>
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
                        "🧪 Query generieren"
                      )}
                    </button>
                  </form>
                </div>
              </div>
            </div>

            <div className="col-md-6">
              <div className="card">
                <div className="card-header">
                  <h5>📊 Query-Analyse</h5>
                </div>
                <div className="card-body">
                  {queryTestResults ? (
                    queryTestResults.status === "success" ? (
                      <div>
                        <div className="mb-3">
                          <h6>🎯 MUST Terms (Kernkontext):</h6>
                          <div className="bg-light p-2 rounded">
                            {queryTestResults.query_analysis.must_terms.join(
                              ", "
                            )}
                          </div>
                        </div>

                        <div className="mb-3">
                          <h6>🔍 SHOULD Terms (Risikofaktoren):</h6>
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
                              <h6>❌ NEGATIVE Terms (Ausschluss):</h6>
                              <div className="bg-warning bg-opacity-25 p-2 rounded">
                                {queryTestResults.query_analysis.negative_terms.join(
                                  ", "
                                )}
                              </div>
                            </div>
                          )}

                        <div className="mb-3">
                          <h6>⚡ BOOST Terms (Therapie/Dosierung):</h6>
                          <div className="bg-light p-2 rounded small">
                            {queryTestResults.query_analysis.boost_terms
                              .slice(0, 10)
                              .join(", ")}
                            ...
                          </div>
                        </div>

                        <div className="mb-3">
                          <h6>📝 Finale Query:</h6>
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
                        ❌ {queryTestResults.message}
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
                  <h5>🔍 Klinische Parameter</h5>
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
                        <option value="CAP">
                          CAP - Ambulant erworbene Pneumonie
                        </option>
                        <option value="HAP">
                          HAP - Nosokomial erworbene Pneumonie
                        </option>
                        <option value="AKUTE_EXAZERBATION_COPD">
                          AECOPD - Akute Exazerbation der COPD
                        </option>
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
                        "🔍 RAG Search starten"
                      )}
                    </button>
                  </form>
                </div>
              </div>
            </div>

            <div className="col-md-8">
              <div className="card">
                <div className="card-header">
                  <h5>📋 Search Ergebnisse</h5>
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
                          {searchResults.dosing_tables && searchResults.dosing_tables.length > 0 && (
                            <> • {searchResults.dosing_tables.length} Dosierungstabellen</>
                          )}
                        </small>
                      </div>

                      {/* Dosing Tables Section */}
                      {searchResults.dosing_tables && searchResults.dosing_tables.length > 0 && (
                        <div className="mb-4">
                          <h6 className="text-primary">💊 Dosierungstabellen</h6>
                          <div className="border rounded p-3 bg-light">
                            {searchResults.dosing_tables.map((table, idx) => (
                              <div key={idx} className="card mb-3 border-primary">
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
                                          .querySelector(".dosing-table-content");
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
                                          .replace(/DOSING TABLE \(LLM Format\):/g, '')
                                          .replace(/END OF DOSING TABLE/g, '')
                                          .replace(/\| \*\*/g, '<th>')
                                          .replace(/\*\* \|/g, '</th>')
                                          .replace(/\| /g, '<td>')
                                          .replace(/ \|/g, '</td>')
                                          .replace(/\n/g, '</tr><tr>')
                                          .replace(/<tr><\/tr>/g, '')
                                          .replace(/^<\/tr>/, '')
                                          .replace(/<tr>$/, '')
                                      }} 
                                    />
                                  </div>
                                  {table.clinical_context && Object.keys(table.clinical_context).length > 0 && (
                                    <div className="mt-3">
                                      <h6>🎯 Klinischer Kontext:</h6>
                                      <div className="d-flex flex-wrap gap-2">
                                        {table.clinical_context.indication && (
                                          <span className="badge bg-info">
                                            {table.clinical_context.indication}
                                          </span>
                                        )}
                                        {table.clinical_context.severity && (
                                          <span className="badge bg-warning">
                                            {table.clinical_context.severity}
                                          </span>
                                        )}
                                        {table.clinical_context.infection_site && (
                                          <span className="badge bg-success">
                                            {table.clinical_context.infection_site}
                                          </span>
                                        )}
                                        {table.clinical_context.keywords && table.clinical_context.keywords.length > 0 && (
                                          table.clinical_context.keywords.map((keyword, kidx) => (
                                            <span key={kidx} className="badge bg-secondary">
                                              {keyword}
                                            </span>
                                          ))
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
                      <h6 className="text-secondary">📋 Leitlinien-Chunks</h6>
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
                                        `📑 ${result.section_path}`}
                                      {result.page &&
                                        ` • 📄 Seite ${result.page}`}
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
      </div>
    </div>
  );
}

export default App;
