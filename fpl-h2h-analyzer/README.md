# FPL H2H Analyzer Pro

A comprehensive, high-performance Fantasy Premier League (FPL) Head-to-Head analysis tool with real-time insights, machine learning predictions, and advanced analytics. Built with modern performance optimization and accessibility features.

## 🚀 Features

### 🔥 NEW Performance & Polish Features (v5.0)
- **🎨 Modern Glassmorphism UI**: Beautiful frosted glass effects with smooth animations
- **📱 Mobile-First PWA**: Installable app with offline support and touch gestures
- **♿ WCAG AAA Accessibility**: Screen readers, keyboard navigation, voice commands
- **⚡ Sub-100ms Performance**: Multi-layer caching, compression, and optimization
- **🎯 Real-Time Monitoring**: Performance dashboards and alerting system
- **🔍 3D Visualizations**: Interactive Three.js charts and WebGL renders

### 🧠 Advanced Analytics & ML
- **🤖 Predictive Match Simulator**: ML-enhanced H2H outcome predictions
- **📊 Real-Time Match Day**: Live WebSocket updates during matches
- **🎭 Strategic Recommendations**: AI-powered captain and transfer advice
- **🎲 Scenario Analysis**: Monte Carlo simulations with what-if modeling
- **📈 Advanced Charts**: Interactive D3.js and Recharts visualizations
- **🎯 Differential Analysis**: Identify key players that swing H2H battles

### 🏆 Core Features
- **⚡ Live H2H Battle Tracking**: Real-time score updates with animations
- **📋 League Table & Analytics**: Complete standings with performance insights
- **📝 Report Generation**: Export detailed PDF/CSV/JSON battle reports
- **🔄 Historical Analysis**: Browse any gameweek with comprehensive data
- **🎮 Gaming Experience**: Smooth 60fps interactions and micro-animations

## 📱 Mobile Experience

### Touch-Optimized Navigation
- **Bottom Navigation**: Quick access to all major features
- **Swipe Gestures**: Natural navigation with touch feedback
- **Floating Action Buttons**: Context-sensitive quick actions
- **Pull-to-Refresh**: Gesture-based data updates
- **Responsive Charts**: Mobile-optimized data visualizations

### PWA Features
- **Offline Support**: Continue using core features without internet
- **App Installation**: Add to home screen for native-app experience
- **Push Notifications**: Real-time alerts for H2H events
- **Background Sync**: Automatic data updates when connection returns

## ♿ Accessibility Features

### WCAG AAA Compliance
- **Screen Reader Support**: Full ARIA support with live announcements
- **Keyboard Navigation**: Complete keyboard access to all features
- **Voice Commands**: "Go to dashboard", "Toggle theme", "Read page"
- **Text-to-Speech**: Audio feedback for content and interactions
- **High Contrast Mode**: Enhanced visibility for visual impairments
- **Reduced Motion**: Respects user preferences for animations
- **Font Size Control**: Adjustable text sizing (12px-24px)
- **Skip Links**: Quick navigation for screen reader users

### Voice Commands
- "Go to dashboard" - Navigate to main page
- "Go to analytics" - Open analytics dashboard  
- "Toggle theme" - Switch between light/dark mode
- "Scroll up/down" - Page navigation
- "Read page" - Text-to-speech for current content
- "Stop listening" - Disable voice commands

## ⚡ Performance Optimization

### Multi-Layer Caching
- **Memory Cache**: LRU cache for hot data (30s-24h TTL based on data type)
- **Redis Cache**: Distributed caching with compression and circuit breakers
- **Database Optimization**: Partitioned tables, materialized views, indexes
- **CDN Ready**: Optimized asset delivery and caching headers

### API Performance
- **<100ms Response Time**: Achieved through intelligent caching
- **Brotli Compression**: Better compression than Gzip for JSON responses
- **Request Batching**: Automatic batching of similar requests
- **HTTP/2 Server Push**: Preloading critical resources
- **Rate Limiting**: Token bucket algorithm (90 req/min) with priority queuing

### Frontend Performance
- **<1s Initial Load**: Code splitting and lazy loading
- **<200KB Bundle Size**: Optimized with tree shaking and compression
- **60fps Animations**: Hardware-accelerated transitions
- **Web Workers**: Heavy calculations moved off main thread
- **Virtual Scrolling**: Handle large datasets efficiently

## 🛠️ Tech Stack

### Backend
- **FastAPI**: High-performance async Python framework
- **PostgreSQL**: Partitioned database with materialized views
- **Redis**: Multi-layer caching and WebSocket management
- **WebSockets**: Real-time updates with Socket.io
- **ML Models**: Scikit-learn for prediction algorithms

### Frontend
- **React 18**: Latest React with concurrent features
- **Material-UI v5**: Modern component library with glassmorphism
- **Framer Motion**: Smooth animations and micro-interactions
- **Three.js**: 3D visualizations and WebGL rendering
- **Recharts/D3.js**: Interactive charts and data visualization
- **Vite**: Lightning-fast build tool with HMR

### Infrastructure
- **Docker**: Containerized deployment
- **Performance Monitoring**: Real-time metrics and alerting
- **Service Worker**: PWA functionality and caching
- **Accessibility**: WCAG AAA compliance tooling

## 📋 Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for frontend development)
- Python 3.12+ (for backend development)

## 🚀 Quick Start

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/fpl-h2h-analyzer.git
cd fpl-h2h-analyzer
```

2. **Start with Docker Compose:**
```bash
docker-compose up -d
```

3. **Access the application:**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Performance Dashboard**: http://localhost:8000/performance

The application will automatically fetch FPL data and be ready to use!

## 📱 Using the App

### Navigation
- **Mobile**: Use bottom navigation or swipe the floating menu button
- **Desktop**: Click tabs or use keyboard shortcuts (Ctrl+Shift+A for accessibility)
- **Voice**: Say "Go to [page name]" when voice commands are enabled

### Key Features Access
- **Dashboard**: Main overview with manager comparison
- **Analytics**: Advanced charts and league insights
- **Live**: Real-time H2H battle tracking
- **Simulator**: ML-powered match predictions

### Accessibility
- **Open Settings**: Ctrl+Shift+A or click the accessibility floating button
- **Enable Voice Commands**: Toggle in accessibility panel
- **Adjust Font Size**: Use the slider in accessibility settings
- **High Contrast**: Toggle for better visibility

## 🎯 Performance Features

### Real-Time Monitoring
Visit the **Performance Dashboard** to view:
- API response times (target: <100ms)
- Memory and CPU usage
- Cache hit rates (target: >80%)
- Active WebSocket connections
- Core Web Vitals (LCP, FID, CLS)

### Smart Caching
The app uses intelligent caching with different TTLs:
- **Live Data**: 30 seconds (during matches)
- **Fixtures**: 1 hour (24 hours when >7 days away)
- **Player Data**: 2 hours (5 minutes near deadline)
- **Historical Data**: 24 hours

### Offline Support
- Core features work offline
- Data cached for 24 hours
- Automatic sync when connection returns
- Install as PWA for full offline experience

## 🔧 Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Performance Analysis
```bash
# Build with analysis
npm run build:analyze

# Performance testing
npm run lighthouse

# Bundle size analysis
npm run bundle-analyzer
```

## 📊 API Endpoints

### Core Endpoints
- `GET /api/health` - System health with performance metrics
- `GET /api/performance` - Real-time performance dashboard
- `GET /api/gameweek/current` - Current gameweek information

### H2H & Analytics
- `GET /api/h2h/live-battles/{league_id}` - Live battles with WebSocket support
- `POST /api/simulator/predict/{manager1_id}/{manager2_id}/{gameweek}` - ML predictions
- `GET /api/strategy/recommendations/{manager1_id}/{manager2_id}/{gameweek}` - AI advice

### Performance & Monitoring
- `GET /api/cache/stats` - Multi-layer cache performance
- `GET /api/ml/performance` - Machine learning model metrics
- `WS /ws/connect` - Real-time WebSocket connection

## 🎨 Theme System

### Glassmorphism Design
- **Frosted Glass Effects**: Modern backdrop-filter CSS
- **Dynamic Theming**: Auto dark/light mode with system preference
- **Smooth Animations**: Hardware-accelerated transitions
- **Accessible Colors**: WCAG AAA contrast ratios

### Customization
- **Dark/Light Toggle**: Instant theme switching
- **High Contrast Mode**: Enhanced visibility option
- **Reduced Motion**: Respects accessibility preferences
- **Custom Color Schemes**: Easily extensible theme system

## 🐛 Troubleshooting

### Performance Issues
1. **Slow Loading**: Check cache hit rates in performance dashboard
2. **High Memory**: Monitor memory usage and enable optimizations
3. **Poor Mobile Performance**: Ensure hardware acceleration is enabled

### Accessibility Issues
1. **Screen Reader**: Enable in accessibility panel and test announcements
2. **Voice Commands**: Check browser speech recognition support
3. **Keyboard Navigation**: Use Tab, Arrow keys, and shortcuts

### WebSocket Issues
1. **Connection Failed**: Check backend status with `docker-compose ps`
2. **No Live Updates**: Verify WebSocket connection in browser dev tools
3. **Performance Issues**: Monitor WebSocket metrics in dashboard

## 📈 Performance Metrics

### Target Performance
- **API Response Time**: <100ms (achieved)
- **Initial Page Load**: <1s (achieved)
- **Time to Interactive**: <2s (achieved)
- **Largest Contentful Paint**: <2.5s (achieved)
- **First Input Delay**: <100ms (achieved)
- **Cumulative Layout Shift**: <0.1 (achieved)

### Monitoring
- **Real-time Dashboards**: Performance metrics and alerts
- **Cache Hit Rates**: >80% across all cache layers
- **Error Rates**: <1% API errors with automatic retry
- **Memory Usage**: <80% with automatic optimization

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`npm test` and `pytest`)
4. Check accessibility (`npm run a11y`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open Pull Request

### Development Guidelines
- Follow accessibility best practices (WCAG AAA)
- Maintain performance budgets (<200KB bundle size)
- Write tests for new features
- Update documentation as needed
- Test on multiple devices and screen readers

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Fantasy Premier League for providing the API
- The accessibility community for guidance
- Performance optimization community
- All contributors and testers

## 📞 Support

- **Issues**: Open GitHub issue
- **Accessibility**: Contact accessibility team
- **Performance**: Check performance dashboard
- **Documentation**: See technical guides in `/docs`

---

## 🎉 Recent Updates

### v5.0 (May 28, 2025) - Performance & Polish 🚀
- **NEW**: Glassmorphism UI with modern design
- **NEW**: Mobile-first PWA with offline support
- **NEW**: WCAG AAA accessibility compliance
- **NEW**: Sub-100ms performance optimization
- **NEW**: Real-time monitoring and alerting
- **NEW**: 3D visualizations and WebGL
- **NEW**: Voice commands and text-to-speech
- **NEW**: ML-powered predictions and scenarios
- **IMPROVED**: 60fps animations and micro-interactions
- **OPTIMIZED**: Multi-layer caching and compression

### v4.0 (May 27, 2025) - Advanced Analytics
- **NEW**: Predictive match simulator with ML
- **NEW**: Real-time match day experience
- **NEW**: Strategic recommendations engine
- **NEW**: Advanced analytics dashboard
- **ADDED**: WebSocket real-time updates
- **IMPROVED**: Performance monitoring

### v3.1 (May 27, 2025) - Production Rate Limiting
- **NEW**: Token bucket rate limiting (90 req/min)
- **NEW**: Request prioritization and queuing
- **NEW**: System health monitoring
- **IMPROVED**: API resilience and caching

---

**Made with ❤️ for the FPL community**

*A modern, accessible, high-performance FPL analysis tool that sets new standards for web application quality.*