-- FPL H2H Analyzer Database Schema
-- Optimized for performance with indexing, partitioning, and materialized views

-- Create database extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Teams table
CREATE TABLE teams (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(10) NOT NULL,
    strength_overall_home INTEGER,
    strength_overall_away INTEGER,
    strength_attack_home INTEGER,
    strength_attack_away INTEGER,
    strength_defence_home INTEGER,
    strength_defence_away INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for team lookups
CREATE INDEX idx_teams_name ON teams USING gin(name gin_trgm_ops);

-- Players table with partitioning by season
CREATE TABLE players (
    id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    first_name VARCHAR(100),
    second_name VARCHAR(100),
    web_name VARCHAR(50),
    team_id INTEGER REFERENCES teams(id),
    element_type INTEGER, -- 1=GK, 2=DEF, 3=MID, 4=FWD
    now_cost INTEGER,
    total_points INTEGER DEFAULT 0,
    points_per_game DECIMAL(4,2) DEFAULT 0,
    selected_by_percent DECIMAL(5,2) DEFAULT 0,
    form DECIMAL(3,1) DEFAULT 0,
    minutes INTEGER DEFAULT 0,
    goals_scored INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    clean_sheets INTEGER DEFAULT 0,
    goals_conceded INTEGER DEFAULT 0,
    own_goals INTEGER DEFAULT 0,
    penalties_saved INTEGER DEFAULT 0,
    penalties_missed INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    bonus INTEGER DEFAULT 0,
    bps INTEGER DEFAULT 0,
    influence DECIMAL(6,1) DEFAULT 0,
    creativity DECIMAL(6,1) DEFAULT 0,
    threat DECIMAL(6,1) DEFAULT 0,
    ict_index DECIMAL(5,1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, season)
) PARTITION BY RANGE (season);

-- Create partitions for different seasons
CREATE TABLE players_2023 PARTITION OF players FOR VALUES FROM (2023) TO (2024);
CREATE TABLE players_2024 PARTITION OF players FOR VALUES FROM (2024) TO (2025);
CREATE TABLE players_2025 PARTITION OF players FOR VALUES FROM (2025) TO (2026);

-- Indexes for players table
CREATE INDEX idx_players_team_id ON players (team_id, season);
CREATE INDEX idx_players_element_type ON players (element_type, season);
CREATE INDEX idx_players_form ON players (form DESC, season);
CREATE INDEX idx_players_total_points ON players (total_points DESC, season);
CREATE INDEX idx_players_web_name ON players USING gin(web_name gin_trgm_ops);
CREATE INDEX idx_players_updated_at ON players (updated_at);

-- Gameweeks table
CREATE TABLE gameweeks (
    id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    name VARCHAR(50),
    deadline_time TIMESTAMP,
    average_entry_score INTEGER,
    finished BOOLEAN DEFAULT FALSE,
    data_checked BOOLEAN DEFAULT FALSE,
    highest_scoring_entry INTEGER,
    highest_score INTEGER,
    is_previous BOOLEAN DEFAULT FALSE,
    is_current BOOLEAN DEFAULT FALSE,
    is_next BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, season)
) PARTITION BY RANGE (season);

-- Create gameweek partitions
CREATE TABLE gameweeks_2023 PARTITION OF gameweeks FOR VALUES FROM (2023) TO (2024);
CREATE TABLE gameweeks_2024 PARTITION OF gameweeks FOR VALUES FROM (2024) TO (2025);
CREATE TABLE gameweeks_2025 PARTITION OF gameweeks FOR VALUES FROM (2025) TO (2026);

-- Indexes for gameweeks
CREATE INDEX idx_gameweeks_deadline ON gameweeks (deadline_time, season);
CREATE INDEX idx_gameweeks_current ON gameweeks (is_current, season) WHERE is_current = TRUE;
CREATE INDEX idx_gameweeks_finished ON gameweeks (finished, season);

-- Fixtures table with partitioning
CREATE TABLE fixtures (
    id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    gameweek_id INTEGER NOT NULL,
    team_h INTEGER REFERENCES teams(id),
    team_a INTEGER REFERENCES teams(id),
    team_h_score INTEGER,
    team_a_score INTEGER,
    team_h_difficulty INTEGER,
    team_a_difficulty INTEGER,
    kickoff_time TIMESTAMP,
    started BOOLEAN DEFAULT FALSE,
    finished BOOLEAN DEFAULT FALSE,
    finished_provisional BOOLEAN DEFAULT FALSE,
    minutes INTEGER DEFAULT 0,
    provisional_start_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, season)
) PARTITION BY RANGE (season);

-- Create fixture partitions
CREATE TABLE fixtures_2023 PARTITION OF fixtures FOR VALUES FROM (2023) TO (2024);
CREATE TABLE fixtures_2024 PARTITION OF fixtures FOR VALUES FROM (2024) TO (2025);
CREATE TABLE fixtures_2025 PARTITION OF fixtures FOR VALUES FROM (2025) TO (2026);

-- Indexes for fixtures
CREATE INDEX idx_fixtures_gameweek ON fixtures (gameweek_id, season);
CREATE INDEX idx_fixtures_teams ON fixtures (team_h, team_a, season);
CREATE INDEX idx_fixtures_kickoff ON fixtures (kickoff_time, season);
CREATE INDEX idx_fixtures_started ON fixtures (started, season) WHERE started = TRUE;
CREATE INDEX idx_fixtures_finished ON fixtures (finished, season);

-- Managers table
CREATE TABLE managers (
    id INTEGER PRIMARY KEY,
    player_first_name VARCHAR(100),
    player_last_name VARCHAR(100),
    player_region_name VARCHAR(100),
    player_region_id INTEGER,
    player_region_iso_code_short VARCHAR(10),
    summary_overall_points INTEGER DEFAULT 0,
    summary_overall_rank INTEGER,
    summary_event_points INTEGER DEFAULT 0,
    summary_event_rank INTEGER,
    current_event INTEGER,
    favourite_team INTEGER REFERENCES teams(id),
    started_event INTEGER,
    last_deadline_bank INTEGER DEFAULT 1000,
    last_deadline_value INTEGER DEFAULT 1000,
    last_deadline_total_transfers INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for managers
CREATE INDEX idx_managers_overall_rank ON managers (summary_overall_rank);
CREATE INDEX idx_managers_name ON managers USING gin((player_first_name || ' ' || player_last_name) gin_trgm_ops);
CREATE INDEX idx_managers_updated_at ON managers (updated_at);

-- Manager picks table with partitioning
CREATE TABLE manager_picks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    manager_id INTEGER NOT NULL,
    gameweek_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    multiplier INTEGER DEFAULT 1, -- 0=bench, 1=playing, 2=captain, 3=triple_captain
    is_captain BOOLEAN DEFAULT FALSE,
    is_vice_captain BOOLEAN DEFAULT FALSE,
    event_points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (season);

-- Create manager picks partitions
CREATE TABLE manager_picks_2023 PARTITION OF manager_picks FOR VALUES FROM (2023) TO (2024);
CREATE TABLE manager_picks_2024 PARTITION OF manager_picks FOR VALUES FROM (2024) TO (2025);
CREATE TABLE manager_picks_2025 PARTITION OF manager_picks FOR VALUES FROM (2025) TO (2026);

-- Indexes for manager picks
CREATE INDEX idx_manager_picks_manager_gw ON manager_picks (manager_id, gameweek_id, season);
CREATE INDEX idx_manager_picks_player ON manager_picks (player_id, season);
CREATE INDEX idx_manager_picks_captain ON manager_picks (is_captain, season) WHERE is_captain = TRUE;
CREATE INDEX idx_manager_picks_multiplier ON manager_picks (multiplier, season);

-- H2H leagues table
CREATE TABLE h2h_leagues (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200),
    created_by INTEGER REFERENCES managers(id),
    start_event INTEGER,
    league_type VARCHAR(20) DEFAULT 'h2h',
    scoring VARCHAR(20) DEFAULT 'h',
    admin_entry INTEGER,
    closed BOOLEAN DEFAULT FALSE,
    max_entries INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for H2H leagues
CREATE INDEX idx_h2h_leagues_created_by ON h2h_leagues (created_by);
CREATE INDEX idx_h2h_leagues_name ON h2h_leagues USING gin(name gin_trgm_ops);

-- H2H league entries
CREATE TABLE h2h_league_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    league_id INTEGER REFERENCES h2h_leagues(id) ON DELETE CASCADE,
    manager_id INTEGER REFERENCES managers(id),
    entry_id INTEGER,
    entry_name VARCHAR(200),
    player_first_name VARCHAR(100),
    player_last_name VARCHAR(100),
    waiver_pick INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(league_id, manager_id)
);

-- Indexes for H2H league entries
CREATE INDEX idx_h2h_entries_league ON h2h_league_entries (league_id);
CREATE INDEX idx_h2h_entries_manager ON h2h_league_entries (manager_id);

-- H2H matches table with partitioning
CREATE TABLE h2h_matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    league_id INTEGER NOT NULL,
    gameweek_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    manager1_id INTEGER NOT NULL,
    manager2_id INTEGER NOT NULL,
    manager1_points INTEGER DEFAULT 0,
    manager2_points INTEGER DEFAULT 0,
    finished BOOLEAN DEFAULT FALSE,
    started BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (season);

-- Create H2H matches partitions
CREATE TABLE h2h_matches_2023 PARTITION OF h2h_matches FOR VALUES FROM (2023) TO (2024);
CREATE TABLE h2h_matches_2024 PARTITION OF h2h_matches FOR VALUES FROM (2024) TO (2025);
CREATE TABLE h2h_matches_2025 PARTITION OF h2h_matches FOR VALUES FROM (2025) TO (2026);

-- Indexes for H2H matches
CREATE INDEX idx_h2h_matches_league_gw ON h2h_matches (league_id, gameweek_id, season);
CREATE INDEX idx_h2h_matches_managers ON h2h_matches (manager1_id, manager2_id, season);
CREATE INDEX idx_h2h_matches_finished ON h2h_matches (finished, season);
CREATE INDEX idx_h2h_matches_gameweek ON h2h_matches (gameweek_id, season);

-- Player statistics table with partitioning
CREATE TABLE player_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id INTEGER NOT NULL,
    gameweek_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    fixture_id INTEGER,
    minutes INTEGER DEFAULT 0,
    goals_scored INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    clean_sheets INTEGER DEFAULT 0,
    goals_conceded INTEGER DEFAULT 0,
    own_goals INTEGER DEFAULT 0,
    penalties_saved INTEGER DEFAULT 0,
    penalties_missed INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    bonus INTEGER DEFAULT 0,
    bps INTEGER DEFAULT 0,
    influence DECIMAL(6,1) DEFAULT 0,
    creativity DECIMAL(6,1) DEFAULT 0,
    threat DECIMAL(6,1) DEFAULT 0,
    ict_index DECIMAL(5,1) DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    in_dreamteam BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (season);

-- Create player stats partitions
CREATE TABLE player_stats_2023 PARTITION OF player_stats FOR VALUES FROM (2023) TO (2024);
CREATE TABLE player_stats_2024 PARTITION OF player_stats FOR VALUES FROM (2024) TO (2025);
CREATE TABLE player_stats_2025 PARTITION OF player_stats FOR VALUES FROM (2025) TO (2026);

-- Indexes for player stats
CREATE INDEX idx_player_stats_player_gw ON player_stats (player_id, gameweek_id, season);
CREATE INDEX idx_player_stats_gameweek ON player_stats (gameweek_id, season);
CREATE INDEX idx_player_stats_points ON player_stats (total_points DESC, season);
CREATE INDEX idx_player_stats_bonus ON player_stats (bonus DESC, season) WHERE bonus > 0;
CREATE INDEX idx_player_stats_goals ON player_stats (goals_scored DESC, season) WHERE goals_scored > 0;

-- Cache table for expensive queries
CREATE TABLE query_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    data JSONB NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for cache expiration cleanup
CREATE INDEX idx_query_cache_expires ON query_cache (expires_at);

-- Materialized views for analytics

-- Player performance summary view
CREATE MATERIALIZED VIEW player_performance_summary AS
SELECT 
    p.id,
    p.season,
    p.web_name,
    p.team_id,
    p.element_type,
    p.total_points,
    p.points_per_game,
    p.form,
    COUNT(ps.id) as games_played,
    AVG(ps.total_points) as avg_points_per_game,
    SUM(ps.minutes) as total_minutes,
    SUM(ps.goals_scored) as total_goals,
    SUM(ps.assists) as total_assists,
    SUM(ps.clean_sheets) as total_clean_sheets,
    SUM(ps.bonus) as total_bonus,
    ROUND(AVG(ps.bps), 1) as avg_bps,
    COUNT(CASE WHEN ps.total_points >= 10 THEN 1 END) as double_digit_hauls,
    COUNT(CASE WHEN ps.total_points <= 2 THEN 1 END) as blanks
FROM players p
LEFT JOIN player_stats ps ON p.id = ps.player_id AND p.season = ps.season
WHERE p.season = EXTRACT(YEAR FROM CURRENT_DATE)
GROUP BY p.id, p.season, p.web_name, p.team_id, p.element_type, p.total_points, p.points_per_game, p.form;

-- Index for player performance summary
CREATE INDEX idx_player_perf_summary_points ON player_performance_summary (total_points DESC);
CREATE INDEX idx_player_perf_summary_form ON player_performance_summary (form DESC);
CREATE INDEX idx_player_perf_summary_team ON player_performance_summary (team_id);

-- H2H head-to-head records view
CREATE MATERIALIZED VIEW h2h_head_to_head_records AS
SELECT 
    m.manager1_id,
    m.manager2_id,
    m.league_id,
    m.season,
    COUNT(*) as total_matches,
    COUNT(CASE WHEN m.manager1_points > m.manager2_points THEN 1 END) as manager1_wins,
    COUNT(CASE WHEN m.manager2_points > m.manager1_points THEN 1 END) as manager2_wins,
    COUNT(CASE WHEN m.manager1_points = m.manager2_points THEN 1 END) as draws,
    AVG(m.manager1_points) as manager1_avg_points,
    AVG(m.manager2_points) as manager2_avg_points,
    AVG(ABS(m.manager1_points - m.manager2_points)) as avg_margin,
    MAX(ABS(m.manager1_points - m.manager2_points)) as biggest_margin
FROM h2h_matches m
WHERE m.finished = TRUE
GROUP BY m.manager1_id, m.manager2_id, m.league_id, m.season;

-- Index for H2H records
CREATE INDEX idx_h2h_records_managers ON h2h_head_to_head_records (manager1_id, manager2_id);
CREATE INDEX idx_h2h_records_league ON h2h_head_to_head_records (league_id, season);

-- Team strength analysis view
CREATE MATERIALIZED VIEW team_strength_analysis AS
SELECT 
    t.id,
    t.name,
    t.short_name,
    COUNT(DISTINCT f.id) as fixtures_played,
    AVG(CASE WHEN f.team_h = t.id THEN f.team_h_score ELSE f.team_a_score END) as avg_goals_scored,
    AVG(CASE WHEN f.team_h = t.id THEN f.team_a_score ELSE f.team_h_score END) as avg_goals_conceded,
    COUNT(CASE WHEN (f.team_h = t.id AND f.team_h_score > f.team_a_score) 
                 OR (f.team_a = t.id AND f.team_a_score > f.team_h_score) THEN 1 END) as wins,
    COUNT(CASE WHEN f.team_h_score = f.team_a_score THEN 1 END) as draws,
    COUNT(CASE WHEN (f.team_h = t.id AND f.team_h_score < f.team_a_score) 
                 OR (f.team_a = t.id AND f.team_a_score < f.team_h_score) THEN 1 END) as losses,
    COUNT(CASE WHEN (f.team_h = t.id AND f.team_a_score = 0) 
                 OR (f.team_a = t.id AND f.team_h_score = 0) THEN 1 END) as clean_sheets
FROM teams t
LEFT JOIN fixtures f ON (f.team_h = t.id OR f.team_a = t.id) 
                    AND f.finished = TRUE 
                    AND f.season = EXTRACT(YEAR FROM CURRENT_DATE)
GROUP BY t.id, t.name, t.short_name;

-- Index for team strength
CREATE INDEX idx_team_strength_goals ON team_strength_analysis (avg_goals_scored DESC);
CREATE INDEX idx_team_strength_conceded ON team_strength_analysis (avg_goals_conceded ASC);

-- Functions for automatic updates

-- Function to update materialized views
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY player_performance_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY h2h_head_to_head_records;
    REFRESH MATERIALIZED VIEW CONCURRENTLY team_strength_analysis;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM query_cache WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Function to update player updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at columns
CREATE TRIGGER update_players_updated_at BEFORE UPDATE ON players
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_managers_updated_at BEFORE UPDATE ON managers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_h2h_matches_updated_at BEFORE UPDATE ON h2h_matches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_manager_picks_updated_at BEFORE UPDATE ON manager_picks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_player_stats_updated_at BEFORE UPDATE ON player_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create indexes for full-text search
CREATE INDEX idx_players_fulltext ON players USING gin(to_tsvector('english', web_name || ' ' || first_name || ' ' || second_name));
CREATE INDEX idx_managers_fulltext ON managers USING gin(to_tsvector('english', player_first_name || ' ' || player_last_name));

-- Connection pooling configuration (to be set in postgresql.conf)
-- max_connections = 200
-- shared_buffers = 256MB
-- effective_cache_size = 1GB
-- work_mem = 4MB
-- maintenance_work_mem = 64MB
-- checkpoint_completion_target = 0.9
-- wal_buffers = 16MB
-- default_statistics_target = 100
-- random_page_cost = 1.1
-- effective_io_concurrency = 200

-- Query performance monitoring
CREATE VIEW slow_queries AS
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 20;

-- Indexes usage monitoring
CREATE VIEW unused_indexes AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE idx_tup_read = 0 AND idx_tup_fetch = 0
ORDER BY pg_relation_size(indexrelid) DESC;

-- Table sizes monitoring
CREATE VIEW table_sizes AS
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;