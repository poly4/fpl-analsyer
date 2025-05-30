# Performance Check Command

Run performance analysis on: $ARGUMENTS

## Steps:

1. **Measure Initial Render Time**
   ```bash
   cd frontend
   npm run dev &
   DEV_PID=$!
   sleep 5
   curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5173
   kill $DEV_PID
   ```

2. **Check Re-render Frequency**
   - Open Chrome DevTools
   - Go to Performance tab
   - Record while interacting with $ARGUMENTS
   - Check for unnecessary re-renders
   - Look for components rendering > 16ms

3. **Analyze Bundle Impact**
   ```bash
   cd frontend
   npm run build
   npm run analyze
   # Check size of chunks containing $ARGUMENTS
   ```

4. **Test Animation Performance**
   - Open Chrome DevTools
   - Go to Rendering tab
   - Enable FPS meter
   - Interact with $ARGUMENTS animations
   - Ensure consistent 60fps

5. **Memory Usage Profiling**
   - Open Chrome DevTools
   - Go to Memory tab
   - Take heap snapshot before using $ARGUMENTS
   - Use the feature extensively
   - Take another snapshot
   - Compare for memory leaks

6. **Generate Optimization Report**
   ```bash
   echo "Performance Report for: $ARGUMENTS"
   echo "================================"
   echo ""
   echo "Initial Render: [TIME]ms"
   echo "Re-renders: [COUNT] unnecessary"
   echo "Bundle Impact: [SIZE]KB"
   echo "Animation FPS: [FPS] average"
   echo "Memory Leak: [YES/NO]"
   echo ""
   echo "Recommendations:"
   echo "- [Specific optimization suggestions]"
   ```

## Automated Script

```bash
#!/bin/bash
COMPONENT=$1

echo "🔍 Analyzing performance for: $COMPONENT"

# Build and analyze
cd frontend
npm run build -- --mode production > build.log 2>&1

# Extract metrics
BUNDLE_SIZE=$(du -sk dist | cut -f1)
BUILD_TIME=$(grep "built in" build.log | sed 's/.*built in //')

# Run Lighthouse
npx lighthouse http://localhost:5173 --output=json --output-path=./lighthouse-report.json

# Extract scores
LCP=$(jq '.audits["largest-contentful-paint"].numericValue' lighthouse-report.json)
FID=$(jq '.audits["max-potential-fid"].numericValue' lighthouse-report.json)
CLS=$(jq '.audits["cumulative-layout-shift"].numericValue' lighthouse-report.json)

echo "📊 Results:"
echo "  Bundle Size: ${BUNDLE_SIZE}KB"
echo "  Build Time: $BUILD_TIME"
echo "  LCP: ${LCP}ms"
echo "  FID: ${FID}ms"
echo "  CLS: $CLS"

# Cleanup
rm lighthouse-report.json build.log
```

## Quick Checks

For rapid performance validation:

```bash
# Check render performance
window.__performanceUtils.renderTracker.getReport()

# Check API performance
window.__performanceUtils.apiMonitor

# Check FPS
window.__performanceUtils.fpsMonitor.getFPS()

# Get recommendations
window.__performanceUtils.getRecommendations()
```