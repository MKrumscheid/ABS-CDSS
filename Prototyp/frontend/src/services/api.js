import axios from "axios";

const API_BASE =
  process.env.NODE_ENV === "production" ? "" : "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 180000, // 3 minutes timeout for LLM requests
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error("API Request Error:", error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error("API Response Error:", error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Therapy Recommendation API
export const therapyAPI = {
  // Generate therapy recommendation with real-time progress
  generateRecommendationStream: async (requestData, onProgress) => {
    const baseUrl =
      process.env.NODE_ENV === "production" ? "" : "http://localhost:8000";
    const url = `${baseUrl}/therapy/recommend-stream`;

    return new Promise((resolve, reject) => {
      fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }

          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = "";

          function readStream() {
            return reader.read().then(({ done, value }) => {
              if (done) {
                return;
              }

              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split("\n");

              // Keep the last incomplete line in buffer
              buffer = lines.pop() || "";

              for (const line of lines) {
                if (line.startsWith("data: ")) {
                  try {
                    const data = JSON.parse(line.slice(6));

                    if (data.type === "progress") {
                      onProgress(data.message);
                    } else if (data.type === "result") {
                      resolve(data.data);
                      return;
                    } else if (data.type === "complete") {
                      // Stream completed successfully
                      return;
                    } else if (data.type === "error") {
                      reject(new Error(data.message));
                      return;
                    }
                  } catch (e) {
                    console.warn("Failed to parse SSE data:", line);
                  }
                }
              }

              return readStream();
            });
          }

          return readStream();
        })
        .catch((error) => {
          reject(error);
        });
    });
  },

  // Generate therapy recommendation (fallback)
  generateRecommendation: async (requestData) => {
    const response = await api.post("/therapy/recommend", requestData, {
      timeout: 300000, // 5 minutes for therapy recommendation
    });
    return response.data;
  },

  // Save therapy recommendation
  saveRecommendation: async (saveData) => {
    const response = await api.post("/therapy/save", saveData);
    return response.data;
  },

  // Get saved therapy recommendations (list)
  getSavedRecommendations: async () => {
    const response = await api.get("/therapy/saved");
    return response.data;
  },

  // Get specific saved therapy recommendation
  getSavedRecommendation: async (id) => {
    const response = await api.get(`/therapy/saved/${id}`);
    return response.data;
  },

  // Delete saved therapy recommendation
  deleteSavedRecommendation: async (id) => {
    const response = await api.delete(`/therapy/saved/${id}`);
    return response.data;
  },
};

// Patient API
export const patientAPI = {
  // Search patients
  searchPatients: async (searchData) => {
    const response = await api.post("/patients/search", searchData);
    return response.data;
  },

  // Get patient details
  getPatientDetails: async (patientId) => {
    const response = await api.get(`/patients/${patientId}`);
    return response.data;
  },
};

// Available options for dropdowns
export const availableIndications = [
  // Respiratorische Infektionen
  {
    category: "Respiratorische Infektionen",
    options: [
      {
        value: "AMBULANT_ERWORBENE_PNEUMONIE",
        label: "CAP (Ambulant erworbene Pneumonie)",
      },
      {
        value: "NOSOKOMIAL_ERWORBENE_PNEUMONIE",
        label: "HAP (Nosokomial erworbene Pneumonie)",
      },
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
      { value: "OHRMUSCHELPERICHONDRITIS", label: "Ohrmuschelperichondritis" },
      { value: "NASENFURUNKEL", label: "Nasenfurunkel" },
      { value: "PERITONSILLITIS", label: "Peritonsillitis" },
      { value: "PERITONSILLARABSZESS", label: "Peritonsillarabszess" },
      {
        value: "BAKTERIELLE_SINUSITIDEN_UND_KOMPLIKATIONEN",
        label: "Bakterielle Sinusitiden und Komplikationen",
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
      { value: "HAEMATOGENE_OSTEOMYELITIS", label: "Hämatogene Osteomyelitis" },
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
      { value: "BAKTERIELLE_ENDOKARDITIS", label: "Bakterielle Endokarditis" },
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

export const severityOptions = [
  { value: "LEICHT", label: "Leicht" },
  { value: "MITTELSCHWER", label: "Mittelschwer" },
  { value: "SCHWER", label: "Schwer" },
  { value: "SEPTISCH", label: "Septisch" },
];

export const riskFactorOptions = [
  {
    value: "ANTIBIOTISCHE_VORBEHANDLUNG",
    label: "Antibiotische Vorbehandlung (3 Monate)",
  },
  { value: "MRGN_VERDACHT", label: "MRGN-Verdacht" },
  { value: "MRSA_VERDACHT", label: "MRSA-Verdacht" },
  { value: "BEATMUNG", label: "Beatmung" },
  { value: "KATHETER", label: "Katheter" },
];

export default api;
