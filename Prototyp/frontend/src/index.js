import React from "react";
import ReactDOM from "react-dom/client";
import "bootstrap/dist/css/bootstrap.min.css";
import App from "./App";
import EnduserApp from "./EnduserApp";

// Determine which app to render based on environment variable
const isEnduserMode = process.env.REACT_APP_MODE === "enduser";
const AppComponent = isEnduserMode ? EnduserApp : App;

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <AppComponent />
  </React.StrictMode>
);
