#!/bin/bash

echo "🔍 FPL H2H Analyzer - Diagnostic Check"
echo "=================================="
echo

# Check if server is running
if ps aux | grep -v grep | grep vite > /dev/null; then
    echo "✅ Vite dev server is running"
    PORT=$(ps aux | grep -v grep | grep vite | grep -o 'localhost:[0-9]*' | head -1 | cut -d: -f2)
    echo "📍 Server port: $PORT"
else
    echo "❌ Vite dev server is NOT running"
    echo "🔧 Starting server..."
    cd "/Users/raphaelyembra/trae/fpl compare/fpl-h2h-analyzer/frontend"
    nohup npm run dev > /tmp/vite.log 2>&1 &
    sleep 3
    echo "⏳ Server starting..."
fi

echo
echo "🌐 Testing accessibility..."

# Test main app
if curl -s http://localhost:5173/ > /dev/null; then
    echo "✅ Main app accessible at http://localhost:5173/"
else
    echo "❌ Main app NOT accessible"
fi

# Test status page
if curl -s http://localhost:5173/status.html > /dev/null; then
    echo "✅ Status page accessible at http://localhost:5173/status.html"
else
    echo "❌ Status page NOT accessible"
fi

echo
echo "🎯 Next Steps:"
echo "1. Open: http://localhost:5173/status.html"
echo "2. Then:  http://localhost:5173/"
echo "3. Hard refresh with Cmd+Shift+R"
echo
echo "📊 Server log (last 5 lines):"
tail -5 /tmp/vite.log 2>/dev/null || echo "No log file found"