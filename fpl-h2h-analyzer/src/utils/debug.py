import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

class DebugLogger:
    def __init__(self, debug_dir: str = "debug_logs"):
        self.debug_dir = Path(debug_dir)
        self.debug_dir.mkdir(exist_ok=True)

    def log_api_response(self, endpoint: str, data: Any, manager_id: Optional[int] = None):
        """Log API responses for debugging"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{endpoint.replace('/', '_')}_{manager_id or 'general'}_{timestamp}.json"

        try:
            with open(self.debug_dir / filename, 'w') as f:
                json.dump({
                    'endpoint': endpoint,
                    'timestamp': timestamp,
                    'data': data
                }, f, indent=2)
        except IOError as e:
            print(f"Error writing debug log to {filename}: {e}")

    def log_error(self, error_type: str, details: Dict[str, Any]):
        """Log errors for debugging"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"error_{error_type}_{timestamp}.json"

        try:
            with open(self.debug_dir / filename, 'w') as f:
                json.dump({
                    'error_type': error_type,
                    'timestamp': timestamp,
                    'details': details
                }, f, indent=2)
        except IOError as e:
            print(f"Error writing error log to {filename}: {e}")