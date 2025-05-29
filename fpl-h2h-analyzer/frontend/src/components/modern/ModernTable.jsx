import React, { useState, useMemo } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Box,
  Typography,
  Chip,
  Avatar,
  IconButton,
  Tooltip,
  Collapse,
  useTheme,
  alpha
} from '@mui/material';
import {
  ExpandMore,
  ExpandLess,
  TrendingUp,
  TrendingDown,
  Remove
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import GlassCard from './GlassCard';
import AnimatedNumber from './AnimatedNumber';
import { glassMixins, animations } from '../../styles/themes';

/**
 * ModernTable - Enhanced data table with glassmorphism and animations
 * Features: sorting, expansion, hover effects, responsive design
 */
const ModernTable = ({
  data = [],
  columns = [],
  title,
  subtitle,
  sortable = true,
  expandable = false,
  hoverable = true,
  striped = false,
  compact = false,
  loading = false,
  emptyMessage = "No data available",
  maxHeight,
  stickyHeader = false,
  variant = 'glass',
  animate = true,
  onRowClick,
  onSort,
  renderExpandedRow,
  className = '',
  sx = {},
  ...props
}) => {
  const theme = useTheme();
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [expandedRows, setExpandedRows] = useState(new Set());

  // Handle sorting
  const handleSort = (columnKey) => {
    if (!sortable) return;
    
    let direction = 'asc';
    if (sortConfig.key === columnKey && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    
    const newConfig = { key: columnKey, direction };
    setSortConfig(newConfig);
    
    if (onSort) {
      onSort(newConfig);
    }
  };

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortConfig.key || !sortable) return data;
    
    return [...data].sort((a, b) => {
      const aVal = a[sortConfig.key];
      const bVal = b[sortConfig.key];
      
      if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [data, sortConfig, sortable]);

  // Handle row expansion
  const toggleRowExpansion = (rowId) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(rowId)) {
      newExpanded.delete(rowId);
    } else {
      newExpanded.add(rowId);
    }
    setExpandedRows(newExpanded);
  };

  // Table variants
  const tableVariants = {
    glass: {
      background: 'rgba(255, 255, 255, 0.03)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      borderRadius: '16px',
      overflow: 'hidden',
    },
    minimal: {
      background: 'rgba(255, 255, 255, 0.01)',
      border: '1px solid rgba(255, 255, 255, 0.05)',
      borderRadius: '12px',
      overflow: 'hidden',
    },
    elevated: {
      background: 'rgba(255, 255, 255, 0.05)',
      backdropFilter: 'blur(15px)',
      WebkitBackdropFilter: 'blur(15px)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      borderRadius: '20px',
      boxShadow: '0 12px 40px rgba(31, 38, 135, 0.2)',
      overflow: 'hidden',
    }
  };

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05
      }
    }
  };

  const rowVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: { 
      opacity: 1, 
      x: 0,
      transition: {
        duration: 0.3,
        ease: animations.easing.easeOut
      }
    }
  };

  // Render cell content with formatting
  const renderCellContent = (value, column) => {
    if (column.render) {
      return column.render(value);
    }

    switch (column.type) {
      case 'number':
        return (
          <AnimatedNumber 
            value={value}
            decimals={column.decimals || 0}
            format={column.format || 'number'}
            animate={false}
          />
        );
      
      case 'badge':
        return (
          <Chip
            label={value}
            size="small"
            color={column.getBadgeColor ? column.getBadgeColor(value) : 'default'}
            sx={{
              background: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              fontSize: '0.75rem',
              fontWeight: 500
            }}
          />
        );
      
      case 'avatar':
        return (
          <Avatar 
            sx={{ 
              width: 32, 
              height: 32,
              fontSize: '0.875rem',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
            }}
          >
            {value?.charAt(0) || '?'}
          </Avatar>
        );
      
      case 'trend':
        const getTrendIcon = () => {
          if (value > 0) return <TrendingUp sx={{ color: '#00ff88', fontSize: 16 }} />;
          if (value < 0) return <TrendingDown sx={{ color: '#ff4757', fontSize: 16 }} />;
          return <Remove sx={{ color: '#ffd93d', fontSize: 16 }} />;
        };
        
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            {getTrendIcon()}
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {Math.abs(value)}
            </Typography>
          </Box>
        );
      
      default:
        return value;
    }
  };

  // Loading skeleton
  const LoadingSkeleton = () => (
    <TableContainer sx={tableVariants[variant]}>
      <Table size={compact ? 'small' : 'medium'}>
        <TableHead>
          <TableRow>
            {columns.map((column, index) => (
              <TableCell key={index}>
                <Box sx={{ 
                  width: '80%', 
                  height: 16, 
                  background: 'rgba(255, 255, 255, 0.1)',
                  borderRadius: '4px',
                  animation: 'pulse 1.5s ease-in-out infinite'
                }} />
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {[...Array(5)].map((_, index) => (
            <TableRow key={index}>
              {columns.map((_, colIndex) => (
                <TableCell key={colIndex}>
                  <Box sx={{ 
                    width: `${60 + Math.random() * 40}%`, 
                    height: 14, 
                    background: 'rgba(255, 255, 255, 0.05)',
                    borderRadius: '4px',
                    animation: 'pulse 1.5s ease-in-out infinite'
                  }} />
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  if (loading) {
    return <LoadingSkeleton />;
  }

  return (
    <motion.div
      variants={containerVariants}
      initial={animate ? "hidden" : false}
      animate={animate ? "visible" : false}
      className={className}
    >
      <GlassCard variant="minimal" padding={0} sx={sx} {...props}>
        {/* Table Header */}
        {(title || subtitle) && (
          <Box sx={{ p: 3, pb: 0 }}>
            {title && (
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                {title}
              </Typography>
            )}
            {subtitle && (
              <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
                {subtitle}
              </Typography>
            )}
          </Box>
        )}

        {/* Table Container */}
        <TableContainer 
          sx={{ 
            maxHeight,
            '&::-webkit-scrollbar': {
              width: 6,
              height: 6,
            },
            '&::-webkit-scrollbar-track': {
              background: 'transparent',
            },
            '&::-webkit-scrollbar-thumb': {
              background: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '3px',
            },
          }}
        >
          <Table 
            size={compact ? 'small' : 'medium'}
            stickyHeader={stickyHeader}
          >
            {/* Table Head */}
            <TableHead>
              <TableRow>
                {expandable && <TableCell sx={{ width: 48 }} />}
                {columns.map((column) => (
                  <TableCell
                    key={column.key}
                    align={column.align || 'left'}
                    sx={{
                      background: 'rgba(255, 255, 255, 0.02)',
                      borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                      fontWeight: 600,
                      fontSize: '0.875rem',
                      color: 'rgba(255, 255, 255, 0.9)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                    }}
                  >
                    {sortable && column.sortable !== false ? (
                      <TableSortLabel
                        active={sortConfig.key === column.key}
                        direction={sortConfig.key === column.key ? sortConfig.direction : 'asc'}
                        onClick={() => handleSort(column.key)}
                        sx={{
                          color: 'inherit !important',
                          '& .MuiTableSortLabel-icon': {
                            color: 'rgba(255, 255, 255, 0.7) !important',
                          }
                        }}
                      >
                        {column.label}
                      </TableSortLabel>
                    ) : (
                      column.label
                    )}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>

            {/* Table Body */}
            <TableBody>
              <AnimatePresence>
                {sortedData.length === 0 ? (
                  <TableRow>
                    <TableCell 
                      colSpan={columns.length + (expandable ? 1 : 0)}
                      sx={{ textAlign: 'center', py: 4 }}
                    >
                      <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                        {emptyMessage}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  sortedData.map((row, index) => (
                    <React.Fragment key={row.id || index}>
                      <motion.tr
                        variants={rowVariants}
                        style={{
                          cursor: onRowClick ? 'pointer' : 'default',
                        }}
                        whileHover={hoverable ? {
                          backgroundColor: 'rgba(255, 255, 255, 0.05)',
                          x: 4,
                          transition: { duration: 0.2 }
                        } : {}}
                        onClick={() => onRowClick?.(row)}
                      >
                        {/* Expand button */}
                        {expandable && (
                          <TableCell sx={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleRowExpansion(row.id || index);
                              }}
                              sx={{ color: 'rgba(255, 255, 255, 0.7)' }}
                            >
                              {expandedRows.has(row.id || index) ? 
                                <ExpandLess /> : <ExpandMore />
                              }
                            </IconButton>
                          </TableCell>
                        )}
                        
                        {/* Data cells */}
                        {columns.map((column) => (
                          <TableCell
                            key={column.key}
                            align={column.align || 'left'}
                            sx={{
                              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                              fontSize: '0.875rem',
                              color: 'rgba(255, 255, 255, 0.9)',
                              backgroundColor: striped && index % 2 === 1 ? 
                                'rgba(255, 255, 255, 0.02)' : 'transparent',
                            }}
                          >
                            {renderCellContent(row[column.key], column)}
                          </TableCell>
                        ))}
                      </motion.tr>

                      {/* Expanded row content */}
                      {expandable && expandedRows.has(row.id || index) && (
                        <TableRow>
                          <TableCell 
                            colSpan={columns.length + 1}
                            sx={{ 
                              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                              background: 'rgba(255, 255, 255, 0.02)',
                              p: 0
                            }}
                          >
                            <Collapse in={expandedRows.has(row.id || index)}>
                              <Box sx={{ p: 2 }}>
                                {renderExpandedRow?.(row) || (
                                  <Typography variant="body2">
                                    Expanded content for row {index + 1}
                                  </Typography>
                                )}
                              </Box>
                            </Collapse>
                          </TableCell>
                        </TableRow>
                      )}
                    </React.Fragment>
                  ))
                )}
              </AnimatePresence>
            </TableBody>
          </Table>
        </TableContainer>
      </GlassCard>
    </motion.div>
  );
};

// Preset table configurations for FPL use cases
export const LeagueTable = (props) => (
  <ModernTable 
    variant="glass"
    sortable
    hoverable
    striped
    columns={[
      { key: 'rank', label: 'Rank', type: 'number', align: 'center' },
      { key: 'team_name', label: 'Team' },
      { key: 'player_name', label: 'Manager' },
      { key: 'total', label: 'Points', type: 'number', align: 'right' },
      { key: 'event_total', label: 'GW', type: 'number', align: 'right' },
    ]}
    {...props}
  />
);

export const H2HTable = (props) => (
  <ModernTable 
    variant="elevated"
    expandable
    hoverable
    columns={[
      { key: 'player_name', label: 'Manager' },
      { key: 'matches_won', label: 'W', type: 'number', align: 'center' },
      { key: 'matches_drawn', label: 'D', type: 'number', align: 'center' },
      { key: 'matches_lost', label: 'L', type: 'number', align: 'center' },
      { key: 'points_for', label: 'PF', type: 'number', align: 'right' },
      { key: 'points_against', label: 'PA', type: 'number', align: 'right' },
    ]}
    {...props}
  />
);

export const PlayerTable = (props) => (
  <ModernTable 
    variant="minimal"
    compact
    columns={[
      { key: 'name', label: 'Player' },
      { key: 'team', label: 'Team' },
      { key: 'position', label: 'Pos', align: 'center' },
      { key: 'points', label: 'Pts', type: 'number', align: 'right' },
      { key: 'price', label: 'Price', type: 'number', format: 'currency', align: 'right' },
    ]}
    {...props}
  />
);

export default ModernTable;