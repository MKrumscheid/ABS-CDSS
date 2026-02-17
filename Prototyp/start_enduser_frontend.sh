#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/frontend"
echo "Starting Enduser Frontend on port 4000..."
echo "Admin Frontend: http://localhost:3000"
echo "Enduser Frontend: http://localhost:4000"
npm run start:enduser
