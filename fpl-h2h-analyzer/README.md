# FPL H2H Analyzer

A comprehensive Fantasy Premier League (FPL) Head-to-Head analysis tool that provides real-time insights, predictions, and detailed battle reports for H2H leagues. Now with enhanced historical analysis, league tables, and advanced analytics!

## 🚀 Features

### Core Features
- **Live H2H Battle Tracking**: Real-time score updates during gameweeks with WebSocket integration
- **Historical Battle Viewing**: Browse battles from any gameweek (GW1-GW38) with gameweek selector
- **Comprehensive Battle Analysis**: Detailed breakdowns including differentials, captain choices, and chip usage
- **League Table**: Complete standings with win/draw/loss records and points for/against
- **Advanced Analytics Dashboard**: League-wide performance metrics and insights
- **Report Generation**: Export detailed PDF/CSV/JSON reports of H2H battles and season analysis

### Technical Highlights
- **Real-time Updates**: WebSocket integration for live score updates
- **Intelligent Caching**: Redis-based caching with file backup for optimal performance
- **Responsive Design**: Material-UI based frontend that works on all devices
- **Docker Containerization**: Easy deployment with Docker Compose
- **Async Architecture**: FastAPI backend with async/await for high performance

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.12+ (for local development)
- Node.js 20+ (for frontend development)

## 🚀 Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/fpl-h2h-analyzer.git
cd fpl-h2h-analyzer
```

2. Start the application with Docker Compose:
```bash
docker-compose up -d
```

3. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

The application will automatically fetch the latest FPL data and be ready to use!

## 📁 Project Structure

```
fpl-h2h-analyzer/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── services/         # Business logic & FPL integration
│   │   │   ├── h2h_analyzer.py      # H2H battle analysis
│   │   │   ├── live_data.py         # Live data fetching & caching
│   │   │   ├── report_generator.py  # PDF/CSV report generation
│   │   │   └── cache.py             # Redis caching service
│   │   └── websocket/        # Real-time WebSocket updates
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── LiveBattles.jsx      # Live battles with gameweek selector
│   │   │   ├── LeagueTable.jsx      # League standings table
│   │   │   ├── Analytics.jsx        # Analytics dashboard
│   │   │   └── BattleCard.jsx       # Individual battle display
│   │   ├── pages/            # Page components
│   │   └── services/         # API clients & WebSocket
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── docker-compose.yml        # Docker orchestration
├── reports/                  # Generated reports directory
└── README.md
```

## 🛠️ Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📡 API Endpoints

### Core Endpoints
- `GET /api/health` - Comprehensive health check with service status
- `GET /api/gameweek/current` - Get current gameweek
- `GET /api/league/{league_id}/overview` - Get league overview and standings

### H2H Battle Endpoints
- `GET /api/h2h/live-battles/{league_id}` - Get live H2H battles (supports `?gameweek=` parameter)
- `GET /api/h2h/battle/{manager1_id}/{manager2_id}` - Get detailed battle analysis
- `GET /api/h2h/battle/{manager1_id}/{manager2_id}?gameweek={gw}` - Historical battle analysis

### Report Generation
- `POST /api/report/generate/h2h/{manager1_id}/{manager2_id}` - Generate H2H report
  - Body: `{"league_id": 620117, "format": "pdf|json|csv"}`
- `GET /api/report/download/{file_path}` - Download generated report

### WebSocket
- `WS /ws/connect` - Main WebSocket connection for real-time updates
- Supports subscriptions to:
  - League updates
  - Live gameweek scores
  - H2H battle updates

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Redis Configuration
REDIS_URL=redis://redis:6379

# Database Configuration (PostgreSQL)
DATABASE_URL=postgresql://fpl_user:fpl_password@postgres:5432/fpl_h2h_db

# API Configuration
FPL_API_BASE_URL=https://fantasy.premierleague.com/api/
CACHE_TTL=300  # Cache time-to-live in seconds

# Application Settings
MAX_WEBSOCKET_CONNECTIONS=1000
DEBUG=false
```

### Docker Compose Services

The application uses the following services:
- **backend**: FastAPI application (port 8000)
- **frontend**: React application with Nginx (port 3000)
- **redis**: Caching and real-time updates
- **postgres**: Database for persistent storage

## 🎯 Usage Guide

### Navigation
The app uses **tab-based navigation** within a single page. All features are accessible through tabs at the top of the dashboard:

### Viewing Live Battles
1. Click the **"All Battles"** tab (second tab)
2. Select the desired gameweek from the dropdown (defaults to current GW)
3. View all H2H matches for your league
4. Each battle card shows:
   - Current scores
   - Manager names
   - Chip usage
   - Live/Completed status
5. Click on any battle card to expand analytics (if available)

### League Table
1. Click the **"League Table"** tab (third tab)
2. View complete H2H standings:
   - Current position and total points
   - Win/Draw/Loss records
   - Points for and against
   - Visual indicators for top 3 positions

### Analytics Dashboard
1. Click the **"Analytics"** tab (fourth tab)
2. View league-wide performance metrics:
   - Top scorers and performers
   - Win rate analysis
   - Form tracking
3. Generate H2H reports:
   - Click "Generate H2H Report" button
   - Select two managers from dropdowns
   - Click "Generate Report" to create PDF

### Manager Comparison
1. Click the **"Manager Comparison"** tab (first tab)
2. Select exactly 2 managers from the table
3. Click "Compare Selected" button
4. View detailed analysis:
   - Head-to-head record
   - Squad comparison
   - Differential players
   - Performance trends

## 🐛 Troubleshooting

### Common Issues

1. **"No battles found" error**
   - Ensure you're connected to the internet
   - Check if the FPL API is accessible
   - Try selecting a different gameweek

2. **WebSocket connection errors**
   - Refresh the page
   - Check if the backend is running: `docker-compose ps`
   - View logs: `docker-compose logs backend`

3. **Report generation fails**
   - Ensure the reports directory exists
   - Check backend logs for detailed errors
   - Verify manager IDs are correct

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use ESLint configuration for JavaScript
- Write tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Fantasy Premier League for providing the API
- The FPL community for inspiration and feedback
- All contributors who have helped improve this tool

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact the maintainers
- Join our Discord community (coming soon)

## 📊 Current Implementation Status

### ✅ Working Features
- **Live H2H Battles**: Real-time score tracking with WebSocket updates
- **Historical Analysis**: View battles from any gameweek (GW1-38)
- **League Table**: Complete H2H standings with statistics  
- **Analytics Dashboard**: Performance insights and report generation
- **Report Generation**: Export H2H analysis as PDF/CSV/JSON
- **Comprehensive Analytics**: Differential analysis, predictions, patterns
- **Caching System**: Redis + file-based caching for performance

### 🚧 Known Limitations
- **Single League**: Currently hardcoded to league ID 620117
- **No Authentication**: Public leagues only
- **No Rate Limiting**: May hit FPL API limits with heavy usage
- **Limited API Coverage**: Using 8 of 20+ available FPL endpoints

See [TECHNICAL_DEBT.md](./TECHNICAL_DEBT.md) for detailed implementation status and roadmap.

## 🎉 Recent Updates

### v3.0.1 (May 27, 2025) - Fixes & Documentation
- **FIXED**: Visualization API endpoint error
- **FIXED**: Clarified navigation - all features use tabs, not routes
- **ADDED**: Comprehensive technical debt documentation
- **ADDED**: Clear usage instructions for each feature
- **VERIFIED**: All core features working as expected

### v3.0 (May 27, 2025)
- **NEW**: League Table tab with complete standings and statistics
- **NEW**: Analytics dashboard with performance metrics and insights
- **NEW**: Gameweek selector for viewing historical battles
- **NEW**: PDF/CSV/JSON report generation for H2H analysis
- **FIXED**: WebSocket connection issues in Docker environment
- **FIXED**: League overview 500 errors
- **FIXED**: "No battles found" issue for completed gameweeks
- **FIXED**: H2H match pagination for leagues with many gameweeks
- **IMPROVED**: Better handling of end-of-season data
- **IMPROVED**: Enhanced error messages and fallback data

---
Made with ❤️ for the FPL community