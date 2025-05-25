# H2H Comparator Engine
# This file will contain functions for comparing two managers head-to-head.

from typing import List, Dict, Any, Optional, Tuple, Set

from ..models.manager import ManagerProfile, ManagerGameweekPicks
from ..models.h2h_league import H2HLeague, H2HMatch
# from api.fpl_client import FPLAPIClient # For fetching fresh data if needed

def calculate_h2h_record(
    manager1_id: int,
    manager2_id: int,
    h2h_league: H2HLeague
) -> Dict[str, Any]:
    """Calculates the direct H2H record between two managers in a given H2H league."""
    manager1_wins = 0
    manager2_wins = 0
    draws = 0
    matches_played = 0
    manager1_points_total = 0
    manager2_points_total = 0

    for gw_matches in h2h_league.matches.values():
        for match in gw_matches:
            is_m1_entry1 = match.entry_1_entry == manager1_id
            is_m1_entry2 = match.entry_2_entry == manager1_id
            is_m2_entry1 = match.entry_1_entry == manager2_id
            is_m2_entry2 = match.entry_2_entry == manager2_id

            if (is_m1_entry1 and is_m2_entry2) or (is_m1_entry2 and is_m2_entry1):
                matches_played += 1
                m1_score = match.entry_1_points if is_m1_entry1 else match.entry_2_points
                m2_score = match.entry_1_points if is_m2_entry1 else match.entry_2_points
                
                manager1_points_total += m1_score
                manager2_points_total += m2_score

                if m1_score > m2_score:
                    manager1_wins += 1
                elif m2_score > m1_score:
                    manager2_wins += 1
                else:
                    draws += 1
    
    return {
        "manager1_id": manager1_id,
        "manager2_id": manager2_id,
        "matches_played": matches_played,
        "manager1_wins": manager1_wins,
        "manager2_wins": manager2_wins,
        "draws": draws,
        "manager1_total_fpl_points_in_h2h": manager1_points_total,
        "manager2_total_fpl_points_in_h2h": manager2_points_total,
        "manager1_avg_fpl_points_in_h2h": manager1_points_total / matches_played if matches_played > 0 else 0,
        "manager2_avg_fpl_points_in_h2h": manager2_points_total / matches_played if matches_played > 0 else 0,
    }

def identify_differentials(
    manager1_picks: ManagerGameweekPicks,
    manager2_picks: ManagerGameweekPicks,
    bootstrap_static_data: Dict[str, Any] # For player names
) -> Dict[str, Any]:
    """Identifies differential players between two managers for a specific gameweek."""
    if not bootstrap_static_data or 'elements' not in bootstrap_static_data:
        return {"error": "Bootstrap static data not available for differential analysis."}

    player_map = {p['id']: p for p in bootstrap_static_data['elements']}

    m1_player_ids: Set[int] = {pick.element for pick in manager1_picks.picks if pick.multiplier > 0} # Only starting XI
    m2_player_ids: Set[int] = {pick.element for pick in manager2_picks.picks if pick.multiplier > 0} # Only starting XI

    m1_captain = next((pick.element for pick in manager1_picks.picks if pick.is_captain), None)
    m2_captain = next((pick.element for pick in manager2_picks.picks if pick.is_captain), None)
    
    m1_vice_captain = next((pick.element for pick in manager1_picks.picks if pick.is_vice_captain), None)
    m2_vice_captain = next((pick.element for pick in manager2_picks.picks if pick.is_vice_captain), None)

    # Differentials are players in M1's team but not M2's, and vice-versa
    m1_diff_ids = m1_player_ids - m2_player_ids
    m2_diff_ids = m2_player_ids - m1_player_ids
    shared_player_ids = m1_player_ids.intersection(m2_player_ids)

    def get_player_details(player_id: int) -> Dict[str, Any]:
        player_data = player_map.get(player_id)
        if player_data:
            return {"id": player_id, "name": player_data.get('web_name', 'Unknown')}
        return {"id": player_id, "name": 'Unknown'}

    return {
        "manager1_differentials": [get_player_details(pid) for pid in m1_diff_ids],
        "manager2_differentials": [get_player_details(pid) for pid in m2_diff_ids],
        "shared_players": [get_player_details(pid) for pid in shared_player_ids],
        "manager1_captain": get_player_details(m1_captain) if m1_captain else None,
        "manager2_captain": get_player_details(m2_captain) if m2_captain else None,
        "captain_is_differential": m1_captain != m2_captain if m1_captain and m2_captain else True, # True if one has captain and other doesn't
        "manager1_vice_captain": get_player_details(m1_vice_captain) if m1_vice_captain else None,
        "manager2_vice_captain": get_player_details(m2_vice_captain) if m2_vice_captain else None,
    }

def calculate_momentum(manager_profile: ManagerProfile, h2h_league: H2HLeague, last_n_gws: int = 3) -> Dict[str, Any]:
    """
    Calculates momentum based on recent H2H results and FPL point scores.
    This is a placeholder and can be expanded significantly.
    """
    # H2H Momentum (wins in last N H2H games)
    h2h_wins_last_n = 0
    h2h_matches_considered = 0
    
    # Sort matches by gameweek descending to get recent ones
    all_manager_matches = sorted(
        h2h_league.get_matches_for_manager(manager_profile.id),
        key=lambda m: m.event,
        reverse=True
    )

    for match in all_manager_matches:
        if h2h_matches_considered >= last_n_gws:
            break
        if (match.entry_1_entry == manager_profile.id and match.entry_1_win) or \
           (match.entry_2_entry == manager_profile.id and match.entry_2_win):
            h2h_wins_last_n += 1
        h2h_matches_considered +=1

    # FPL Points Momentum (average points in last N GWs - already in manager_analyzer.calculate_form)
    from .manager_analyzer import calculate_form # Avoid circular import if possible, or pass as arg
    fpl_points_form = calculate_form(manager_profile, last_n_gws)

    return {
        "manager_id": manager_profile.id,
        "h2h_wins_last_n_gws": h2h_wins_last_n,
        "h2h_matches_considered_for_momentum": h2h_matches_considered,
        "fpl_points_form_last_n_gws": round(fpl_points_form, 2)
        # Could add rank change momentum, etc.
    }

# Example Usage (for testing purposes)
if __name__ == "__main__":
    from ..models.h2h_league import H2HLeagueEntry # For mock data
    from ..models.manager import GameweekPerformance, ManagerPick # For mock data

    # Mock H2HLeague data
    mock_league = H2HLeague(
        id=100, name="Test H2H Comp League", created="", closed=False, league_type='x', scoring='h2h', start_event=1
    )
    # GW1 Match: M1 (id=1) vs M2 (id=2)
    match1_gw1 = H2HMatch(id=1, event=1, league_id=100, entry_1_entry=1, entry_1_name="M1 Team", entry_1_player_name="M1", entry_1_points=70, entry_1_win=1, entry_1_draw=0, entry_1_loss=0, entry_2_entry=2, entry_2_name="M2 Team", entry_2_player_name="M2", entry_2_points=60, entry_2_win=0, entry_2_draw=0, entry_2_loss=1, is_knockout=False, winner=1)
    # GW2 Match: M1 (id=1) vs M3 (id=3)
    match2_gw2 = H2HMatch(id=2, event=2, league_id=100, entry_1_entry=1, entry_1_name="M1 Team", entry_1_player_name="M1", entry_1_points=50, entry_1_win=0, entry_1_draw=0, entry_1_loss=1, entry_2_entry=3, entry_2_name="M3 Team", entry_2_player_name="M3", entry_2_points=55, entry_2_win=1, entry_2_draw=0, entry_2_loss=0, is_knockout=False, winner=3)
    # GW3 Match: M2 (id=2) vs M1 (id=1)
    match3_gw3 = H2HMatch(id=3, event=3, league_id=100, entry_1_entry=2, entry_1_name="M2 Team", entry_1_player_name="M2", entry_1_points=80, entry_1_win=1, entry_1_draw=0, entry_1_loss=0, entry_2_entry=1, entry_2_name="M1 Team", entry_2_player_name="M1", entry_2_points=75, entry_2_win=0, entry_2_draw=0, entry_2_loss=1, is_knockout=False, winner=2)
    
    mock_league.matches = {1: [match1_gw1], 2: [match2_gw2], 3: [match3_gw3]}

    manager1_id_test = 1
    manager2_id_test = 2

    h2h_record = calculate_h2h_record(manager1_id_test, manager2_id_test, mock_league)
    print(f"H2H Record between Manager {manager1_id_test} and Manager {manager2_id_test}:")
    print(json.dumps(h2h_record, indent=2))

    # Mock ManagerGameweekPicks for differential analysis (GW3)
    # Assume M1 (id=1) and M2 (id=2) played in GW3
    mock_m1_gw3_perf = GameweekPerformance(event=3, points=75, total_points=0, rank=0, rank_sort=0, overall_rank=0, bank=0, value=0, event_transfers=0, event_transfers_cost=0, points_on_bench=0)
    mock_m2_gw3_perf = GameweekPerformance(event=3, points=80, total_points=0, rank=0, rank_sort=0, overall_rank=0, bank=0, value=0, event_transfers=0, event_transfers_cost=0, points_on_bench=0)

    m1_picks_gw3 = ManagerGameweekPicks(
        active_chip=None, automatic_subs=[], entry_history=mock_m1_gw3_perf,
        picks=[
            ManagerPick(element=101, position=1, multiplier=1, is_captain=False, is_vice_captain=False), # Salah
            ManagerPick(element=102, position=2, multiplier=2, is_captain=True, is_vice_captain=False),  # Haaland (C)
            ManagerPick(element=103, position=3, multiplier=1, is_captain=False, is_vice_captain=True), # Saka (VC)
            ManagerPick(element=104, position=4, multiplier=1, is_captain=False, is_vice_captain=False)  # Trippier
        ]
    )
    m2_picks_gw3 = ManagerGameweekPicks(
        active_chip=None, automatic_subs=[], entry_history=mock_m2_gw3_perf,
        picks=[
            ManagerPick(element=101, position=1, multiplier=1, is_captain=False, is_vice_captain=False), # Salah
            ManagerPick(element=202, position=2, multiplier=2, is_captain=True, is_vice_captain=False),  # Kane (C)
            ManagerPick(element=103, position=3, multiplier=1, is_captain=False, is_vice_captain=True), # Saka (VC)
            ManagerPick(element=204, position=4, multiplier=1, is_captain=False, is_vice_captain=False)  # Rashford
        ]
    )
    mock_bootstrap_data_diff = {
        "elements": [
            {"id": 101, "web_name": "Salah"}, {"id": 102, "web_name": "Haaland"}, 
            {"id": 103, "web_name": "Saka"}, {"id": 104, "web_name": "Trippier"},
            {"id": 202, "web_name": "Kane"}, {"id": 204, "web_name": "Rashford"}
        ]
    }
    import json # for pretty printing
    differentials = identify_differentials(m1_picks_gw3, m2_picks_gw3, mock_bootstrap_data_diff)
    print(f"\nDifferentials for GW3 between M1 and M2:")
    print(json.dumps(differentials, indent=2))

    # Mock ManagerProfile for momentum
    m1_profile = ManagerProfile(id=1, name="M1", team_name="M1 Team", started_event=1, current_gameweek_history=[
        GameweekPerformance(event=1, points=70, total_points=70, rank=0,rank_sort=0,overall_rank=0,bank=0,value=0,event_transfers=0,event_transfers_cost=0,points_on_bench=0),
        GameweekPerformance(event=2, points=50, total_points=120, rank=0,rank_sort=0,overall_rank=0,bank=0,value=0,event_transfers=0,event_transfers_cost=0,points_on_bench=0),
        GameweekPerformance(event=3, points=75, total_points=195, rank=0,rank_sort=0,overall_rank=0,bank=0,value=0,event_transfers=0,event_transfers_cost=0,points_on_bench=0)
    ])
    momentum_m1 = calculate_momentum(m1_profile, mock_league, last_n_gws=2)
    print(f"\nMomentum for Manager {m1_profile.id} (last 2 GWs):")
    print(json.dumps(momentum_m1, indent=2))

    print("\nDone with H2H Comparator tests.")