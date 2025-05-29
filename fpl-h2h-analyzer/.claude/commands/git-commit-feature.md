# Git Commit Feature Command

**Purpose:** Create structured, professional git commits for feature implementation following conventional commit standards optimized for the FPL H2H Analyzer project.

## Usage
```bash
> /git-commit-feature FeatureName
```

## Template Prompt

```
create a comprehensive git commit for the {FeatureName} implementation following our project standards:

## 1. Pre-Commit Validation

### Code Quality Check
```bash
# Run linting and tests
/test-and-lint

# Ensure no console.log statements in production code
grep -r "console.log" frontend/src --exclude-dir=node_modules || echo "✅ No console.log found"

# Check for TODO comments that should be addressed
grep -r "TODO\|FIXME" frontend/src backend/app --exclude-dir=node_modules || echo "✅ No unresolved TODOs"

# Validate TypeScript compilation
cd frontend && npx tsc --noEmit
```

### File Organization Check
```bash
# Ensure new files follow project structure
find frontend/src -name "*.jsx" -o -name "*.tsx" | head -10
find backend/app -name "*.py" | head -10

# Check for unused imports
cd frontend && npx eslint src/ --ext .js,.jsx,.ts,.tsx --quiet --rule "no-unused-vars: error"
```

## 2. Git Status Review

```bash
# Review all changes
git status

# Show detailed diff
git diff --stat

# Review specific file changes
git diff HEAD~1..HEAD --name-only
```

## 3. Commit Message Structure

Use conventional commit format optimized for FPL H2H Analyzer:

```
<type>(<scope>): <description>

<body>

<footer>
```

### Type Options:
- `feat`: New feature (glassmorphism, animations, analytics)
- `fix`: Bug fix (WebSocket reconnection, data loading)
- `perf`: Performance improvement (bundle size, animation fps)
- `refactor`: Code refactoring (component splitting, architecture)
- `style`: Visual/styling changes (CSS, theme updates)
- `ui`: User interface improvements (layout, responsiveness)
- `analytics`: Analytics features (predictions, charts, ML)
- `websocket`: Real-time features (live updates, notifications)
- `api`: Backend API changes (endpoints, services)
- `cache`: Caching improvements (Redis, local storage)
- `test`: Testing additions/improvements
- `docs`: Documentation updates
- `chore`: Build process, dependencies, tooling

### Scope Options:
- `dashboard`: Main dashboard components
- `h2h`: Head-to-head battle features  
- `analytics`: Analytics and prediction features
- `live`: Real-time/live data features
- `ui`: User interface components
- `api`: Backend API layers
- `websocket`: WebSocket functionality
- `performance`: Performance optimizations
- `mobile`: Mobile-specific features
- `charts`: Data visualization
- `cache`: Caching layer
- `ml`: Machine learning features

## 4. Commit Examples

### Feature Implementation
```bash
git commit -m "feat(ui): implement glassmorphism design system for modern 2025 aesthetics

- Add comprehensive glassmorphism color palette with rgba values
- Create GlassCard base component with backdrop-filter effects
- Implement glass navigation tabs with smooth transitions
- Add hover animations with transform and glow effects
- Update ThemeProvider with modern gradient definitions
- Ensure browser fallbacks for backdrop-filter support

Performance impact:
- Bundle size: +12KB (glass effect utilities)
- Animation performance: 60fps maintained
- Browser compatibility: 95% (fallbacks for older browsers)

Breaking changes: None - backward compatible with existing components

Closes #123
Addresses MODERNIZATION_ANALYSIS requirements for visual transformation"
```

### Analytics Feature
```bash
git commit -m "feat(analytics): add AI-powered prediction insights with confidence visualization

- Implement AIInsightsPanel component with typewriter animation
- Add ConfidenceBar with animated progress indicators  
- Create PredictionCards with ML recommendation display
- Integrate real-time prediction updates via WebSocket
- Add scenario analysis with visual comparison charts
- Implement predictive scoring with confidence intervals

Analytics enhancements:
- ML prediction accuracy: 87% (baseline: 82%)
- Real-time prediction updates: <100ms latency
- Confidence visualization: Dynamic progress bars
- Scenario modeling: 5 different prediction scenarios

API endpoints added:
- GET /api/analytics/v2/h2h/comprehensive/{m1}/{m2}
- GET /api/analytics/prediction-scenarios/{m1}/{m2}
- WebSocket: /ws/analytics/live-tracking/{m1}/{m2}

Resolves #456
Part of Phase 3: Advanced Features implementation"
```

### Performance Optimization
```bash
git commit -m "perf(frontend): optimize bundle size and implement advanced code splitting

- Implement dynamic imports for analytics components (-340KB)
- Add React.lazy for Three.js 3D visualizations (-280KB)  
- Optimize Framer Motion tree shaking (-120KB)
- Implement service worker caching for API responses
- Add image lazy loading with intersection observer
- Optimize WebSocket message batching for performance

Performance improvements:
- Initial bundle size: 2.8MB → 2.1MB (-25%)
- Time to interactive: 2.5s → 1.8s (-28%)
- Lighthouse performance: 85 → 94 (+9 points)
- Animation frame rate: 60fps maintained
- Memory usage: -15% during navigation

Bundle analysis:
- Core app: 800KB (was 1.2MB)
- Analytics modules: Lazy loaded on demand
- Three.js: Loaded only when 3D features accessed
- Charts: Split by visualization type

No breaking changes - all features remain functional

Fixes #789
Addresses performance targets from MODERNIZATION_ANALYSIS"
```

### WebSocket Enhancement
```bash
git commit -m "feat(websocket): enhance real-time features with room-based subscriptions

- Implement advanced room management for H2H battles
- Add automatic reconnection with exponential backoff
- Create WebSocket health monitoring with visual indicators
- Add message batching for high-frequency updates
- Implement rate limiting with graceful degradation
- Create connection state persistence across page reloads

Real-time improvements:
- Connection stability: 99.8% uptime
- Reconnection time: <2 seconds average
- Message latency: <50ms (was 150ms)
- Concurrent connections: 1000+ supported
- Rate limiting: 100 messages/minute per client

New WebSocket features:
- Room-based subscriptions (league, H2H, manager-specific)
- Heartbeat monitoring with ping/pong
- Connection state visualization in header
- Automatic subscription restoration on reconnect
- Graceful fallback to polling when WebSocket unavailable

WebSocket endpoints:
- /ws/connect (main connection with reconnection)
- /ws/h2h-battle/{m1}/{m2} (battle-specific updates)
- /ws/league/{league_id} (league-wide updates)
- /ws/manager/{manager_id} (manager-specific updates)

Backward compatible with existing WebSocket connections

Implements #321
Completes real-time infrastructure modernization"
```

## 5. Pre-Commit Hooks Setup

```bash
# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

echo "🔍 Running pre-commit checks..."

# Run linting
echo "📝 Linting code..."
cd frontend && npm run lint
if [ $? -ne 0 ]; then
  echo "❌ Linting failed. Please fix errors before committing."
  exit 1
fi

# Run tests
echo "🧪 Running tests..."
npm run test:quick
if [ $? -ne 0 ]; then
  echo "❌ Tests failed. Please fix tests before committing."
  exit 1
fi

# Check bundle size
echo "📦 Checking bundle size..."
npm run build > /dev/null 2>&1
BUNDLE_SIZE=$(du -sh frontend/dist | cut -f1)
echo "📊 Bundle size: $BUNDLE_SIZE"

echo "✅ Pre-commit checks passed!"
EOF

chmod +x .git/hooks/pre-commit
```

## 6. Commit Workflow

### Standard Feature Commit
```bash
# 1. Stage relevant files
git add frontend/src/components/modern/
git add frontend/src/styles/themes.js
git add MODERNIZATION_ANALYSIS.md

# 2. Review changes
git diff --cached

# 3. Create structured commit
git commit -m "feat(ui): implement glassmorphism design system

- Add comprehensive color palette with rgba values
- Create GlassCard base component with backdrop effects
- Update ThemeProvider with modern gradients
- Ensure browser compatibility with fallbacks

Bundle impact: +12KB
Performance: 60fps maintained
Browser support: 95%

Implements MODERNIZATION_ANALYSIS Phase 1
Closes #123"

# 4. Push to feature branch
git push origin feature/glassmorphism-design-system
```

### Emergency Hotfix Commit
```bash
git commit -m "fix(websocket): resolve connection timeout causing data loss

- Increase WebSocket ping interval to 30s (was 10s)
- Add connection retry with exponential backoff
- Implement message queue for failed sends
- Add connection state persistence

Critical fix for production WebSocket stability
Resolves 504 timeout errors affecting 15% of users

Hotfix for #urgent-999"
```

## 7. Branch and PR Integration

### Feature Branch Naming
```bash
# Branch naming convention
feature/glassmorphism-design-system
feature/ai-prediction-insights  
feature/websocket-room-management
fix/bundle-size-optimization
perf/animation-performance
ui/mobile-responsive-design
```

### PR Title Generation
After committing, create PR with generated title:
```
[FEAT] Implement glassmorphism design system for 2025 modern aesthetics

Transforms the visual foundation of the application with:
- Comprehensive glass effect system
- Modern color palette and gradients  
- Smooth animations and micro-interactions
- Enhanced accessibility and performance

Part of MODERNIZATION_ANALYSIS Phase 1 implementation.
```

## 8. Automated Commit Validation

```bash
# Validate commit message format
npx commitlint --edit $1

# Check for sensitive information
git diff --cached | grep -i "password\|secret\|key\|token" && echo "⚠️  Potential sensitive data detected"

# Validate file size limits
git diff --cached --name-only | xargs ls -la | awk '$5 > 100000 {print "⚠️  Large file: " $9 " (" $5 " bytes)"}'
```

Remember to follow the conventional commit format and include relevant context about performance impact, breaking changes, and issue references.
```

## Integration with Development Workflow

This command should be used:
- After completing feature development
- Before creating pull requests  
- For hotfixes and urgent patches
- When implementing modernization phases
- For all significant code changes

## Commit Message Quality Standards

- **Clear and descriptive** - explains what and why
- **Includes impact metrics** - bundle size, performance, etc.
- **References issues/tickets** - maintains traceability  
- **Breaking changes noted** - helps with versioning
- **Scope clearly defined** - helps with code review