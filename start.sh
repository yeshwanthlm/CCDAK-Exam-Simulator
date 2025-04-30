#!/bin/bash
# macOS startup script for the exam system
# Make this executable with: chmod +x start.sh

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Kill any existing Python processes using the required ports
echo "Checking for existing processes using ports 8000-8020 and 8080-8100..."
for port in $(seq 8000 8020) $(seq 8080 8100); do
  pid=$(lsof -ti:$port)
  if [ ! -z "$pid" ]; then
    echo "Killing process $pid using port $port"
    kill -9 $pid 2>/dev/null
  fi
done

# Ensure source_jsons directory exists
if [ ! -d "$DIR/source_jsons" ]; then
  echo "Creating source_jsons directory..."
  mkdir -p "$DIR/source_jsons"
fi

# Run the Python startup script
python3 start_servers.py