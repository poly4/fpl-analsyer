# Configuration for FPL H2H Analyzer

# FPL API Base URL
FPL_API_BASE_URL = "https://fantasy.premierleague.com/api/"

# League ID for "Top Dog Premier League" (Example - replace with actual ID if known)
# If you don't know the ID, the application might need to search by name,
# which can be less reliable.
TARGET_LEAGUE_ID = 620117 # e.g., 12345
TARGET_LEAGUE_NAME = "Top Dog Premier League"

# Cache settings
CACHE_DIR = ".api_cache"
CACHE_EXPIRY_SECONDS = 3600  # 1 hour

# Report settings
REPORTS_DIR = "reports"
DEFAULT_REPORT_FORMATS = ["json", "md"]

# Other configurations can be added here
# e.g., specific manager IDs for quick testing, etc.