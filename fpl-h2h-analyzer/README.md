# FPL H2H League Analyzer

A Python application to analyze Fantasy Premier League (FPL) Head-to-Head (H2H) leagues, with a focus on detailed manager comparisons and comprehensive report generation.

## Features

-   Fetch data directly from the official FPL API.
-   Detailed analysis of H2H league standings and matches.
-   In-depth comparison of two selected managers, including:
    -   H2H record
    -   Performance metrics (average points, consistency, form)
    -   Transfer analysis
    -   Captain success rates
    -   Differential player identification
    -   Momentum calculation
-   Generate comprehensive reports in multiple formats (JSON, CSV, Markdown).
-   Visualize data using charts (matplotlib/plotly).
-   Interactive Command Line Interface (CLI) for ease of use.

## Project Structure

```
fpl-h2h-analyzer/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   └── fpl_client.py       # Handles FPL API communication
│   ├── models/
│   │   ├── __init__.py
│   │   ├── manager.py          # Dataclasses for manager profiles
│   │   └── h2h_league.py       # Dataclasses for H2H league data
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── manager_analyzer.py # Functions for individual manager analysis
│   │   └── h2h_comparator.py   # Functions for comparing managers
│   ├── reports/
│   │   ├── __init__.py
│   │   └── report_generator.py # Generates reports in various formats
│   └── main.py                 # Main application CLI
├── requirements.txt            # Project dependencies
├── config.py                   # Configuration settings
└── README.md                   # This file
```

## Prerequisites

-   Python 3.8+

## Setup

1.  **Clone the repository (or create the files as per the structure):**
    ```bash
    # git clone <repository_url> # If it were a git repo
    # cd fpl-h2h-analyzer
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration (Optional):**
    Modify `config.py` if you need to set a default league ID or change cache settings.

## Usage

Run the main application from the root directory of the project:

```bash
python src/main.py
```

The application will guide you through the following steps:

1.  **Enter League Name/ID:** Provide the name or ID of the FPL H2H league you want to analyze (e.g., "Top Dog Premier League").
2.  **Select Managers:** The application will (eventually) list managers in the league. You'll be prompted to select two managers for a detailed comparison by entering their FPL IDs.
3.  **Analysis & Report:** The application will perform the analysis and generate a report, saving it to the `reports/` directory.

### Example Interaction:

```
$ python src/main.py
Welcome to the FPL H2H League Analyzer!
Enter the FPL H2H league name or ID you want to analyze (default: Top Dog Premier League): My Awesome League
Analyzing league: My Awesome League

Select two managers to compare:
1. Manager A (ID: 1234567)
2. Manager B (ID: 2345678)
(Note: In a full implementation, manager list would be fetched from the league)
Enter ID of the first manager: 1234567
Enter ID of the second manager: 2345678

Comparing Manager 1234567 vs Manager 2345678
Generating comprehensive analysis... (This will take a moment)

Report saved to: reports/h2h_battle_1234567_vs_2345678.md
```

## Core Components

-   **`FPLAPIClient` (`src/api/fpl_client.py`):**
    -   Fetches manager data (profile, history, picks).
    -   Retrieves H2H league standings and match details.
    -   Implements caching to respect API rate limits.
-   **Data Models (`src/models/`):**
    -   Uses Python `dataclasses` for structured representation of managers, H2H matches, league standings, and gameweek performance.
-   **Analysis Engine (`src/analysis/`):**
    -   `manager_analyzer.py`: Calculates individual performance metrics.
    -   `h2h_comparator.py`: Focuses on direct H2H comparisons.
-   **Report Generator (`src/reports/report_generator.py`):**
    -   Creates detailed reports of H2H battles.
    -   Supports export to JSON, CSV, and Markdown.
    -   Includes capabilities for generating charts (e.g., using `matplotlib` or `plotly`).
-   **Main Application (`src/main.py`):**
    -   Provides an interactive CLI using the `rich` library.
    -   Orchestrates the workflow: data fetching, analysis, and report generation.

## Technical Stack

-   **Python 3.8+**
-   **`requests`**: For making HTTP requests to the FPL API.
-   **`pandas`**: For data manipulation and analysis (especially useful for tabular data and time series).
-   **`matplotlib` / `plotly`**: For creating visualizations and charts.
-   **`rich`**: For creating a user-friendly and visually appealing CLI.

## TODO / Future Enhancements

This is a foundational setup. Future development will involve implementing the core logic within each module:

-   [ ] **`FPLAPIClient`**: Implement all API endpoint fetching methods (manager details, league standings, fixtures, gameweek history, manager picks).
-   [ ] **Data Models**: Define all necessary `dataclasses` with appropriate fields and types.
-   [ ] **Analysis Engine**: Develop algorithms for all listed analytical features.
-   [ ] **Report Generator**: Implement functions to format and export data into JSON, CSV, Markdown, and generate plots.
-   [ ] **`main.py`**: Enhance CLI to dynamically fetch and display league managers, handle user input robustly, and integrate all components.
-   [ ] Add comprehensive error handling and logging.
-   [ ] Implement progress bars for long-running operations (e.g., using `rich.progress`).
-   [ ] Write unit tests for critical components.
-   [ ] Add ability to search for league ID by name if not provided.
-   [ ] More sophisticated caching strategies.

## Contributing

(Details on how to contribute if this were an open project)

## License

(Specify a license, e.g., MIT)