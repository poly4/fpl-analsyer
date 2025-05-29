// Modern UI Components - 2025 Design System
// Glassmorphism-based components with animations and advanced interactions

// Base Components
export { default as GlassCard } from './GlassCard';
export { 
  GlassContainer, 
  GlassButton, 
  GlassModal, 
  GlassStatus, 
  MinimalCard, 
  ElevatedCard 
} from './GlassCard';

// Data Display Components
export { default as AnimatedNumber } from './AnimatedNumber';
export { 
  ScoreCounter, 
  PointsDisplay, 
  RankDisplay, 
  PercentageDisplay, 
  CompactNumber, 
  LiveScore 
} from './AnimatedNumber';

export { default as StatBox } from './StatBox';
export { 
  ScoreBox, 
  RankBox, 
  PointsBox, 
  WinRateBox, 
  LiveStatBox 
} from './StatBox';

export { default as ModernTable } from './ModernTable';
export { 
  LeagueTable, 
  H2HTable, 
  PlayerTable 
} from './ModernTable';

// Layout Components
export { default as BentoGrid } from './BentoGrid';
export { 
  BentoItem, 
  HeroCard, 
  CompactGrid 
} from './BentoGrid';

// Visual Indicators
export { 
  PerformanceBadge,
  BadgeCollection,
  PerformanceIndicator,
  BADGE_CONFIGS
} from './PerformanceBadges';

// Manager Components
export { default as ManagerCard } from './ManagerCard';

// Re-export themes for convenience
export { 
  glassMixins, 
  animations, 
  colors, 
  typography,
  createModernTheme 
} from '../../styles/themes';