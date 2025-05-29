# Test and Lint Command

**Purpose:** Run comprehensive testing and linting for the FPL H2H Analyzer application after making changes.

## Usage
```bash
> /test-and-lint
```

## Template Prompt

```
run comprehensive testing and linting workflow for the FPL H2H Analyzer application:

## 1. Frontend Testing & Linting

### Install Dependencies (if needed)
```bash
cd frontend
npm install
```

### Linting & Code Quality
```bash
# Run ESLint for JavaScript/TypeScript
npx eslint src/ --ext .js,.jsx,.ts,.tsx --fix

# Check for unused dependencies
npx depcheck

# Check for security vulnerabilities
npm audit --audit-level moderate

# TypeScript type checking
npx tsc --noEmit
```

### Performance Testing
```bash
# Build application and check bundle size
npm run build

# Analyze bundle size
npx vite-bundle-analyzer dist/stats.html

# Check for performance regressions
npm run lighthouse
```

### Component Testing
```bash
# Run React component tests
npm test -- --coverage --watchAll=false

# Test component accessibility
npm run test:a11y
```

## 2. Backend Testing & Linting

### Python Code Quality
```bash
cd backend

# Install testing dependencies
pip install pytest pytest-asyncio pytest-cov black flake8 mypy

# Format code with Black
black app/ --line-length 88

# Lint with flake8
flake8 app/ --max-line-length=88 --ignore=E203,W503

# Type checking with mypy
mypy app/ --ignore-missing-imports

# Security scanning
bandit -r app/
```

### API Testing
```bash
# Run FastAPI tests
pytest tests/ -v --cov=app --cov-report=html

# Test API endpoints
pytest tests/test_fpl_endpoints.py -v

# Test WebSocket functionality
pytest tests/test_websocket_manager.py -v

# Test cache service
pytest tests/test_cache_service.py -v
```

## 3. Integration Testing

### API Integration
```bash
# Start backend services
docker-compose up -d redis postgres

# Test API health endpoints
curl -f http://localhost:8000/api/health

# Test rate limiter
curl -f http://localhost:8000/api/test/rate-limiter

# Test analytics endpoints
curl -f http://localhost:8000/api/test/analytics
```

### Frontend-Backend Integration
```bash
# Start full development environment
docker-compose up -d

# Test WebSocket connections
npm run test:websocket

# Test API integration
npm run test:integration

# Test real-time features
npm run test:realtime
```

## 4. Performance Validation

### Frontend Performance
```bash
# Lighthouse audit
npm run lighthouse -- --only-categories=performance,accessibility,best-practices

# Bundle size analysis
npm run analyze

# Check for memory leaks
npm run test:memory

# Validate 60fps animations
npm run test:animations
```

### Backend Performance
```bash
# Load testing with locust
locust -f tests/load_test.py --host=http://localhost:8000

# Database query performance
pytest tests/test_database_performance.py

# Redis cache performance
pytest tests/test_cache_performance.py

# WebSocket connection limits
pytest tests/test_websocket_load.py
```

## 5. Security Validation

### Frontend Security
```bash
# Check for known vulnerabilities
npm audit --audit-level high

# Scan for security issues
npm run security-scan

# Validate CSP headers
npm run test:csp
```

### Backend Security
```bash
# Security scanning
bandit -r app/ -f json -o security-report.json

# Check for SQL injection vulnerabilities
sqlmap --batch --crawl=2 --url="http://localhost:8000"

# Validate rate limiting
pytest tests/test_rate_limiting.py -v
```

## 6. Accessibility Testing

### Frontend A11y
```bash
# Run axe-core accessibility tests
npm run test:a11y

# Test keyboard navigation
npm run test:keyboard

# Test screen reader compatibility
npm run test:screenreader

# Color contrast validation
npm run test:contrast
```

## 7. Error Handling Validation

### Test Error Boundaries
```bash
# Test React error boundaries
npm run test:error-boundaries

# Test API error responses
pytest tests/test_error_handling.py

# Test WebSocket error scenarios
pytest tests/test_websocket_errors.py

# Test network failure scenarios
npm run test:network-errors
```

## 8. Build & Deployment Validation

### Production Build
```bash
# Frontend production build
cd frontend
npm run build
npm run preview

# Backend production setup
cd backend
python -m app.main

# Docker build test
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d --scale app=2
```

### Environment Testing
```bash
# Test development environment
npm run dev

# Test production environment
npm run start

# Test staging environment
npm run staging

# Test environment variables
npm run test:env
```

## 9. Regression Testing

### Visual Regression
```bash
# Take screenshots of all pages
npm run test:visual

# Compare with baseline images
npm run test:visual-diff

# Update baseline if changes are intended
npm run test:visual-update
```

### Functional Regression
```bash
# Run full test suite
npm run test:full

# Test critical user paths
npm run test:e2e

# Test browser compatibility
npm run test:browsers
```

## 10. Performance Monitoring

### Check Performance Metrics
```bash
# Monitor bundle size
bundlesize

# Check lighthouse scores
lighthouse http://localhost:5173 --output=json

# Validate performance budgets
npm run perf-budget

# Check for performance regressions
npm run perf-compare
```

## 11. Final Validation Checklist

### Code Quality
- [ ] All linting errors fixed
- [ ] TypeScript errors resolved
- [ ] No security vulnerabilities (high severity)
- [ ] Code coverage above 80%
- [ ] No console errors in production build

### Performance
- [ ] Bundle size under 2.5MB
- [ ] Lighthouse performance score > 90
- [ ] All animations run at 60fps
- [ ] API response times < 500ms
- [ ] WebSocket connections stable

### Accessibility
- [ ] WCAG AA compliance
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] Color contrast ratios pass
- [ ] All interactive elements have ARIA labels

### Functionality
- [ ] All tests pass
- [ ] No console errors
- [ ] WebSocket connections work
- [ ] Real-time updates function
- [ ] Error handling works gracefully

### Security
- [ ] No high-severity vulnerabilities
- [ ] Rate limiting functional
- [ ] Input validation working
- [ ] CORS configured correctly
- [ ] CSP headers set properly

If any tests fail, fix the issues before proceeding with deployment.
```

## Integration with Git Workflow

This command should be run:
- Before committing changes
- After major feature additions
- Before creating pull requests
- As part of CI/CD pipeline
- Before production deployments

## Automated CI/CD Integration

```yaml
# .github/workflows/test-and-lint.yml
name: Test and Lint
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Run full test suite
        run: /test-and-lint
```