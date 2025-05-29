# Modernize Component Command

**Purpose:** Transform an existing React component to 2025 modern design standards with glassmorphism, animations, and enhanced UX.

## Usage
```bash
> /modernize-component ComponentName
```

## Template Prompt

```
ultrathink and completely modernize the {ComponentName} component with 2025 design excellence:

## 1. Visual Transformation
- Apply glassmorphism design system from MODERNIZATION_ANALYSIS.md
- Implement backdrop-filter: blur(20px) with rgba backgrounds
- Add subtle borders with glass effects (rgba(255,255,255,0.1))
- Use modern gradient backgrounds and accent colors
- Apply consistent border-radius: 12px for modern aesthetics

## 2. Animation Integration
- Add Framer Motion for smooth transitions (300ms ease-out)
- Implement staggered animations for list items (50ms delay)
- Create hover effects with scale transforms (scale: 1.02)
- Add smooth loading states with shimmer effects
- Ensure 60fps performance for all animations

## 3. Enhanced UX Patterns
- Implement modern interaction feedback
- Add visual hierarchy with proper spacing (8px, 16px, 24px, 32px)
- Create responsive design that works on all screen sizes
- Add accessibility improvements (ARIA labels, keyboard navigation)
- Include error states with beautiful messaging

## 4. Component Architecture
- Break down large components into smaller, reusable parts
- Separate business logic from presentation components
- Add proper TypeScript types for all props
- Implement error boundaries for graceful failure
- Create composable component patterns

## 5. Data Visualization (if applicable)
- Use glassmorphic containers for charts
- Add animated data transitions
- Implement real-time value counters with AnimatedNumber
- Create interactive hover states for data points
- Add loading skeletons that match the final layout

## 6. Performance Optimization
- Implement proper memoization (React.memo, useMemo, useCallback)
- Add lazy loading for heavy components
- Optimize re-renders with efficient state management
- Use proper dependency arrays in useEffect
- Implement abort controllers for API calls

## Requirements:
- Maintain all existing functionality
- Improve visual appeal dramatically
- Add smooth animations without performance impact
- Follow 2025 design trends (glassmorphism, micro-interactions)
- Ensure mobile responsiveness
- Add comprehensive error handling
- Include loading states for all async operations

## Testing:
- Test component in isolation
- Verify animations at 60fps
- Check responsiveness on mobile/desktop
- Validate accessibility with screen readers
- Test error states and edge cases

Remember to use the design system variables from themes.js and maintain consistency with other modernized components.
```

## Example Usage

### Input:
```bash
> /modernize-component ManagerComparison
```

### Expected Action:
Claude will completely redesign the ManagerComparison component with:
- Glassmorphic cards for manager display
- Animated statistics with real-time counters
- Smooth transitions between comparison tabs
- Modern data tables with hover effects
- Responsive design with mobile optimizations
- Enhanced loading states with staggered animations