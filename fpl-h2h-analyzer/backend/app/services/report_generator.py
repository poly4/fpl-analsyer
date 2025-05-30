from typing import Dict, List, Optional, Any, Tuple
import json
import csv
from datetime import datetime
import logging
from pathlib import Path
import io

# Optional dependencies for PDF generation
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    logging.warning("reportlab not installed. PDF generation will be unavailable.")

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates comprehensive reports for H2H battles and league analysis.
    Supports multiple output formats: JSON, CSV, PDF.
    """
    
    def __init__(self, live_data_service, h2h_analyzer, enhanced_h2h_analyzer=None):
        """
        Initialize the report generator with required services.
        
        Args:
            live_data_service: Service for fetching FPL data
            h2h_analyzer: Core H2H analysis service
            enhanced_h2h_analyzer: Enhanced analytics service (optional)
        """
        self.live_data_service = live_data_service
        self.h2h_analyzer = h2h_analyzer
        self.enhanced_h2h_analyzer = enhanced_h2h_analyzer
        
        # Create reports directory if it doesn't exist
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
    
    async def generate_h2h_season_report(
        self,
        manager1_id: int,
        manager2_id: int,
        league_id: int,
        output_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive season report for H2H battles between two managers.
        
        Args:
            manager1_id: First manager ID
            manager2_id: Second manager ID
            league_id: H2H league ID
            output_format: Output format (json, csv, pdf)
            
        Returns:
            Dict containing report data and file path
        """
        logger.info(f"Generating H2H season report for managers {manager1_id} vs {manager2_id}")
        
        # Gather all season data
        report_data = await self._gather_season_data(manager1_id, manager2_id, league_id)
        
        # Generate report in requested format
        if output_format.lower() == "json":
            file_path = await self._generate_json_report(report_data, manager1_id, manager2_id)
        elif output_format.lower() == "csv":
            file_path = await self._generate_csv_report(report_data, manager1_id, manager2_id)
        elif output_format.lower() == "pdf":
            if not HAS_REPORTLAB:
                raise ValueError("PDF generation requires reportlab to be installed")
            file_path = await self._generate_pdf_report(report_data, manager1_id, manager2_id)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        return {
            "status": "success",
            "file_path": str(file_path),
            "format": output_format,
            "data": report_data
        }
    
    async def _gather_season_data(
        self,
        manager1_id: int,
        manager2_id: int,
        league_id: int
    ) -> Dict[str, Any]:
        """Gather all season data for the H2H report."""
        
        # Get manager information
        manager1_info = await self.live_data_service.get_manager_info(manager1_id)
        manager2_info = await self.live_data_service.get_manager_info(manager2_id)
        
        # Get all H2H matches between these managers
        all_matches = []
        h2h_record = {"manager1_wins": 0, "manager2_wins": 0, "draws": 0}
        
        # Fetch matches for all gameweeks in batches for better performance
        import asyncio
        
        async def fetch_gw_matches(gw):
            try:
                matches = await self.h2h_analyzer.get_h2h_matches(league_id, gw)
                return gw, matches
            except Exception as e:
                logger.warning(f"Error fetching matches for GW{gw}: {e}")
                return gw, []
        
        # Create tasks for all gameweeks and run them concurrently
        tasks = [fetch_gw_matches(gw) for gw in range(1, 39)]
        gw_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for gw_result in gw_results:
            if isinstance(gw_result, Exception):
                continue
                
            gw, matches = gw_result
            for match in matches:
                if self._is_match_between_managers(match, manager1_id, manager2_id):
                    all_matches.append(match)
                    # Update H2H record
                    if match.get('entry_1_entry') == manager1_id:
                        if match.get('entry_1_points', 0) > match.get('entry_2_points', 0):
                            h2h_record["manager1_wins"] += 1
                        elif match.get('entry_1_points', 0) < match.get('entry_2_points', 0):
                            h2h_record["manager2_wins"] += 1
                        else:
                            h2h_record["draws"] += 1
                    else:
                        if match.get('entry_2_points', 0) > match.get('entry_1_points', 0):
                            h2h_record["manager1_wins"] += 1
                        elif match.get('entry_2_points', 0) < match.get('entry_1_points', 0):
                            h2h_record["manager2_wins"] += 1
                        else:
                            h2h_record["draws"] += 1
        
        # Calculate statistics
        stats = self._calculate_season_statistics(all_matches, manager1_id, manager2_id)
        
        # Get key battles (biggest wins, closest matches)
        key_battles = self._identify_key_battles(all_matches, manager1_id, manager2_id)
        
        # Get form analysis
        form_analysis = self._analyze_form(all_matches, manager1_id, manager2_id)
        
        # If enhanced analyzer is available, get advanced analytics
        advanced_analytics = None
        if self.enhanced_h2h_analyzer:
            try:
                # Get analytics for the most recent match
                if all_matches:
                    latest_match = all_matches[-1]
                    latest_gw = latest_match.get('event', 38)
                    advanced_analytics = await self.enhanced_h2h_analyzer.analyze_battle_comprehensive(
                        manager1_id, manager2_id, latest_gw
                    )
            except Exception as e:
                logger.warning(f"Error getting advanced analytics: {e}")
        
        return {
            "managers": {
                "manager1": {
                    "id": manager1_id,
                    "name": manager1_info.get('name', ''),
                    "player_name": f"{manager1_info.get('player_first_name', '')} {manager1_info.get('player_last_name', '')}".strip()
                },
                "manager2": {
                    "id": manager2_id,
                    "name": manager2_info.get('name', ''),
                    "player_name": f"{manager2_info.get('player_first_name', '')} {manager2_info.get('player_last_name', '')}".strip()
                }
            },
            "h2h_record": h2h_record,
            "all_matches": all_matches,
            "statistics": stats,
            "key_battles": key_battles,
            "form_analysis": form_analysis,
            "advanced_analytics": advanced_analytics,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _is_match_between_managers(self, match: Dict[str, Any], manager1_id: int, manager2_id: int) -> bool:
        """Check if a match is between the two specified managers."""
        entry1 = match.get('entry_1_entry')
        entry2 = match.get('entry_2_entry')
        return (entry1 == manager1_id and entry2 == manager2_id) or \
               (entry1 == manager2_id and entry2 == manager1_id)
    
    def _calculate_season_statistics(
        self,
        matches: List[Dict[str, Any]],
        manager1_id: int,
        manager2_id: int
    ) -> Dict[str, Any]:
        """Calculate season statistics from all matches."""
        if not matches:
            return {}
        
        manager1_points = []
        manager2_points = []
        margins = []
        
        for match in matches:
            if match.get('entry_1_entry') == manager1_id:
                m1_pts = match.get('entry_1_points', 0)
                m2_pts = match.get('entry_2_points', 0)
            else:
                m1_pts = match.get('entry_2_points', 0)
                m2_pts = match.get('entry_1_points', 0)
            
            manager1_points.append(m1_pts)
            manager2_points.append(m2_pts)
            margins.append(m1_pts - m2_pts)
        
        return {
            "manager1": {
                "total_points": sum(manager1_points),
                "avg_points": sum(manager1_points) / len(manager1_points) if manager1_points else 0,
                "highest_score": max(manager1_points) if manager1_points else 0,
                "lowest_score": min(manager1_points) if manager1_points else 0
            },
            "manager2": {
                "total_points": sum(manager2_points),
                "avg_points": sum(manager2_points) / len(manager2_points) if manager2_points else 0,
                "highest_score": max(manager2_points) if manager2_points else 0,
                "lowest_score": min(manager2_points) if manager2_points else 0
            },
            "margins": {
                "avg_margin": sum(margins) / len(margins) if margins else 0,
                "biggest_win_margin": max(margins) if margins else 0,
                "biggest_loss_margin": min(margins) if margins else 0
            }
        }
    
    def _identify_key_battles(
        self,
        matches: List[Dict[str, Any]],
        manager1_id: int,
        manager2_id: int
    ) -> Dict[str, Any]:
        """Identify key battles from the season."""
        if not matches:
            return {}
        
        # Find biggest wins for each manager
        biggest_m1_win = None
        biggest_m2_win = None
        closest_match = None
        highest_scoring = None
        
        max_m1_margin = -999
        max_m2_margin = -999
        min_margin = 999
        max_total = 0
        
        for match in matches:
            if match.get('entry_1_entry') == manager1_id:
                m1_pts = match.get('entry_1_points', 0)
                m2_pts = match.get('entry_2_points', 0)
            else:
                m1_pts = match.get('entry_2_points', 0)
                m2_pts = match.get('entry_1_points', 0)
            
            margin = m1_pts - m2_pts
            total = m1_pts + m2_pts
            
            # Biggest manager1 win
            if margin > max_m1_margin:
                max_m1_margin = margin
                biggest_m1_win = match
            
            # Biggest manager2 win
            if margin < max_m2_margin:
                max_m2_margin = margin
                biggest_m2_win = match
            
            # Closest match
            if abs(margin) < abs(min_margin):
                min_margin = margin
                closest_match = match
            
            # Highest scoring
            if total > max_total:
                max_total = total
                highest_scoring = match
        
        return {
            "biggest_manager1_win": biggest_m1_win,
            "biggest_manager2_win": biggest_m2_win,
            "closest_match": closest_match,
            "highest_scoring_match": highest_scoring
        }
    
    def _analyze_form(
        self,
        matches: List[Dict[str, Any]],
        manager1_id: int,
        manager2_id: int
    ) -> Dict[str, Any]:
        """Analyze form trends throughout the season."""
        if not matches:
            return {}
        
        # Sort matches by gameweek
        sorted_matches = sorted(matches, key=lambda x: x.get('event', 0))
        
        # Calculate form streaks
        current_m1_streak = 0
        current_m2_streak = 0
        best_m1_streak = 0
        best_m2_streak = 0
        
        for match in sorted_matches:
            if match.get('entry_1_entry') == manager1_id:
                m1_pts = match.get('entry_1_points', 0)
                m2_pts = match.get('entry_2_points', 0)
            else:
                m1_pts = match.get('entry_2_points', 0)
                m2_pts = match.get('entry_1_points', 0)
            
            if m1_pts > m2_pts:
                current_m1_streak += 1
                current_m2_streak = 0
                best_m1_streak = max(best_m1_streak, current_m1_streak)
            elif m2_pts > m1_pts:
                current_m2_streak += 1
                current_m1_streak = 0
                best_m2_streak = max(best_m2_streak, current_m2_streak)
            else:
                # Draw doesn't break streaks
                pass
        
        # Last 5 matches form
        last_5_results = []
        for match in sorted_matches[-5:]:
            if match.get('entry_1_entry') == manager1_id:
                m1_pts = match.get('entry_1_points', 0)
                m2_pts = match.get('entry_2_points', 0)
            else:
                m1_pts = match.get('entry_2_points', 0)
                m2_pts = match.get('entry_1_points', 0)
            
            if m1_pts > m2_pts:
                last_5_results.append('W')
            elif m2_pts > m1_pts:
                last_5_results.append('L')
            else:
                last_5_results.append('D')
        
        return {
            "best_winning_streak": {
                "manager1": best_m1_streak,
                "manager2": best_m2_streak
            },
            "current_form": {
                "manager1": ''.join(last_5_results),
                "manager2": ''.join(['W' if r == 'L' else 'L' if r == 'W' else 'D' for r in last_5_results])
            }
        }
    
    async def _generate_json_report(
        self,
        data: Dict[str, Any],
        manager1_id: int,
        manager2_id: int
    ) -> Path:
        """Generate JSON report."""
        filename = f"h2h_report_{manager1_id}_vs_{manager2_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = self.reports_dir / filename
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Generated JSON report: {file_path}")
        return file_path
    
    async def _generate_csv_report(
        self,
        data: Dict[str, Any],
        manager1_id: int,
        manager2_id: int
    ) -> Path:
        """Generate CSV report with match history."""
        filename = f"h2h_report_{manager1_id}_vs_{manager2_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = self.reports_dir / filename
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Gameweek', 'Manager 1', 'Score 1', 'Manager 2', 'Score 2', 
                'Winner', 'Margin'
            ])
            
            # Match data
            for match in data.get('all_matches', []):
                gw = match.get('event', '')
                
                if match.get('entry_1_entry') == manager1_id:
                    m1_name = match.get('entry_1_name', '')
                    m1_score = match.get('entry_1_points', 0)
                    m2_name = match.get('entry_2_name', '')
                    m2_score = match.get('entry_2_points', 0)
                else:
                    m1_name = match.get('entry_2_name', '')
                    m1_score = match.get('entry_2_points', 0)
                    m2_name = match.get('entry_1_name', '')
                    m2_score = match.get('entry_1_points', 0)
                
                if m1_score > m2_score:
                    winner = m1_name
                elif m2_score > m1_score:
                    winner = m2_name
                else:
                    winner = 'Draw'
                
                margin = abs(m1_score - m2_score)
                
                writer.writerow([gw, m1_name, m1_score, m2_name, m2_score, winner, margin])
        
        logger.info(f"Generated CSV report: {file_path}")
        return file_path
    
    async def _generate_pdf_report(
        self,
        data: Dict[str, Any],
        manager1_id: int,
        manager2_id: int
    ) -> Path:
        """Generate PDF report with comprehensive analysis."""
        filename = f"h2h_report_{manager1_id}_vs_{manager2_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path = self.reports_dir / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(str(file_path), pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#38003c'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        manager1_name = data['managers']['manager1']['name']
        manager2_name = data['managers']['manager2']['name']
        
        story.append(Paragraph(f"H2H Season Report", title_style))
        story.append(Paragraph(f"{manager1_name} vs {manager2_name}", styles['Heading2']))
        story.append(Spacer(1, 0.5*inch))
        
        # H2H Record
        record = data['h2h_record']
        record_data = [
            ['H2H Record', 'Wins', 'Draws', 'Losses'],
            [manager1_name, str(record['manager1_wins']), str(record['draws']), str(record['manager2_wins'])],
            [manager2_name, str(record['manager2_wins']), str(record['draws']), str(record['manager1_wins'])]
        ]
        
        record_table = Table(record_data)
        record_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(record_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Season Statistics
        stats = data['statistics']
        if stats:
            story.append(Paragraph("Season Statistics", styles['Heading2']))
            
            stats_data = [
                ['Manager', 'Total Points', 'Avg Points', 'Highest', 'Lowest'],
                [
                    manager1_name,
                    str(stats['manager1']['total_points']),
                    f"{stats['manager1']['avg_points']:.1f}",
                    str(stats['manager1']['highest_score']),
                    str(stats['manager1']['lowest_score'])
                ],
                [
                    manager2_name,
                    str(stats['manager2']['total_points']),
                    f"{stats['manager2']['avg_points']:.1f}",
                    str(stats['manager2']['highest_score']),
                    str(stats['manager2']['lowest_score'])
                ]
            ]
            
            stats_table = Table(stats_data)
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(stats_table)
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"Generated PDF report: {file_path}")
        return file_path
    
    async def generate_league_report(
        self,
        league_id: int,
        output_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive league report.
        
        Args:
            league_id: H2H league ID
            output_format: Output format (json, csv, pdf)
            
        Returns:
            Dict containing report data and file path
        """
        logger.info(f"Generating league report for league {league_id}")
        
        # Get league standings
        standings = await self.h2h_analyzer.get_h2h_standings(league_id)
        
        # Get all matches for the season
        all_matches = []
        for gw in range(1, 39):
            try:
                matches = await self.h2h_analyzer.get_h2h_matches(league_id, gw)
                all_matches.extend(matches)
            except Exception as e:
                logger.warning(f"Error fetching matches for GW{gw}: {e}")
        
        report_data = {
            "league_id": league_id,
            "standings": standings,
            "total_matches": len(all_matches),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Generate report in requested format
        if output_format.lower() == "json":
            filename = f"league_report_{league_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            file_path = self.reports_dir / filename
            
            with open(file_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
        else:
            raise ValueError(f"League reports currently only support JSON format")
        
        return {
            "status": "success",
            "file_path": str(file_path),
            "format": output_format,
            "data": report_data
        }