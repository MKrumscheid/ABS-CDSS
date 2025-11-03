import { createTheme } from "@mui/material/styles";

// Medical-themed color palette
export const medicalTheme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#1565c0",
      light: "#5e92f3",
      dark: "#003c8f",
      contrastText: "#ffffff",
    },
    secondary: {
      main: "#2e7d32",
      light: "#60ad5e",
      dark: "#005005",
      contrastText: "#ffffff",
    },
    error: {
      main: "#d32f2f",
      light: "#ff6659",
      dark: "#9a0007",
    },
    warning: {
      main: "#f57c00",
      light: "#ffad42",
      dark: "#bb4d00",
    },
    info: {
      main: "#0288d1",
      light: "#5eb8ff",
      dark: "#005b9f",
    },
    success: {
      main: "#388e3c",
      light: "#6abf69",
      dark: "#00600f",
    },
    background: {
      default: "#f8f9fa",
      paper: "#ffffff",
    },
    text: {
      primary: "#212121",
      secondary: "#757575",
    },
  },
  typography: {
    fontFamily: [
      "Inter",
      "-apple-system",
      "BlinkMacSystemFont",
      '"Segoe UI"',
      "Roboto",
      '"Helvetica Neue"',
      "Arial",
      "sans-serif",
    ].join(","),
    h1: {
      fontWeight: 600,
      fontSize: "2.5rem",
      lineHeight: 1.2,
      color: "#1565c0",
    },
    h2: {
      fontWeight: 600,
      fontSize: "2rem",
      lineHeight: 1.3,
      color: "#1565c0",
    },
    h3: {
      fontWeight: 600,
      fontSize: "1.75rem",
      lineHeight: 1.3,
      color: "#212121",
    },
    h4: {
      fontWeight: 500,
      fontSize: "1.5rem",
      lineHeight: 1.4,
      color: "#212121",
    },
    h5: {
      fontWeight: 500,
      fontSize: "1.25rem",
      lineHeight: 1.4,
      color: "#212121",
    },
    h6: {
      fontWeight: 500,
      fontSize: "1.125rem",
      lineHeight: 1.4,
      color: "#212121",
    },
    body1: {
      fontSize: "1rem",
      lineHeight: 1.5,
      color: "#212121",
    },
    body2: {
      fontSize: "0.875rem",
      lineHeight: 1.43,
      color: "#757575",
    },
    button: {
      fontWeight: 500,
      textTransform: "none",
      fontSize: "0.875rem",
    },
  },
  shape: {
    borderRadius: 8,
  },
  spacing: 8,
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: "10px 24px",
          boxShadow: "none",
          "&:hover": {
            boxShadow: "0px 2px 4px rgba(0, 0, 0, 0.1)",
          },
        },
        contained: {
          "&:hover": {
            boxShadow: "0px 4px 8px rgba(0, 0, 0, 0.15)",
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: "0px 2px 8px rgba(0, 0, 0, 0.08)",
          "&:hover": {
            boxShadow: "0px 4px 16px rgba(0, 0, 0, 0.12)",
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          "& .MuiOutlinedInput-root": {
            borderRadius: 8,
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          fontWeight: 500,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: "0px 1px 4px rgba(0, 0, 0, 0.1)",
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        elevation1: {
          boxShadow: "0px 1px 4px rgba(0, 0, 0, 0.08)",
        },
        elevation2: {
          boxShadow: "0px 2px 8px rgba(0, 0, 0, 0.1)",
        },
        elevation3: {
          boxShadow: "0px 4px 12px rgba(0, 0, 0, 0.12)",
        },
      },
    },
  },
});

export default medicalTheme;
