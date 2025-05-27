# Main Application
# This file will serve as the main application entry point.

import time
from typing import List, Optional, Tuple

from rich.console import Console
from rich.markup import escape
from rich.prompt import IntPrompt
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.live import Live

from src.api.fpl_client import FPLAPIClient
from config import TARGET_LEAGUE_ID, TARGET_LEAGUE_NAME # Use configured league ID and name
from .models.manager import ManagerProfile, ManagerGameweekPicks # Add ManagerGameweekPicks
from .models.h2h_league import H2HLeague, H2HLeagueEntry
from .reports.report_generator import generate_manager_comparison_report

CONSOLE = Console()

def get_current_gameweek(bootstrap_data: dict) -> Optional[int]:
    """Extracts the current gameweek from bootstrap-static data."""
    events = bootstrap_data.get('events', [])
    for event in events:
        if event.get('is_current') is True:
            return event.get('id')
    return None

def select_managers_from_league(
    league_members: List[H2HLeagueEntry],
    num_managers_to_select: int = 2
) -> List[H2HLeagueEntry]:
    """Allows user to select managers from the league for comparison."""
    if not league_members:
        CONSOLE.print("[bold red]No league members found to select from.[/bold red]")
        return []

    table = Table(title="Available Managers in League")
    table.add_column("No.", style="dim", width=6)
    table.add_column("Manager Name", style="cyan")
    table.add_column("Team Name", style="magenta")
    table.add_column("Entry ID", style="green")

    for idx, member in enumerate(league_members):
        table.add_row(str(idx + 1), member.player_name, member.entry_name, str(member.entry_id))
    
    CONSOLE.print(table)
    
    selected_managers = []
    selected_indices = set()

    for i in range(num_managers_to_select):
        while True:
            try:
                choice = IntPrompt.ask(
                    f"Select Manager {i + 1} (enter number)", 
                    choices=[str(j+1) for j in range(len(league_members)) if j not in selected_indices],
                    show_choices=False # Choices are already in table
                )
                selected_index = choice - 1
                if selected_index not in selected_indices:
                    selected_indices.add(selected_index)
                    selected_managers.append(league_members[selected_index])
                    CONSOLE.print(f"[green]Selected: {league_members[selected_index].player_name}[/green]")
                    break
                else:
                    CONSOLE.print("[yellow]Manager already selected. Please choose a different one.[/yellow]") 
            except ValueError:
                CONSOLE.print("[red]Invalid input. Please enter a number from the list.[/red]")
            except Exception as e:
                CONSOLE.print(f"[red]An error occurred: {e}. Please try again.[/red]")
                # Potentially re-prompt or exit if error is persistent
                # For now, just re-prompt

    return selected_managers

from src.utils.debug import DebugLogger

def fetch_all_required_data(
    client: FPLAPIClient,
    league_id: int,
    manager_ids: List[int],
    progress: Progress,
    debug_logger: Optional[DebugLogger] = None
) -> Tuple[Optional[dict], Optional[H2HLeague], List[ManagerProfile], Optional[int], List[Optional[dict]]]:
    """Fetches all data required for the analysis and report with enhanced error handling and debugging."""

    bootstrap_task = progress.add_task("[cyan]Fetching bootstrap data...[/cyan]", total=1)
    league_task = progress.add_task("[cyan]Fetching H2H league data...[/cyan]", total=1)
    managers_task = progress.add_task("[cyan]Fetching manager profiles...[/cyan]", total=len(manager_ids))
    picks_task = progress.add_task("[cyan]Fetching manager picks...[/cyan]", total=len(manager_ids))

    bootstrap_data = client.get_bootstrap_static()
    progress.update(bootstrap_task, advance=1, description="[green]Bootstrap data fetched.[/green]")
    if debug_logger and bootstrap_data:
        debug_logger.log_api_response("bootstrap-static", bootstrap_data)
    if not bootstrap_data:
        error_details = {"message": "Failed to fetch bootstrap data.", "league_id": league_id, "manager_ids": manager_ids}
        if debug_logger:
            debug_logger.log_error("bootstrap_fetch_failed", error_details)
        CONSOLE.print("[bold red]Error: Failed to fetch bootstrap data. Please check your internet connection or the FPL API status.[/bold red]")
        return None, None, [], None, []

    current_gw = get_current_gameweek(bootstrap_data)
    if current_gw is None:
        error_details = {"message": "Could not determine current gameweek.", "bootstrap_keys": list(bootstrap_data.keys()) if bootstrap_data else "N/A"}
        if debug_logger:
            debug_logger.log_error("current_gameweek_failed", error_details)
        CONSOLE.print("[bold red]Error: Could not determine current gameweek from bootstrap data. The API structure might have changed.[/bold red]")
        return bootstrap_data, None, [], None, []
    CONSOLE.print(f"[info]Current Gameweek: {current_gw}[/info]")

    h2h_league_data_standings = client.get_h2h_league_standings(league_id)
    progress.update(league_task, advance=1, description="[green]H2H league standings fetched.[/green]")
    if debug_logger and h2h_league_data_standings:
        debug_logger.log_api_response(f"leagues-h2h/{league_id}/standings", h2h_league_data_standings)
    if not h2h_league_data_standings or not h2h_league_data_standings.get('standings', {}).get('results'):
        error_details = {"message": "Failed to fetch H2H league standings.", "league_id": league_id, "response_keys": list(h2h_league_data_standings.keys()) if h2h_league_data_standings else "N/A"}
        if debug_logger:
            debug_logger.log_error("h2h_standings_fetch_failed", error_details)
        CONSOLE.print(f"[bold red]Error: Failed to fetch H2H league standings for league {league_id}. The league ID might be incorrect or the API is unavailable.[/bold red]")
        return bootstrap_data, None, [], current_gw, []

    # Create H2HLeague object from standings
    h2h_league_obj = H2HLeague.from_standings_api_data(h2h_league_data_standings)

    # Fetch H2H matches and update the league object
    all_matches_data = client.get_h2h_league_matches(league_id)
    if debug_logger and all_matches_data:
        debug_logger.log_api_response(f"leagues-h2h-matches/league/{league_id}", all_matches_data)
    if all_matches_data and all_matches_data.get('results'):
        h2h_league_obj.update_matches_from_api_data(all_matches_data['results'])
    else:
        error_details = {"message": "Could not fetch H2H match details.", "league_id": league_id, "response_keys": list(all_matches_data.keys()) if all_matches_data else "N/A"}
        if debug_logger:
            debug_logger.log_error("h2h_matches_fetch_failed", error_details)
        CONSOLE.print(f"[yellow]Warning: Could not fetch H2H match details for league {league_id}. H2H record might be incomplete.[/yellow]")

    manager_profiles: List[ManagerProfile] = []
    manager_picks_latest_gw: List[Optional[ManagerGameweekPicks]] = []  # Change type

    for manager_id in manager_ids:
        # CONSOLE.print(f"Fetching data for manager ID: {manager_id}...") # Progress bar handles this
        manager_info_raw = client.get_manager_info(manager_id)
        if debug_logger and manager_info_raw:
            debug_logger.log_api_response(f"entry/{manager_id}", manager_info_raw, manager_id=manager_id)

        manager_history_raw = client.get_manager_history(manager_id)
        if debug_logger and manager_history_raw:
            debug_logger.log_api_response(f"entry/{manager_id}/history", manager_history_raw, manager_id=manager_id)

        if manager_info_raw and manager_history_raw:
            try:
                profile_data = manager_info_raw
                profile_data.update(manager_history_raw)

                manager_profile = ManagerProfile.from_entry_api_data(profile_data)
                manager_profiles.append(manager_profile)
                progress.update(managers_task, advance=1, description=f"[green]Fetched profile for {manager_profile.name}[/green]")

                picks_data = client.get_manager_picks(manager_id, current_gw)
                if picks_data:
                    # Convert raw dict to ManagerGameweekPicks object
                    try:
                        picks_obj = ManagerGameweekPicks.from_api_data(picks_data)
                        manager_picks_latest_gw.append(picks_obj)
                    except Exception as e:
                        CONSOLE.print(f"[yellow]Warning: Could not parse picks for manager {manager_id}: {str(e)}[/yellow]")
                        manager_picks_latest_gw.append(None)
                else:
                    manager_picks_latest_gw.append(None)
                progress.update(picks_task, advance=1)
            except Exception as e:
                 error_details = {"message": "Error processing manager data.", "manager_id": manager_id, "error": str(e)}
                 if debug_logger:
                     debug_logger.log_error("manager_data_processing_failed", error_details)
                 CONSOLE.print(f"[bold red]Error processing data for manager {manager_id}: {escape(str(e))}. Skipping.[/bold red]")
                 manager_picks_latest_gw.append(None) # Ensure lists stay aligned
        else:
            error_details = {"message": "Failed to fetch complete data for manager.", "manager_id": manager_id, "info_fetched": bool(manager_info_raw), "history_fetched": bool(manager_history_raw)}
            if debug_logger:
                debug_logger.log_error("manager_fetch_failed", error_details)
            CONSOLE.print(f"[bold red]Failed to fetch complete data for manager {manager_id}. Skipping.[/bold red]")
            manager_picks_latest_gw.append(None) # Ensure lists stay aligned
            progress.update(managers_task, advance=1)
            progress.update(picks_task, advance=1)

    progress.update(managers_task, description="[green]All manager profiles processed.[/green]")
    progress.update(picks_task, description="[green]All manager picks processed.[/green]")

    return bootstrap_data, h2h_league_obj, manager_profiles, current_gw, manager_picks_latest_gw

def main():
    CONSOLE.print("[bold cyan]Fantasy Premier League H2H Analyzer[/bold cyan]")
    CONSOLE.print(f"Targeting League: [bold yellow]{TARGET_LEAGUE_NAME} (ID: {TARGET_LEAGUE_ID})[/bold yellow]")

    client = FPLAPIClient()
    debug_logger = DebugLogger() # Initialize debug logger

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=CONSOLE,
        transient=True # Hide progress bar when task is complete
    ) as progress:
        league_members_task = progress.add_task("[cyan]Fetching league members...[/cyan]", total=1)
        initial_league_standings_data = client.get_h2h_league_standings(TARGET_LEAGUE_ID)
        progress.update(league_members_task, advance=1, description="[green]League members fetched.[/green]")

        if not initial_league_standings_data or not initial_league_standings_data.get("standings", {}).get("results"):
            CONSOLE.print(f"[bold red]Error: Could not fetch league members for {TARGET_LEAGUE_NAME}. The league ID might be incorrect or the API is unavailable.[/bold red]")
            return

        league_members_entries = [
            H2HLeagueEntry.from_api_data(entry_data) 
            for entry_data in initial_league_standings_data["standings"]["results"]
        ]

        if not league_members_entries:
            CONSOLE.print(f"[bold red]Error: No league members found in {TARGET_LEAGUE_NAME}. Please check the league ID.[/bold red]")
            return

        selected_entries = select_managers_from_league(league_members_entries, num_managers_to_select=2)

        if len(selected_entries) < 2:
            CONSOLE.print("[bold red]Not enough managers selected for comparison. Please select at least two managers.[/bold red]")
            return

        manager1_entry, manager2_entry = selected_entries[0], selected_entries[1]
        manager_ids_to_fetch = [manager1_entry.entry_id, manager2_entry.entry_id]

        CONSOLE.print(f"\nComparing [bold magenta]{manager1_entry.player_name}[/bold magenta] vs [bold magenta]{manager2_entry.player_name}[/bold magenta]...")

        bootstrap_data, h2h_league_full_data, manager_profiles, current_gw, manager_picks_raw = \
            fetch_all_required_data(client, TARGET_LEAGUE_ID, manager_ids_to_fetch, progress, debug_logger)

        if not manager_profiles or len(manager_profiles) < 2:
            CONSOLE.print("[bold red]Could not fetch data for the selected managers. Aborting.[/bold red]")
            return

        manager1_profile = next((p for p in manager_profiles if p.id == manager1_entry.entry_id), None)
        manager2_profile = next((p for p in manager_profiles if p.id == manager2_entry.entry_id), None)

        if not manager1_profile or not manager2_profile:
             CONSOLE.print("[bold red]Could not find profile data for one or both selected managers after fetching. Aborting.[/bold red]")
             return

        # Find the raw picks data for each manager
        manager1_picks_raw = next((p for p, entry in zip(manager_picks_raw, manager_ids_to_fetch) if entry == manager1_entry.entry_id), None)
        manager2_picks_raw = next((p for p, entry in zip(manager_picks_raw, manager_ids_to_fetch) if entry == manager2_entry.entry_id), None)

        if not manager1_picks_raw or not manager2_picks_raw:
             CONSOLE.print(f"[bold red]Could not fetch picks data for one or both managers for gameweek {current_gw}. Aborting.[/bold red]")
             return

        # Generate and print the report
        report = generate_manager_comparison_report(
            manager1_profile,
            manager2_profile,
            h2h_league_full_data, # Pass the full league data including matches
            bootstrap_data, # Pass bootstrap data for element info
            current_gw,
            manager1_picks_raw,
            manager2_picks_raw
        )
        CONSOLE.print(report)

    CONSOLE.print("\n[bold green]Analysis complete. Thank you for using FPL H2H Analyzer![/bold green]")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Log any unhandled exceptions
        debug_logger = DebugLogger() # Re-initialize if main failed before logger was created
        error_details = {"message": "An unhandled error occurred.", "error": str(e)}
        debug_logger.log_error("unhandled_exception", error_details)
        CONSOLE.print(f"[bold red]An unexpected error occurred: {escape(str(e))}. Check debug logs for details.[/bold red]")