import React, { useState } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  IconButton,
  useTheme,
  useMediaQuery,
} from "@mui/material";
import {
  Menu as MenuIcon,
  LocalHospital as HospitalIcon,
  BookmarkBorder as SavedIcon,
  Close as CloseIcon,
} from "@mui/icons-material";
import { useNavigate, useLocation } from "react-router-dom";

const drawerWidth = 280;

function Layout({ children }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const navigate = useNavigate();
  const location = useLocation();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const menuItems = [
    {
      text: "Therapie-Empfehlung",
      icon: <HospitalIcon />,
      path: "/therapy",
      description: "Neue Antibiotika-Empfehlung erstellen",
    },
    {
      text: "Gespeicherte Anfragen",
      icon: <SavedIcon />,
      path: "/saved",
      description: "Frühere Empfehlungen anzeigen",
    },
  ];

  const handleNavigation = (path) => {
    navigate(path);
    if (isMobile) {
      setMobileOpen(false);
    }
  };

  const drawer = (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      {/* Drawer Header */}
      <Box
        sx={{
          p: 2,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderBottom: 1,
          borderColor: "divider",
          bgcolor: "primary.main",
          color: "primary.contrastText",
          minHeight: { xs: 56, sm: 64 },
        }}
      >
        <Typography
          variant="h6"
          noWrap
          component="div"
          sx={{
            fontWeight: 600,
            fontSize: { xs: "1.1rem", sm: "1.25rem" },
            color: "white",
          }}
        >
          ABS-CDSS
        </Typography>
        {isMobile && (
          <IconButton
            color="inherit"
            onClick={handleDrawerToggle}
            sx={{ ml: 1 }}
          >
            <CloseIcon />
          </IconButton>
        )}
      </Box>

      {/* Navigation Menu */}
      <List sx={{ flex: 1, pt: 1 }}>
        {menuItems.map((item) => (
          <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton
              onClick={() => handleNavigation(item.path)}
              selected={location.pathname === item.path}
              sx={{
                mx: 1,
                borderRadius: 2,
                "&.Mui-selected": {
                  bgcolor: "primary.light",
                  color: "primary.contrastText",
                  "&:hover": {
                    bgcolor: "primary.main",
                  },
                },
                "&:hover": {
                  bgcolor: "action.hover",
                },
              }}
            >
              <ListItemIcon
                sx={{
                  color:
                    location.pathname === item.path
                      ? "primary.contrastText"
                      : "primary.main",
                  minWidth: 40,
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.text}
                secondary={item.description}
                primaryTypographyProps={{
                  fontSize: "0.95rem",
                  fontWeight: location.pathname === item.path ? 600 : 500,
                }}
                secondaryTypographyProps={{
                  fontSize: "0.8rem",
                  color:
                    location.pathname === item.path
                      ? "primary.contrastText"
                      : "text.secondary",
                  opacity: 0.8,
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      {/* Footer */}
      <Box
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: "divider",
          bgcolor: "grey.50",
        }}
      >
        <Typography variant="body2" color="text.secondary" align="center">
          Antibiotika Clinical Decision Support
        </Typography>
        <Typography
          variant="caption"
          color="text.secondary"
          align="center"
          display="block"
          sx={{ mt: 0.5 }}
        >
          Version 2.0 - Enduser Interface
        </Typography>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: "flex" }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        elevation={2}
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
          height: { xs: 56, sm: 64 },
        }}
      >
        <Toolbar sx={{ minHeight: { xs: 56, sm: 64 }, px: { xs: 2, md: 3 } }}>
          {isMobile && (
            <IconButton
              color="inherit"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          <HospitalIcon sx={{ mr: 1.5 }} />
          <Typography
            variant="h6"
            noWrap
            component="div"
            sx={{
              flexGrow: 1,
              fontWeight: 600,
              fontSize: { xs: "1.1rem", sm: "1.25rem" },
              color: "white",
            }}
          >
            EmpiriQ - Antibiotika Therapie-Empfehlungen
          </Typography>
        </Toolbar>
      </AppBar>

      {/* Navigation Drawer */}
      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
      >
        {/* Mobile drawer */}
        {isMobile ? (
          <Drawer
            variant="temporary"
            open={mobileOpen}
            onClose={handleDrawerToggle}
            ModalProps={{
              keepMounted: true, // Better open performance on mobile
            }}
            sx={{
              "& .MuiDrawer-paper": {
                boxSizing: "border-box",
                width: drawerWidth,
              },
            }}
          >
            {drawer}
          </Drawer>
        ) : (
          <Drawer
            variant="permanent"
            sx={{
              "& .MuiDrawer-paper": {
                boxSizing: "border-box",
                width: drawerWidth,
              },
            }}
            open
          >
            {drawer}
          </Drawer>
        )}
      </Box>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, md: 3 },
          width: { md: `calc(100% - ${drawerWidth}px)` },
          mt: { xs: 7, sm: 8 }, // Account for consistent AppBar height
        }}
      >
        <Container maxWidth="lg" sx={{ px: { xs: 0, md: 2 } }}>
          {children}
        </Container>
      </Box>
    </Box>
  );
}

export default Layout;
