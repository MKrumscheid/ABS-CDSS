#!/bin/bash
echo "===================================================="
echo "Starting ABS-CDSS - All Services"
echo "===================================================="
echo ""
echo "This will start:"
echo "- Backend API Server (Port 8000)"
echo "- Admin Frontend (Port 3000)" 
echo "- Enduser Frontend (Port 4000)"
echo ""
echo "Press Ctrl+C to stop all services."
echo ""
echo "===================================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Start Backend in background
echo "Starting Backend API Server..."
cd "$SCRIPT_DIR"
gnome-terminal --title="ABS-CDSS Backend (Port 8000)" -- bash -c "./start_backend_venv.sh; exec bash" 2>/dev/null || \
xterm -T "ABS-CDSS Backend (Port 8000)" -e "./start_backend_venv.sh" 2>/dev/null || \
konsole --title "ABS-CDSS Backend (Port 8000)" -e "./start_backend_venv.sh" 2>/dev/null || \
(./start_backend_venv.sh &)

# Wait a moment for backend to initialize
sleep 3

# Start Admin Frontend in new terminal
echo "Starting Admin Frontend..."
gnome-terminal --title="ABS-CDSS Admin Frontend (Port 3000)" -- bash -c "./start_frontend.sh; exec bash" 2>/dev/null || \
xterm -T "ABS-CDSS Admin Frontend (Port 3000)" -e "./start_frontend.sh" 2>/dev/null || \
konsole --title "ABS-CDSS Admin Frontend (Port 3000)" -e "./start_frontend.sh" 2>/dev/null || \
(./start_frontend.sh &)

# Wait a moment
sleep 2

# Start Enduser Frontend in new terminal
echo "Starting Enduser Frontend..."
gnome-terminal --title="ABS-CDSS Enduser Frontend (Port 4000)" -- bash -c "./start_enduser_frontend.sh; exec bash" 2>/dev/null || \
xterm -T "ABS-CDSS Enduser Frontend (Port 4000)" -e "./start_enduser_frontend.sh" 2>/dev/null || \
konsole --title "ABS-CDSS Enduser Frontend (Port 4000)" -e "./start_enduser_frontend.sh" 2>/dev/null || \
(./start_enduser_frontend.sh &)

echo ""
echo "===================================================="
echo "All services are starting..."
echo ""
echo "Backend API:        http://localhost:8000"
echo "Admin Frontend:     http://localhost:3000"
echo "Enduser Frontend:   http://localhost:4000"
echo "API Documentation:  http://localhost:8000/docs"
echo ""
echo "===================================================="
echo ""
echo "All services are now running."
echo "Check the separate terminal windows for each service."
echo "To stop all services, press Ctrl+C here and close the terminal windows."
echo ""

# Keep script running
wait
