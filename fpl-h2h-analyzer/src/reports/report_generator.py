# Report Generator
# This file will contain functions for generating comprehensive H2H battle reports
# in various formats (JSON, CSV, Markdown, charts) using pandas and matplotlib.

import json
import csv
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import matplotlib.pyplot as plt

from ..models.manager import ManagerProfile, ManagerGameweekPicks # Added ManagerGameweekPicks
from typing import Optional # Import Optional
from ..models.h2h_league import H2HLeague
from ..analysis.manager_analyzer import get_overall_manager_stats
from ..analysis.h2h_comparator import calculate_h2h_record, identify_differentials, calculate_momentum
from config import REPORTS_DIR, TARGET_LEAGUE_ID # For default output and context


def generate_manager_comparison_report(
    manager1_profile: ManagerProfile,
    manager2_profile: ManagerProfile,
    h2h_league_data: H2HLeague,
    bootstrap_static_data: Dict[str, Any],
    latest_gw: int,
    manager1_picks_latest_gw: Optional[ManagerGameweekPicks], # Changed type hint
    manager2_picks_latest_gw: Optional[ManagerGameweekPicks], # Changed type hint
    output_formats: List[str] = ["json", "md"],
    output_filename_prefix: str = "h2h_battle_report"
) -> Dict[str, Path]:
    """Generates a comprehensive H2H comparison report for two managers."""
    
    report_data = {}
    output_paths: Dict[str, Path] = {}

    # 1. Basic Manager Info
    report_data['manager1_info'] = {
        'id': manager1_profile.id,
        'name': manager1_profile.name,
        'team_name': manager1_profile.team_name,
        'overall_rank': manager1_profile.overall_rank,
        'overall_points': manager1_profile.overall_points
    }
    report_data['manager2_info'] = {
        'id': manager2_profile.id,
        'name': manager2_profile.name,
        'team_name': manager2_profile.team_name,
        'overall_rank': manager2_profile.overall_rank,
        'overall_points': manager2_profile.overall_points
    }

    # 2. Overall Manager Stats (from manager_analyzer)
    report_data['manager1_overall_stats'] = get_overall_manager_stats(manager1_profile)
    report_data['manager2_overall_stats'] = get_overall_manager_stats(manager2_profile)

    # 3. H2H Record (from h2h_comparator)
    report_data['h2h_record'] = calculate_h2h_record(
        manager1_profile.id, manager2_profile.id, h2h_league_data
    )

    # 4. Differentials for the latest gameweek (from h2h_comparator)
    if manager1_picks_latest_gw and manager2_picks_latest_gw:
        try:
            report_data['latest_gw_differentials'] = identify_differentials(
                manager1_picks_latest_gw, 
                manager2_picks_latest_gw, 
                bootstrap_static_data
            )
        except Exception as e:
            report_data['latest_gw_differentials'] = f"Error processing picks for differentials: {e}"
    else:
        report_data['latest_gw_differentials'] = "Latest gameweek picks not available for one or both managers for differential analysis."

    # 5. Momentum (from h2h_comparator)
    report_data['manager1_momentum'] = calculate_momentum(manager1_profile, h2h_league_data)
    report_data['manager2_momentum'] = calculate_momentum(manager2_profile, h2h_league_data)

    # Ensure output directory exists
    report_dir = Path(REPORTS_DIR)
    report_dir.mkdir(parents=True, exist_ok=True)
    base_filename = f"{output_filename_prefix}_{manager1_profile.id}_vs_{manager2_profile.id}_gw{latest_gw}"

    # Generate reports in requested formats
    if "json" in output_formats:
        json_path = report_dir / f"{base_filename}.json"
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str) # Use default=str for non-serializable like Path or dataclasses
        output_paths["json"] = json_path
        print(f"JSON report saved to: {json_path}")

    if "md" in output_formats:
        md_path = report_dir / f"{base_filename}.md"
        md_content = _generate_markdown_report(report_data, manager1_profile, manager2_profile, latest_gw)
        with open(md_path, 'w') as f:
            f.write(md_content)
        output_paths["md"] = md_path
        print(f"Markdown report saved to: {md_path}")

    if "csv" in output_formats:
        csv_path = report_dir / f"{base_filename}_summary.csv"
        _generate_csv_report(report_data, csv_path)
        output_paths["csv"] = csv_path
        print(f"CSV report saved to: {csv_path}")

    if "chart" in output_formats:
        chart_path_prefix = report_dir / base_filename # Use base_filename directly for prefix
        chart_paths = _generate_charts(report_data, manager1_profile, manager2_profile, chart_path_prefix)
        output_paths.update(chart_paths) 

    return output_paths

def _generate_markdown_report(report_data: Dict, m1: ManagerProfile, m2: ManagerProfile, gw: int) -> str:
    """Helper to generate Markdown content from report_data."""
    md = f"# FPL H2H Battle Report: {m1.name} vs {m2.name} (GW{gw})\n\n"
    md += f"League ID: {TARGET_LEAGUE_ID}\n\n"

    # Manager Info
    md += f"## Manager Profiles\n"
    md += f"### {m1.name} (ID: {m1.id}, Team: {m1.team_name})\n"
    md += f"- Overall Rank: {m1.overall_rank}, Total Points: {m1.overall_points}\n"
    md += f"### {m2.name} (ID: {m2.id}, Team: {m2.team_name})\n"
    md += f"- Overall Rank: {m2.overall_rank}, Total Points: {m2.overall_points}\n\n"

    # H2H Record
    h2h = report_data.get('h2h_record', {})
    md += f"## Head-to-Head Record\n"
    if h2h.get('matches_played', 0) > 0:
        md += f"- Matches Played: {h2h.get('matches_played')}\n"
        md += f"- {m1.name} Wins: {h2h.get('manager1_wins')} ({h2h.get('manager1_total_fpl_points_in_h2h')} pts)\n"
        md += f"- {m2.name} Wins: {h2h.get('manager2_wins')} ({h2h.get('manager2_total_fpl_points_in_h2h')} pts)\n"
        md += f"- Draws: {h2h.get('draws')}\n\n"
    else:
        md += "- No H2H matches found between these managers in this league.\n\n"

    # Overall Stats Comparison
    m1_stats = report_data.get('manager1_overall_stats', {})
    m2_stats = report_data.get('manager2_overall_stats', {})
    md += f"## Overall Performance Comparison\n"
    md += f"| Metric                  | {m1.name:<20} | {m2.name:<20} |\n"
    md += f"|-------------------------|-----------------------|-----------------------|\n"
    md += f"| Average GW Points       | {m1_stats.get('average_gameweek_points', 0.0):<20.2f} | {m2_stats.get('average_gameweek_points', 0.0):<20.2f} |\n"
    md += f"| Consistency (Std Dev)   | {m1_stats.get('consistency_std_dev_points', 0.0):<20.2f} | {m2_stats.get('consistency_std_dev_points', 0.0):<20.2f} |\n"
    md += f"| Form (Last 3GW Avg)     | {m1_stats.get('form_last_3_gw', 0.0):<20.2f} | {m2_stats.get('form_last_3_gw', 0.0):<20.2f} |\n"
    md += f"| Total Transfers Made    | {m1_stats.get('transfer_analysis', {}).get('total_transfers_made', 'N/A'):<20} | {m2_stats.get('transfer_analysis', {}).get('total_transfers_made', 'N/A'):<20} |\n"
    md += f"| Total Hits Cost         | {m1_stats.get('transfer_analysis', {}).get('total_hits_cost', 'N/A'):<20} | {m2_stats.get('transfer_analysis', {}).get('total_hits_cost', 'N/A'):<20} |\n"
    # md += f"| Captain Success Rate    | {m1_stats.get('captain_success_rate_estimate', 'N/A'):<20} | {m2_stats.get('captain_success_rate_estimate', 'N/A'):<20} |\n" # Placeholder
    md += "\n"

    # Differentials (simplified)
    diffs = report_data.get('latest_gw_differentials')
    md += f"## Latest Gameweek ({gw}) Differentials\n"
    if isinstance(diffs, dict):
        md += f"### {m1.name}'s Differentials (Players in {m1.name}'s XI, not in {m2.name}'s XI):\n"
        for p in diffs.get('manager1_differentials', []): md += f"- {p.get('name', 'Unknown')} (ID: {p.get('id')})\n"
        if not diffs.get('manager1_differentials'): md += "- None\n"
        md += f"\n### {m2.name}'s Differentials (Players in {m2.name}'s XI, not in {m1.name}'s XI):\n"
        for p in diffs.get('manager2_differentials', []): md += f"- {p.get('name', 'Unknown')} (ID: {p.get('id')})\n"
        if not diffs.get('manager2_differentials'): md += "- None\n"
        md += f"\n### Shared Players (in XI):\n"
        for p in diffs.get('shared_players', []): md += f"- {p.get('name', 'Unknown')} (ID: {p.get('id')})\n"
        if not diffs.get('shared_players'): md += "- None\n"
        md += f"\n### Captaincy:\n"
        md += f"- {m1.name}'s Captain: {diffs.get('manager1_captain', {}).get('name', 'N/A')}\n"
        md += f"- {m2.name}'s Captain: {diffs.get('manager2_captain', {}).get('name', 'N/A')}\n"
        md += f"- Captains are Differential: {'Yes' if diffs.get('captain_is_differential') else 'No'}\n\n"
    elif isinstance(diffs, str): # Handle error messages or unavailability string
        md += f"- {diffs}\n\n"
    else:
        md += f"- Differential data not available or in unexpected format.\n\n"

    # Momentum
    m1_mom = report_data.get('manager1_momentum', {})
    m2_mom = report_data.get('manager2_momentum', {})
    md += f"## Momentum (Last {m1_mom.get('h2h_matches_considered_for_momentum', 'N')} GWs considered for H2H wins)\n"
    md += f"| Metric                  | {m1.name:<20} | {m2.name:<20} |\n"
    md += f"|-------------------------|-----------------------|-----------------------|\n"
    md += f"| H2H Wins (Recent)       | {m1_mom.get('h2h_wins_last_n_gws', 'N/A'):<20} | {m2_mom.get('h2h_wins_last_n_gws', 'N/A'):<20} |\n"
    md += f"| FPL Points Form (Avg)   | {m1_mom.get('fpl_points_form_last_n_gws', 'N/A'):<20.2f} | {m2_mom.get('fpl_points_form_last_n_gws', 'N/A'):<20.2f} |\n"
    md += "\n"

    md += "---\nReport generated by FPL H2H Analyzer."
    return md

def _generate_csv_report(report_data: Dict, csv_path: Path):
    """Helper to generate a summary CSV file."""
    m1_info = report_data.get('manager1_info', {})
    m2_info = report_data.get('manager2_info', {})
    m1_stats = report_data.get('manager1_overall_stats', {})
    m2_stats = report_data.get('manager2_overall_stats', {})
    h2h = report_data.get('h2h_record', {})

    header = [
        'Metric',
        m1_info.get('name', 'Manager 1'),
        m2_info.get('name', 'Manager 2')
    ]
    rows = [
        header,
        ['Manager ID', m1_info.get('id'), m2_info.get('id')],
        ['Overall Points', m1_info.get('summary_overall_points'), m2_info.get('summary_overall_points')],
        ['Overall Rank', m1_info.get('summary_overall_rank'), m2_info.get('summary_overall_rank')],
        ['Avg GW Points', f"{m1_stats.get('average_gameweek_points', 0):.2f}", f"{m2_stats.get('average_gameweek_points', 0):.2f}"],
        ['Consistency (StdDev)', f"{m1_stats.get('consistency_std_dev_points', 0):.2f}", f"{m2_stats.get('consistency_std_dev_points', 0):.2f}"],
        ['Form (Last 3GW)', f"{m1_stats.get('form_last_3_gw', 0):.2f}", f"{m2_stats.get('form_last_3_gw', 0):.2f}"],
        ['Total Transfers', m1_stats.get('transfer_analysis', {}).get('total_transfers_made', 'N/A'), m2_stats.get('transfer_analysis', {}).get('total_transfers_made', 'N/A')],
        ['Total Hits Cost', m1_stats.get('transfer_analysis', {}).get('total_hits_cost', 'N/A'), m2_stats.get('transfer_analysis', {}).get('total_hits_cost', 'N/A')],
        ['H2H Matches Played', h2h.get('matches_played', 'N/A'), h2h.get('matches_played', 'N/A')], # Same for both in this context
        [f"H2H Wins vs {m2_info.get('name', 'M2')}", h2h.get('manager1_wins', 'N/A'), ''],
        [f"H2H Wins vs {m1_info.get('name', 'M1')}", '', h2h.get('manager2_wins', 'N/A')],
        ['H2H Draws', h2h.get('draws', 'N/A'), h2h.get('draws', 'N/A')],
    ]

    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def _generate_charts(report_data: Dict, m1: ManagerProfile, m2: ManagerProfile, chart_file_prefix: Path) -> Dict[str, Path]:
    """Generates and saves charts comparing manager performance. Returns paths to saved charts."""
    charts_paths = {}
    
    m1_gw_history = m1.current_gameweek_history
    m2_gw_history = m2.current_gameweek_history

    if not m1_gw_history or not m2_gw_history:
        print("Chart generation skipped: Insufficient gameweek history for one or both managers.")
        return charts_paths

    df1 = pd.DataFrame([gw.to_dict() for gw in m1_gw_history])
    df2 = pd.DataFrame([gw.to_dict() for gw in m2_gw_history])

    if 'event' not in df1.columns or 'points' not in df1.columns or \
       'event' not in df2.columns or 'points' not in df2.columns:
        print("Chart generation skipped: 'event' or 'points' missing in gameweek history dataframes.")
        return charts_paths
    
    # Ensure 'event' is sorted for correct plotting, especially if data isn't guaranteed to be sorted
    df1 = df1.sort_values(by='event')
    df2 = df2.sort_values(by='event')

    plt.figure(figsize=(12, 6))
    plt.plot(df1['event'], df1['points'], label=f"{m1.name} GW Points", marker='o', linestyle='-')
    plt.plot(df2['event'], df2['points'], label=f"{m2.name} GW Points", marker='x', linestyle='--')
    
    plt.xlabel("Gameweek")
    plt.ylabel("Points")
    plt.title(f"Gameweek Points Progression: {m1.name} vs {m2.name}")
    plt.legend()
    plt.grid(True)
    
    # Ensure x-ticks cover all gameweeks present
    all_events = pd.concat([df1['event'], df2['event']]).unique()
    if len(all_events) > 0:
        plt.xticks(range(int(min(all_events)), int(max(all_events)) + 1))
    
    gw_points_chart_path = chart_file_prefix.with_suffix('.gw_points.png') # Use with_suffix for clarity
    plt.savefig(gw_points_chart_path)
    plt.close()
    charts_paths['gw_points_chart'] = gw_points_chart_path
    print(f"Gameweek points chart saved to: {gw_points_chart_path}")

    # Overall Rank Progression Chart
    if 'overall_rank' in df1.columns and 'overall_rank' in df2.columns:
        plt.figure(figsize=(12, 6))
        plt.plot(df1['event'], df1['overall_rank'], label=f"{m1.name} Overall Rank", marker='o', linestyle='-')
        plt.plot(df2['event'], df2['overall_rank'], label=f"{m2.name} Overall Rank", marker='x', linestyle='--')
        plt.xlabel("Gameweek")
        plt.ylabel("Overall Rank (Lower is better)")
        plt.title(f"Overall Rank Progression: {m1.name} vs {m2.name}")
        plt.legend()
        plt.grid(True)
        if len(all_events) > 0:
            plt.xticks(range(int(min(all_events)), int(max(all_events)) + 1))
        plt.gca().invert_yaxis() # Lower rank is better
        
        overall_rank_chart_path = chart_file_prefix.with_suffix('.overall_rank.png')
        plt.savefig(overall_rank_chart_path)
        plt.close()
        charts_paths['overall_rank_chart'] = overall_rank_chart_path
        print(f"Overall rank chart saved to: {overall_rank_chart_path}")
    else:
        print("Overall rank chart generation skipped: 'overall_rank' missing in gameweek history.")

    return charts_paths

# Example Usage (for testing purposes)
if __name__ == "__main__":
    from models.manager import GameweekPerformance, ManagerPick # For mock data
    from models.h2h_league import H2HMatch, H2HLeagueEntry # For mock data
    
    # Mock data (ensure it's comprehensive enough for all functions)
    m1_profile_data = {
        "id": 1, "name": "Manager Alpha", "player_name":"Manager Alpha", "team_name": "Alpha FC", "started_event": 1,
        "summary_overall_points": 180, "summary_overall_rank": 10000, # Corrected points
        "current_history": [
            {"event":1, "points":60, "total_points":60, "rank":1000000,"rank_sort":1000000,"overall_rank":1000000,"bank":0,"value":1000,"event_transfers":0,"event_transfers_cost":0,"points_on_bench":5},
            {"event":2, "points":70, "total_points":130, "rank":500000,"rank_sort":500000,"overall_rank":700000,"bank":0,"value":1002,"event_transfers":1,"event_transfers_cost":0,"points_on_bench":8},
            {"event":3, "points":50, "total_points":180, "rank":1200000,"rank_sort":1200000,"overall_rank":800000,"bank":0,"value":1001,"event_transfers":2,"event_transfers_cost":4,"points_on_bench":2},
        ],
        "past": [], "chips": []
    }
    m2_profile_data = {
        "id": 2, "name": "Manager Beta", "player_name":"Manager Beta", "team_name": "Beta United", "started_event": 1,
        "summary_overall_points": 180, "summary_overall_rank": 15000, # Corrected points
        "current_history": [
            {"event":1, "points":55, "total_points":55, "rank":1200000,"rank_sort":1200000,"overall_rank":1200000,"bank":0,"value":1000,"event_transfers":0,"event_transfers_cost":0,"points_on_bench":3},
            {"event":2, "points":65, "total_points":120, "rank":800000,"rank_sort":800000,"overall_rank":900000,"bank":0,"value":1003,"event_transfers":1,"event_transfers_cost":0,"points_on_bench":10},
            {"event":3, "points":60, "total_points":180, "rank":900000,"rank_sort":900000,"overall_rank":850000,"bank":0,"value":1005,"event_transfers":1,"event_transfers_cost":0,"points_on_bench":6},
        ],
        "past": [], "chips": []
    }
    # Use from_api_data which expects 'current_history', 'past', 'chips'
    manager1 = ManagerProfile.from_api_data(m1_profile_data) 
    manager2 = ManagerProfile.from_api_data(m2_profile_data)

    mock_h2h_league = H2HLeague(id=FPL_LEAGUE_ID, name="Test League", created="", closed=False, league_type='x', scoring='h2h', start_event=1, admin_entry=None, code_privacy=None, max_entries=None, cup_league=None, cup_qualified=None, has_cup=False, rank=None)
    mock_h2h_league.matches = {
        1: [H2HMatch(id=1, event=1, league_id=FPL_LEAGUE_ID, entry_1_entry=1, entry_1_name="Alpha FC", entry_1_player_name="Manager Alpha", entry_1_points=60, entry_1_win=1, entry_1_draw=0, entry_1_loss=0, entry_2_entry=2, entry_2_name="Beta United", entry_2_player_name="Manager Beta", entry_2_points=55, entry_2_win=0, entry_2_draw=0, entry_2_loss=1, is_knockout=False, winner=1, seed_value=None)],
        3: [H2HMatch(id=2, event=3, league_id=FPL_LEAGUE_ID, entry_1_entry=1, entry_1_name="Alpha FC", entry_1_player_name="Manager Alpha", entry_1_points=50, entry_1_win=0, entry_1_draw=0, entry_1_loss=1, entry_2_entry=2, entry_2_name="Beta United", entry_2_player_name="Manager Beta", entry_2_points=60, entry_2_win=1, entry_2_draw=0, entry_2_loss=0, is_knockout=False, winner=2, seed_value=None)]
    }
    mock_h2h_league.standings = {
        "has_next": False, "page":1,
        "results": [
            H2HLeagueEntry.from_standings_api_data({"id":10,"entry_name":"Alpha FC","player_name":"Manager Alpha","rank":1,"last_rank":1,"rank_sort":1,"total":6,"entry":1,"matches_played":2,"matches_won":1,"matches_drawn":0,"matches_lost":1,"points_for":110}),
            H2HLeagueEntry.from_standings_api_data({"id":11,"entry_name":"Beta United","player_name":"Manager Beta","rank":2,"last_rank":2,"rank_sort":2,"total":3,"entry":2,"matches_played":2,"matches_won":1,"matches_drawn":0,"matches_lost":1,"points_for":115})
        ]
    }

    mock_bootstrap = {"elements": [
        {"id": 101, "web_name": "Salah", "element_type":3, "team":10}, {"id": 102, "web_name": "Haaland", "element_type":4, "team":11}, {"id": 103, "web_name": "Saka", "element_type":3, "team":1}
    ]}

    # Mock picks for GW3 (latest GW in this example)
    # entry_history for ManagerGameweekPicks should be a GameweekPerformance object
    m1_gw3_perf_for_picks = next((gw for gw in manager1.current_gameweek_history if gw.event == 3), None)
    m2_gw3_perf_for_picks = next((gw for gw in manager2.current_gameweek_history if gw.event == 3), None)

    m1_picks_gw3_obj = None
    if m1_gw3_perf_for_picks:
        m1_picks_gw3_obj = ManagerGameweekPicks(
            active_chip=None, automatic_subs=[], 
            entry_history=m1_gw3_perf_for_picks,
            picks=[
                ManagerPick(element=101, position=1, multiplier=1, is_captain=False, is_vice_captain=False, purchase_price=125, selling_price=126),
                ManagerPick(element=102, position=2, multiplier=2, is_captain=True, is_vice_captain=False, purchase_price=140, selling_price=141)
            ]
        )
    
    m2_picks_gw3_obj = None
    if m2_gw3_perf_for_picks:
        m2_picks_gw3_obj = ManagerGameweekPicks(
            active_chip=None, automatic_subs=[], 
            entry_history=m2_gw3_perf_for_picks,
            picks=[
                ManagerPick(element=101, position=1, multiplier=1, is_captain=False, is_vice_captain=False, purchase_price=125, selling_price=126),
                ManagerPick(element=103, position=2, multiplier=2, is_captain=True, is_vice_captain=False, purchase_price=90, selling_price=91)
            ]
        )

    print("Generating H2H comparison report...")
    output_files = generate_manager_comparison_report(
        manager1_profile=manager1,
        manager2_profile=manager2,
        h2h_league_data=mock_h2h_league,
        bootstrap_static_data=mock_bootstrap,
        latest_gw=3,
        manager1_picks_latest_gw=m1_picks_gw3_obj, 
        manager2_picks_latest_gw=m2_picks_gw3_obj,
        output_formats=["json", "md", "csv", "chart"],
        output_filename_prefix="test_report_alpha_vs_beta"
    )

    print("\nReport generation test complete. Output files:")
    for fmt, path in output_files.items():
        print(f"- {fmt.upper()}: {path}")

    if "md" in output_files and output_files["md"].exists():
        with open(output_files["md"], 'r') as f_md:
            print("\n--- Markdown Report Content (First 300 chars) ---")
            print(f_md.read(300) + "...")
            print("--- End of Preview ---")
    elif "md" in output_files:
        print(f"Markdown file {output_files['md']} was not created.")