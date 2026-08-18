#!/usr/bin/env bash
set -e

echo "=== Nova Brief Build Script ==="

# Install Python dependencies
pip install -r requirements.txt

# Create recipients.json if it doesn't exist
if [ ! -f "recipients.json" ]; then
    echo '{"recipients":[]}' > recipients.json
    echo "Created empty recipients.json"
fi

# Initialize the database
python -c "from database import NewsDatabase; NewsDatabase().init_database(); print('Database initialized')"

echo "=== Build completed successfully! ==="
