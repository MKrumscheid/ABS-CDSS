import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { ThemeProvider } from "@mui/material/styles";
import { CssBaseline, Box } from "@mui/material";
import medicalTheme from "./theme/medicalTheme";
import Layout from "./components/Layout/Layout";
import TherapyRecommendation from "./pages/TherapyRecommendation";
import SavedRequests from "./pages/SavedRequests";
import RagStatusBanner from "./components/RagStatusBanner/RagStatusBanner";

function EnduserApp() {
  return (
    <ThemeProvider theme={medicalTheme}>
      <CssBaseline />
      <RagStatusBanner />
      <Router>
        <Layout>
          <Box
            sx={{
              width: "100%",
              minHeight: "100vh",
              bgcolor: "background.default",
            }}
          >
            <Routes>
              <Route path="/" element={<Navigate to="/therapy" replace />} />
              <Route path="/therapy" element={<TherapyRecommendation />} />
              <Route path="/saved" element={<SavedRequests />} />
            </Routes>
          </Box>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default EnduserApp;
