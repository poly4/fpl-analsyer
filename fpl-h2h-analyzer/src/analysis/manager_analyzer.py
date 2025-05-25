# Manager Analysis Engine
# This file will contain functions for analyzing individual manager performance.

import statistics
from typing import List, Dict, Any, Optional, Tuple

from ..models.manager import ManagerProfile, GameweekPerformance, ManagerGameweekPicks
# We might need bootstrap data (players, teams, etc.) for more detailed analysis like captain points
# from api.fpl_client import FPLAPIClient

def calculate_average_points(manager_profile: ManagerProfile) -> float:
    """Calculates the average gameweek points for the manager this season."""
    if not manager_profile.current_gameweek_history:
        return 0.0
    total_points = sum(gw.points for gw in manager_profile.current_gameweek_history)
    return total_points / len(manager_profile.current_gameweek_history)

def calculate_consistency(manager_profile: ManagerProfile) -> float:
    """Calculates the standard deviation of gameweek points as a measure of consistency."""
    if len(manager_profile.current_gameweek_history) < 2:
        return 0.0  # Not enough data for standard deviation
    points_list = [gw.points for gw in manager_profile.current_gameweek_history]
    return statistics.stdev(points_list)

def calculate_form(manager_profile: ManagerProfile, last_n_gameweeks: int = 5) -> float:
    """Calculates average points over the last N gameweeks."""
    relevant_gws = sorted(manager_profile.current_gameweek_history, key=lambda gw: gw.event, reverse=True)
    form_gws = relevant_gws[:last_n_gameweeks]
    if not form_gws:
        return 0.0
    total_form_points = sum(gw.points for gw in form_gws)
    return total_form_points / len(form_gws)

def analyze_transfers(manager_profile: ManagerProfile) -> Dict[str, Any]:
    """Analyzes transfer activity for the current season."""
    total_transfers = 0
    total_hits_cost = 0
    gameweeks_with_hits = 0

    for gw_perf in manager_profile.current_gameweek_history:
        total_transfers += gw_perf.event_transfers
        total_hits_cost += gw_perf.event_transfers_cost
        if gw_perf.event_transfers_cost < 0: # FPL API uses negative for cost
            gameweeks_with_hits += 1
            
    return {
        "total_transfers": total_transfers,
        "total_hits_cost": abs(total_hits_cost), # Make it positive for display
        "average_transfers_per_gw": total_transfers / len(manager_profile.current_gameweek_history) if manager_profile.current_gameweek_history else 0,
        "gameweeks_with_hits": gameweeks_with_hits
    }

def analyze_captain_success(
    manager_profile: ManagerProfile, 
    manager_picks_history: Dict[int, ManagerGameweekPicks], # Gameweek: Picks
    bootstrap_static_data: Dict[str, Any], # General game data (players, etc.)
    min_captain_return_threshold: int = 8 # Arbitrary threshold for a 'successful' captain pick (e.g. 8+ points)
) -> Dict[str, Any]:
    """
    Analyzes captaincy choices throughout the season.
    Requires manager's gameweek picks and bootstrap static data for player details.
    """
    successful_captain_picks = 0
    total_captain_picks = 0
    total_captain_points = 0
    # TODO: More detailed analysis like points if vice-captain played, blank captains etc.

    if not bootstrap_static_data or 'elements' not in bootstrap_static_data:
        return {"error": "Bootstrap static data not available for captain analysis."}

    player_points_map: Dict[int, Dict[int, int]] = {}
    # This map would be: {player_id: {gameweek: points_scored_in_gw}}
    # For simplicity, we'll assume we can get player points directly. In reality, this is complex.
    # The `live` endpoint for a gameweek gives player points, or `element-summary` for a player.
    # For this example, we'll simulate it or assume it's pre-fetched.

    # Simplified: We need a way to get actual points for each player for each gameweek.
    # This is not directly in manager_picks. It's in the general event live data or player summary.
    # For now, this function will be a placeholder or require pre-processed player_points_map.

    for gw_num, gw_picks in manager_picks_history.items():
        if not gw_picks.picks:
            continue

        captain_id = None
        # vice_captain_id = None # For future use
        for pick in gw_picks.picks:
            if pick.is_captain:
                captain_id = pick.element
            # if pick.is_vice_captain:
            #     vice_captain_id = pick.element
        
        if captain_id is not None:
            total_captain_picks += 1
            # --- This is the complex part: getting the captain's actual points for that gameweek ---
            # This requires looking up `captain_id` in `bootstrap_static_data` (for their general info)
            # and then finding their points for `gw_num`. The `element_summary` endpoint for a player
            # has their `history` which includes points per gameweek.
            # For this placeholder, we'll assume a mock value or skip if not available.
            
            # Example: find player in bootstrap_static_data
            # captain_player_data = next((p for p in bootstrap_static_data['elements'] if p['id'] == captain_id), None)
            # if captain_player_data:
            #   # Now find points for gw_num. This is the tricky bit without more API calls or pre-processing.
            #   # Let's assume we have a way to get this, e.g. from a pre-populated player_points_map
            #   # captain_actual_points_for_gw = player_points_map.get(captain_id, {}).get(gw_num, 0)
            #   # captain_score_in_gw_picks = captain_actual_points_for_gw * pick.multiplier (already in gw_picks.entry_history.points?)
            
            # Simplified: For now, we can't accurately calculate this without more data/logic.
            # We could check if the manager's total points for the GW were high, as a proxy, but that's not captain success.
            pass # Placeholder for actual captain points calculation

    # This is a very simplified version. Real captain success needs detailed player point lookups per GW.
    return {
        "total_captain_picks": total_captain_picks,
        "successful_captain_picks": successful_captain_picks, # Needs implementation
        "average_captain_points": total_captain_points / total_captain_picks if total_captain_picks > 0 else 0, # Needs implementation
        "success_rate": successful_captain_picks / total_captain_picks if total_captain_picks > 0 else 0 # Needs implementation
    }


def get_overall_manager_stats(manager_profile: ManagerProfile) -> Dict[str, Any]:
    """Compiles a summary of overall manager statistics."""
    if not manager_profile.current_gameweek_history:
        return {
            "error": "No gameweek history available for this manager.",
            "manager_id": manager_profile.id,
            "manager_name": manager_profile.name
        }

    latest_gw_perf = max(manager_profile.current_gameweek_history, key=lambda gw: gw.event, default=None)

    return {
        "manager_id": manager_profile.id,
        "manager_name": manager_profile.name,
        "team_name": manager_profile.team_name,
        "overall_rank": manager_profile.overall_rank if manager_profile.overall_rank is not None else latest_gw_perf.overall_rank if latest_gw_perf else 'N/A',
        "total_points": manager_profile.overall_points if manager_profile.overall_points is not None else latest_gw_perf.total_points if latest_gw_perf else 'N/A',
        "average_gameweek_points": calculate_average_points(manager_profile),
        "consistency_stdev": calculate_consistency(manager_profile),
        "form_last_5_gws": calculate_form(manager_profile, 5),
        "transfer_analysis": analyze_transfers(manager_profile),
        "chips_used_this_season": [chip['name'] for chip in manager_profile.chips_played],
        "last_gameweek_points": latest_gw_perf.points if latest_gw_perf else 'N/A',
        "current_team_value": latest_gw_perf.value / 10 if latest_gw_perf and latest_gw_perf.value is not None else 'N/A', # In millions
        "bank": latest_gw_perf.bank / 10 if latest_gw_perf and latest_gw_perf.bank is not None else 'N/A' # In millions
    }

# Example Usage (for testing purposes)
if __name__ == "__main__":
    # Create mock ManagerProfile data (similar to what's in models/manager.py for testing)
    mock_gw1 = GameweekPerformance(event=1, points=60, total_points=60, rank=10000, rank_sort=10000, overall_rank=10000, bank=0, value=1000, event_transfers=0, event_transfers_cost=0, points_on_bench=5)
    mock_gw2 = GameweekPerformance(event=2, points=75, total_points=135, rank=5000, rank_sort=5000, overall_rank=5000, bank=5, value=1002, event_transfers=1, event_transfers_cost=0, points_on_bench=8, chip_played='bboost')
    mock_gw3 = GameweekPerformance(event=3, points=50, total_points=185, rank=8000, rank_sort=8000, overall_rank=6000, bank=2, value=1005, event_transfers=2, event_transfers_cost=-4, points_on_bench=12)
    
    test_manager = ManagerProfile(
        id=123, name="Test Analyzer Manager", team_name="Analyzer FC", started_event=1, 
        overall_rank=6000, overall_points=185,
        current_gameweek_history=[mock_gw1, mock_gw2, mock_gw3],
        past_seasons=[],
        chips_played=[{"name": "bboost", "event": 2}]
    )

    print(f"Analyzing manager: {test_manager.name}")
    
    avg_points = calculate_average_points(test_manager)
    print(f"Average Gameweek Points: {avg_points:.2f}")

    consistency = calculate_consistency(test_manager)
    print(f"Consistency (Std Dev of Points): {consistency:.2f}")

    form = calculate_form(test_manager, last_n_gameweeks=2)
    print(f"Form (Avg Pts Last 2 GWs): {form:.2f}")

    transfers_info = analyze_transfers(test_manager)
    print(f"Transfer Analysis: {transfers_info}")

    # Mock data for captain analysis (very simplified)
    # In a real scenario, FPLAPIClient would fetch this, and bootstrap_static_data would be large.
    mock_picks_gw1 = ManagerGameweekPicks(active_chip=None, automatic_subs=[], entry_history=mock_gw1, picks=[
        ManagerPick(element=10, position=1, multiplier=1, is_captain=False, is_vice_captain=False),
        ManagerPick(element=20, position=2, multiplier=2, is_captain=True, is_vice_captain=False), # Captain
    ])
    mock_picks_gw2 = ManagerGameweekPicks(active_chip='bboost', automatic_subs=[], entry_history=mock_gw2, picks=[
        ManagerPick(element=30, position=1, multiplier=1, is_captain=False, is_vice_captain=False),
        ManagerPick(element=40, position=2, multiplier=2, is_captain=True, is_vice_captain=False), # Captain
    ])
    mock_manager_picks_history = {1: mock_picks_gw1, 2: mock_picks_gw2}
    mock_bootstrap_data = {"elements": [{"id": 20, "web_name": "PlayerA"}, {"id": 40, "web_name": "PlayerB"}] } # Highly simplified

    # Captain analysis is a placeholder and won't produce meaningful results with current mock data structure
    captain_analysis = analyze_captain_success(test_manager, mock_manager_picks_history, mock_bootstrap_data)
    print(f"Captain Success Analysis (Placeholder): {captain_analysis}")

    overall_stats = get_overall_manager_stats(test_manager)
    print("\nOverall Manager Stats:")
    for key, value in overall_stats.items():
        if isinstance(value, dict):
            print(f"  {key.replace('_', ' ').title()}:")
            for sub_key, sub_value in value.items():
                print(f"    {sub_key.replace('_', ' ').title()}: {sub_value}")
        else:
            print(f"  {key.replace('_', ' ').title()}: {value}")

    print("\nDone with Manager Analyzer tests.")