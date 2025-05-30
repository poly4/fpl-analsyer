/**
 * TypeScript interfaces for React components and their props
 */

import { ReactNode, ComponentPropsWithoutRef } from 'react';
import { Manager, ManagerHistory, ManagerPicks, H2HMatch, Player, Team } from './fpl-api';

// Base component props
export interface BaseComponentProps {
  className?: string;
  children?: ReactNode;
  testId?: string;
}

// Loading and error states
export interface AsyncComponentState {
  loading: boolean;
  error: Error | null;
  data: any;
}

export interface LoadingProps extends BaseComponentProps {
  size?: 'small' | 'medium' | 'large';
  variant?: 'spinner' | 'skeleton' | 'pulse';
  text?: string;
}

export interface ErrorBoundaryProps extends BaseComponentProps {
  fallback?: ComponentType<ErrorFallbackProps>;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  isolate?: boolean;
}

export interface ErrorFallbackProps {
  error: Error;
  resetError: () => void;
  retry?: () => void;
}

// Manager-related component props
export interface ManagerProfileProps extends BaseComponentProps {
  managerId: number;
  isOpen: boolean;
  onClose: () => void;
  manager?: Manager;
  history?: ManagerHistory;
}

export interface ManagerCardProps extends BaseComponentProps {
  manager: Manager;
  onClick?: (managerId: number) => void;
  showRank?: boolean;
  showTeam?: boolean;
  size?: 'small' | 'medium' | 'large';
}

export interface ManagerSelectorProps extends BaseComponentProps {
  managers: Manager[];
  selectedManager?: Manager;
  onSelect: (manager: Manager) => void;
  placeholder?: string;
  searchable?: boolean;
  disabled?: boolean;
}

// Gameweek-related component props
export interface GameweekDetailProps extends BaseComponentProps {
  gameweek: number;
  manager1Id: number;
  manager2Id: number;
  isOpen: boolean;
  onClose: () => void;
  picks1?: ManagerPicks;
  picks2?: ManagerPicks;
}

export interface GameweekCardProps extends BaseComponentProps {
  gameweek: number;
  manager1Points: number;
  manager2Points: number;
  onClick?: (gameweek: number) => void;
  winner?: 'manager1' | 'manager2' | 'draw';
  chipUsed?: string | null;
}

// Battle and comparison component props
export interface BattleCardProps extends BaseComponentProps {
  match: H2HMatch;
  onManagerClick?: (managerId: number) => void;
  onGameweekClick?: (gameweek: number, manager1Id: number, manager2Id: number) => void;
  showHistory?: boolean;
  compact?: boolean;
}

export interface ManagerComparisonProps extends BaseComponentProps {
  manager1: Manager;
  manager2: Manager;
  history1?: ManagerHistory;
  history2?: ManagerHistory;
  showPrediction?: boolean;
}

// Analytics component props
export interface AnalyticsProps extends BaseComponentProps {
  manager1Id?: number;
  manager2Id?: number;
  timeframe?: 'season' | 'recent' | 'all';
  metrics?: string[];
}

export interface ChipStrategyProps extends BaseComponentProps {
  managerId: number;
  chipData?: any;
  recommendations?: any;
}

export interface DifferentialImpactProps extends BaseComponentProps {
  manager1Id: number;
  manager2Id: number;
  gameweek?: number;
  data?: any;
}

export interface HistoricalPatternsProps extends BaseComponentProps {
  manager1Id: number;
  manager2Id: number;
  data?: any;
}

export interface TransferROIProps extends BaseComponentProps {
  managerId: number;
  transfers?: any[];
  roi?: any;
}

// Table and list component props
export interface LeagueTableProps extends BaseComponentProps {
  standings: any[];
  onManagerClick?: (managerId: number) => void;
  sortable?: boolean;
  searchable?: boolean;
  pageSize?: number;
}

export interface VirtualizedListProps<T> extends BaseComponentProps {
  items: T[];
  itemHeight: number;
  renderItem: (item: T, index: number) => ReactNode;
  containerHeight: number;
  overscan?: number;
}

// Chart and visualization props
export interface ChartProps extends BaseComponentProps {
  data: any[];
  type: 'line' | 'bar' | 'area' | 'pie' | 'scatter';
  xKey: string;
  yKey: string;
  title?: string;
  height?: number;
  width?: number;
  colors?: string[];
  interactive?: boolean;
  loading?: boolean;
}

export interface PlayerVisualizationProps extends BaseComponentProps {
  players: Player[];
  teams: Team[];
  formation?: string;
  highlights?: number[];
  onClick?: (playerId: number) => void;
}

// Form and input props
export interface SearchInputProps extends ComponentPropsWithoutRef<'input'> {
  onSearch: (query: string) => void;
  debounceMs?: number;
  suggestions?: string[];
  loading?: boolean;
  clearable?: boolean;
}

export interface FilterProps extends BaseComponentProps {
  filters: FilterOption[];
  activeFilters: string[];
  onFilterChange: (filters: string[]) => void;
  multiSelect?: boolean;
}

export interface FilterOption {
  id: string;
  label: string;
  value: any;
  count?: number;
}

// Modal and overlay props
export interface ModalProps extends BaseComponentProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: 'small' | 'medium' | 'large' | 'fullscreen';
  closable?: boolean;
  overlay?: boolean;
  animation?: 'fade' | 'slide' | 'scale';
}

export interface DrawerProps extends BaseComponentProps {
  isOpen: boolean;
  onClose: () => void;
  side?: 'left' | 'right' | 'top' | 'bottom';
  title?: string;
  closable?: boolean;
}

export interface TooltipProps extends BaseComponentProps {
  content: ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  trigger?: 'hover' | 'click' | 'focus';
  delay?: number;
}

// Navigation and layout props
export interface TabsProps extends BaseComponentProps {
  tabs: TabOption[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
  variant?: 'default' | 'pills' | 'underline';
}

export interface TabOption {
  id: string;
  label: string;
  content?: ReactNode;
  disabled?: boolean;
  badge?: string | number;
}

export interface BreadcrumbProps extends BaseComponentProps {
  items: BreadcrumbItem[];
  separator?: ReactNode;
}

export interface BreadcrumbItem {
  label: string;
  href?: string;
  onClick?: () => void;
  current?: boolean;
}

// Theme and styling props
export interface ThemeProviderProps extends BaseComponentProps {
  theme: Theme;
  defaultTheme?: 'light' | 'dark' | 'auto';
}

export interface Theme {
  colors: {
    primary: string;
    secondary: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    success: string;
    warning: string;
    error: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  typography: {
    fontFamily: string;
    fontSize: {
      xs: string;
      sm: string;
      md: string;
      lg: string;
      xl: string;
    };
    fontWeight: {
      normal: number;
      medium: number;
      bold: number;
    };
  };
  breakpoints: {
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  shadows: {
    sm: string;
    md: string;
    lg: string;
  };
  borderRadius: {
    sm: string;
    md: string;
    lg: string;
  };
}

// API and data fetching props
export interface APIHookOptions {
  enabled?: boolean;
  cacheKey?: string;
  cacheTTL?: number;
  retryCount?: number;
  retryDelay?: number;
  debounceMs?: number;
  onSuccess?: (data: any) => void;
  onError?: (error: Error) => void;
}

export interface PaginationOptions {
  page: number;
  pageSize: number;
  totalItems?: number;
  totalPages?: number;
}

export interface SortOptions {
  field: string;
  direction: 'asc' | 'desc';
}

// Performance monitoring props
export interface PerformanceMetrics {
  renderTime: number;
  componentName: string;
  propsSize: number;
  childrenCount: number;
  reRenderCount: number;
}

export interface PerformanceMonitorProps extends BaseComponentProps {
  trackRenders?: boolean;
  trackProps?: boolean;
  warnThreshold?: number;
  onMetrics?: (metrics: PerformanceMetrics) => void;
}

// Accessibility props
export interface A11yProps {
  'aria-label'?: string;
  'aria-labelledby'?: string;
  'aria-describedby'?: string;
  'aria-expanded'?: boolean;
  'aria-hidden'?: boolean;
  'aria-live'?: 'polite' | 'assertive' | 'off';
  role?: string;
  tabIndex?: number;
}

// Animation and transition props
export interface AnimationProps {
  animate?: boolean;
  duration?: number;
  delay?: number;
  easing?: string;
  onAnimationStart?: () => void;
  onAnimationEnd?: () => void;
}

export interface TransitionProps extends AnimationProps {
  show: boolean;
  appear?: boolean;
  enter?: string;
  enterActive?: string;
  exit?: string;
  exitActive?: string;
}

// Utility types
export type Size = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
export type Variant = 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
export type Position = 'top' | 'bottom' | 'left' | 'right';
export type Alignment = 'start' | 'center' | 'end';

// Component composition types
export interface ComposableComponent<T = {}> extends BaseComponentProps {
  as?: keyof JSX.IntrinsicElements | ComponentType<any>;
  forwardedRef?: Ref<any>;
}

// Export utility type helpers
export type WithOptional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type WithRequired<T, K extends keyof T> = T & Required<Pick<T, K>>;

// Event handler types
export type ClickHandler = (event: MouseEvent) => void;
export type ChangeHandler<T = any> = (value: T) => void;
export type SubmitHandler<T = any> = (data: T) => void;
export type KeyboardHandler = (event: KeyboardEvent) => void;