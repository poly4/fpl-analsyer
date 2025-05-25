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
from .models.manager import ManagerProfile
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

def fetch_all_required_data(
    client: FPLAPIClient, 
    league_id: int, 
    manager_ids: List[int],
    progress: Progress
) -> Tuple[Optional[dict], Optional[H2HLeague], List[ManagerProfile], Optional[int], List[Optional[dict]]]:
    """Fetches all data required for the analysis and report."""
    
    bootstrap_task = progress.add_task("[cyan]Fetching bootstrap data...[/cyan]", total=1)
    league_task = progress.add_task("[cyan]Fetching H2H league data...[/cyan]", total=1)
    managers_task = progress.add_task("[cyan]Fetching manager profiles...[/cyan]", total=len(manager_ids))
    picks_task = progress.add_task("[cyan]Fetching manager picks...[/cyan]", total=len(manager_ids))

    bootstrap_data = client.get_bootstrap_static()
    progress.update(bootstrap_task, advance=1, description="[green]Bootstrap data fetched.[/green]")
    if not bootstrap_data:
        CONSOLE.print("[bold red]Failed to fetch bootstrap data. Exiting.[/bold red]")
        return None, None, [], None, []

    current_gw = get_current_gameweek(bootstrap_data)
    if current_gw is None:
        CONSOLE.print("[bold red]Could not determine current gameweek. Exiting.[/bold red]")
        return bootstrap_data, None, [], None, []
    CONSOLE.print(f"[info]Current Gameweek: {current_gw}[/info]")

    h2h_league_data_standings = client.get_h2h_league_standings(league_id)
    progress.update(league_task, advance=1, description="[green]H2H league standings fetched.[/green]")
    if not h2h_league_data_standings:
        CONSOLE.print(f"[bold red]Failed to fetch H2H league standings for league {league_id}. Exiting.[/bold red]")
        return bootstrap_data, None, [], current_gw, []
    
    # Create H2HLeague object from standings
    h2h_league_obj = H2HLeague.from_standings_api_data(h2h_league_data_standings)

    # Fetch H2H matches and update the league object
    all_matches_data = client.get_h2h_league_matches(league_id)
    if all_matches_data:
        h2h_league_obj.update_matches_from_api_data(all_matches_data['results'])
    else:
        CONSOLE.print(f"[yellow]Warning: Could not fetch H2H match details for league {league_id}. H2H record might be incomplete.[/yellow]")

    manager_profiles: List[ManagerProfile] = []
    manager_picks_latest_gw: List[Optional[dict]] = [] # Storing as dicts for now

    for manager_id in manager_ids:
        CONSOLE.print(f"Fetching data for manager ID: {manager_id}...")
        manager_info_raw = client.get_manager_info(manager_id)
        manager_history_raw = client.get_manager_history(manager_id)
        
        if manager_info_raw and manager_history_raw:
            profile_data = manager_info_raw 
            profile_data.update(manager_history_raw) 
            
            manager_profile = ManagerProfile.from_entry_api_data(profile_data)
            manager_profiles.append(manager_profile)
            progress.update(managers_task, advance=1)

            picks_data = client.get_manager_picks(manager_id, current_gw)
            manager_picks_latest_gw.append(picks_data) 
            progress.update(picks_task, advance=1)
        else:
            CONSOLE.print(f"[bold red]Failed to fetch complete data for manager {manager_id}. Skipping.[/bold red]")
            manager_picks_latest_gw.append(None) 
    
    progress.update(managers_task, description="[green]Manager profiles fetched.[/green]")
    progress.update(picks_task, description="[green]Manager picks fetched.[/green]")

    return bootstrap_data, h2h_league_obj, manager_profiles, current_gw, manager_picks_latest_gw

def main():
    CONSOLE.print("[bold cyan]Fantasy Premier League H2H Analyzer[/bold cyan]")
    CONSOLE.print(f"Targeting League: [bold yellow]{TARGET_LEAGUE_NAME} (ID: {TARGET_LEAGUE_ID})[/bold yellow]")

    client = FPLAPIClient()

    with Progress(
        "[progress.description]{task.description}",
        "[progress.percentage]{task.percentage:>3.0f}%",
        console=CONSOLE
    ) as progress:
        league_members_task = progress.add_task("[cyan]Fetching league members...[/cyan]", total=1)
        initial_league_standings_data = client.get_h2h_league_standings(TARGET_LEAGUE_ID)
        progress.update(league_members_task, advance=1, description="[green]League members fetched.[/green]")

        if not initial_league_standings_data or not initial_league_standings_data.get("standings", {}).get("results"):
            CONSOLE.print(f"[bold red]Could not fetch league members for {TARGET_LEAGUE_NAME}. Exiting.[/bold red]")
            return

        league_members_entries = [
            H2HLeagueEntry.from_api_data(entry_data) 
            for entry_data in initial_league_standings_data["standings"]["results"]
        ]

        if not league_members_entries:
            CONSOLE.print(f"[bold red]No league members found in {TARGET_LEAGUE_NAME}. Exiting.[/bold red]")
            return

        selected_entries = select_managers_from_league(league_members_entries, num_managers_to_select=2)

        if len(selected_entries) < 2:
            CONSOLE.print("[bold red]Not enough managers selected for comparison. Exiting.[/bold red]")
            return

        manager1_entry, manager2_entry = selected_entries[0], selected_entries[1]
        manager_ids_to_fetch = [manager1_entry.entry_id, manager2_entry.entry_id]

        CONSOLE.print(f"\nComparing [bold magenta]{manager1_entry.player_name}[/bold magenta] vs [bold magenta]{manager2_entry.player_name}[/bold magenta]...")

        bootstrap_data, h2h_league_full_data, manager_profiles, current_gw, manager_picks_raw = \
            fetch_all_required_data(client, TARGET_LEAGUE_ID, manager_ids_to_fetch, progress)

        if not bootstrap_data or not h2h_league_full_data or len(manager_profiles) < 2 or current_gw is None:
            CONSOLE.print("[bold red]Failed to fetch all necessary data for comparison. Exiting.[/bold red]")
            return
        
        m1_profile = next((p for p in manager_profiles if p.id == manager1_entry.entry_id), None)
        m2_profile = next((p for p in manager_profiles if p.id == manager2_entry.entry_id), None)
        
        # Ensure picks raw data aligns with profiles, assuming order is maintained from manager_ids_to_fetch
        m1_picks_raw_data = None
        m2_picks_raw_data = None
        if m1_profile and manager_ids_to_fetch.index(m1_profile.id) < len(manager_picks_raw):
            m1_picks_raw_data = manager_picks_raw[manager_ids_to_fetch.index(m1_profile.id)]
        if m2_profile and manager_ids_to_fetch.index(m2_profile.id) < len(manager_picks_raw):
            m2_picks_raw_data = manager_picks_raw[manager_ids_to_fetch.index(m2_profile.id)]

        if not m1_profile or not m2_profile:
            CONSOLE.print("[bold red]Could not retrieve profiles for one or both selected managers. Exiting.[/bold red]")
            return

        from src.models.manager import ManagerGameweekPicks 
        m1_picks_obj = ManagerGameweekPicks.from_api_data(m1_picks_raw_data) if m1_picks_raw_data else None
        m2_picks_obj = ManagerGameweekPicks.from_api_data(m2_picks_raw_data) if m2_picks_raw_data else None

        report_generation_task = progress.add_task("[cyan]Generating comparison report...[/cyan]", total=1)
        try:
            output_files = generate_manager_comparison_report(
                manager1_profile=m1_profile,
                manager2_profile=m2_profile,
                h2h_league_data=h2h_league_full_data,
                bootstrap_static_data=bootstrap_data,
                latest_gw=current_gw,
                manager1_picks_latest_gw=m1_picks_obj, 
                manager2_picks_latest_gw=m2_picks_obj,
                output_formats=["json", "md", "csv", "chart"], 
                output_filename_prefix=f"{TARGET_LEAGUE_NAME.replace(' ', '_')}_H2H"
            )
            progress.update(report_generation_task, advance=1, description="[green]Comparison report generated.[/green]")
            CONSOLE.print("\n[bold green]Report Generation Complete![/bold green]")
            for fmt, path in output_files.items():
                CONSOLE.print(f"- {fmt.upper()} report saved to: {escape(str(path))}")
        except Exception as e:
            progress.update(report_generation_task, advance=1, description="[red]Report generation failed.[/red]")
            CONSOLE.print(f"[bold red]An error occurred during report generation: {escape(str(e))}[/bold red]")
            import traceback
            CONSOLE.print(traceback.format_exc())

    CONSOLE.print("\nThank you for using the FPL H2H Analyzer!")

if __name__ == "__main__":
    main()