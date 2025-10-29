#!/bin/bash

echo "🚀 Starting VT Calendar Application..."
echo ""
echo "📦 Installing dependencies..."
npm install

echo ""
echo "✨ Creating .env file from template..."
if [ ! -f .env ]; then
    cp env.template .env
    echo "✅ Created .env file. Please update with your API credentials."
else
    echo "⚠️  .env file already exists."
fi

echo ""
echo "🌐 Starting server on http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm start


