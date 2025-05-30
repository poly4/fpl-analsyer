// Comprehensive animation system with Framer Motion
import { keyframes } from '@emotion/react';

// Animation duration constants for consistency
export const ANIMATION_DURATION = {
  instant: 0.1,
  fast: 0.2,
  normal: 0.3,
  slow: 0.5,
  slower: 0.8,
  slowest: 1.2
};

// Easing functions
export const EASING = {
  easeInOut: [0.4, 0, 0.2, 1],
  easeOut: [0, 0, 0.2, 1],
  easeIn: [0.4, 0, 1, 1],
  sharp: [0.4, 0, 0.6, 1],
  bounce: [0.175, 0.885, 0.32, 1.275],
  elastic: [0.68, -0.55, 0.265, 1.55]
};

// Framer Motion animation variants
export const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
  transition: { duration: ANIMATION_DURATION.normal }
};

export const slideIn = {
  initial: { x: -20, opacity: 0 },
  animate: { x: 0, opacity: 1 },
  exit: { x: 20, opacity: 0 },
  transition: { duration: ANIMATION_DURATION.normal, ease: EASING.easeOut }
};

export const slideUp = {
  initial: { y: 20, opacity: 0 },
  animate: { y: 0, opacity: 1 },
  exit: { y: -20, opacity: 0 },
  transition: { duration: ANIMATION_DURATION.normal, ease: EASING.easeOut }
};

export const scaleIn = {
  initial: { scale: 0.9, opacity: 0 },
  animate: { scale: 1, opacity: 1 },
  exit: { scale: 0.9, opacity: 0 },
  transition: { duration: ANIMATION_DURATION.fast, ease: EASING.easeOut }
};

export const rotateIn = {
  initial: { rotate: -10, opacity: 0 },
  animate: { rotate: 0, opacity: 1 },
  exit: { rotate: 10, opacity: 0 },
  transition: { duration: ANIMATION_DURATION.normal, ease: EASING.bounce }
};

// Stagger children animations
export const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2
    }
  }
};

export const staggerItem = {
  initial: { y: 20, opacity: 0 },
  animate: {
    y: 0,
    opacity: 1,
    transition: {
      duration: ANIMATION_DURATION.normal,
      ease: EASING.easeOut
    }
  }
};

// Hover animations
export const hoverScale = {
  whileHover: { 
    scale: 1.05,
    transition: { duration: ANIMATION_DURATION.fast }
  },
  whileTap: { 
    scale: 0.95,
    transition: { duration: ANIMATION_DURATION.instant }
  }
};

export const hoverGlow = {
  whileHover: {
    boxShadow: '0 0 20px rgba(102, 126, 234, 0.6)',
    transition: { duration: ANIMATION_DURATION.fast }
  }
};

export const hoverLift = {
  whileHover: {
    y: -5,
    boxShadow: '0 10px 30px rgba(0, 0, 0, 0.3)',
    transition: { duration: ANIMATION_DURATION.fast }
  }
};

// Number count animations
export const animateNumber = {
  initial: { opacity: 0, y: 10 },
  animate: { 
    opacity: 1, 
    y: 0,
    transition: {
      duration: ANIMATION_DURATION.slow,
      ease: EASING.easeOut
    }
  }
};

// Success celebration animations
export const successPulse = {
  animate: {
    scale: [1, 1.2, 1],
    opacity: [1, 0.8, 1],
    transition: {
      duration: ANIMATION_DURATION.normal,
      repeat: 3,
      ease: EASING.easeInOut
    }
  }
};

export const successBounce = {
  animate: {
    y: [0, -20, 0],
    transition: {
      duration: ANIMATION_DURATION.slow,
      ease: EASING.bounce,
      repeat: 2
    }
  }
};

// Page transition variants
export const pageSlideLeft = {
  initial: { x: '100%', opacity: 0 },
  animate: { x: 0, opacity: 1 },
  exit: { x: '-100%', opacity: 0 },
  transition: { 
    duration: ANIMATION_DURATION.normal,
    ease: EASING.easeInOut
  }
};

export const pageSlideUp = {
  initial: { y: '100%', opacity: 0 },
  animate: { y: 0, opacity: 1 },
  exit: { y: '-100%', opacity: 0 },
  transition: { 
    duration: ANIMATION_DURATION.normal,
    ease: EASING.easeOut
  }
};

export const pageFade = {
  initial: { opacity: 0 },
  animate: { 
    opacity: 1,
    transition: { duration: ANIMATION_DURATION.slow }
  },
  exit: { 
    opacity: 0,
    transition: { duration: ANIMATION_DURATION.fast }
  }
};

// Card flip animation
export const cardFlip = {
  initial: { rotateY: 0 },
  animate: { rotateY: 180 },
  transition: {
    duration: ANIMATION_DURATION.slow,
    ease: EASING.easeInOut
  }
};

// Loading animations
export const loadingDots = {
  animate: {
    opacity: [0, 1, 0],
    transition: {
      duration: 1.5,
      repeat: Infinity,
      ease: EASING.easeInOut
    }
  }
};

export const loadingRotate = {
  animate: {
    rotate: 360,
    transition: {
      duration: 1,
      repeat: Infinity,
      ease: 'linear'
    }
  }
};

// Parallax effect
export const parallax = (offset = 0) => ({
  initial: { y: offset },
  animate: { y: 0 },
  transition: {
    duration: ANIMATION_DURATION.slower,
    ease: EASING.easeOut
  }
});

// CSS Keyframe animations for non-Framer Motion elements
export const shimmer = keyframes`
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
`;

export const pulse = keyframes`
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
`;

export const spin = keyframes`
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
`;

export const float = keyframes`
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
`;

// Gesture animations
export const swipeableCard = {
  drag: 'x',
  dragConstraints: { left: -100, right: 100 },
  dragElastic: 0.5,
  whileDrag: { scale: 1.1 },
  onDragEnd: (event, info) => {
    if (Math.abs(info.offset.x) > 100) {
      // Card swiped away
      return { x: info.offset.x > 0 ? 200 : -200, opacity: 0 };
    }
    return { x: 0 };
  }
};

// Scroll-triggered animations
export const scrollFadeIn = {
  initial: { opacity: 0, y: 50 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.3 },
  transition: {
    duration: ANIMATION_DURATION.slow,
    ease: EASING.easeOut
  }
};

// 3D transforms
export const rotate3D = {
  initial: { rotateX: -30, opacity: 0 },
  animate: { rotateX: 0, opacity: 1 },
  transition: {
    duration: ANIMATION_DURATION.slow,
    ease: EASING.easeOut
  }
};

// Morphing shapes
export const morphPath = {
  initial: { pathLength: 0 },
  animate: { pathLength: 1 },
  transition: {
    duration: ANIMATION_DURATION.slower,
    ease: EASING.easeInOut
  }
};

// Utility functions
export const staggerDelay = (index, delay = 0.1) => ({
  transition: { delay: index * delay }
});

export const animateOnScroll = (element, animation) => {
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('animate');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1 }
    );
    observer.observe(element);
  }
};

// Particle system for goals
export const createParticles = (x, y, count = 20) => {
  const particles = [];
  for (let i = 0; i < count; i++) {
    const angle = (Math.PI * 2 * i) / count;
    const velocity = 100 + Math.random() * 100;
    particles.push({
      id: i,
      initial: { x, y, scale: 1, opacity: 1 },
      animate: {
        x: x + Math.cos(angle) * velocity,
        y: y + Math.sin(angle) * velocity,
        scale: 0,
        opacity: 0
      },
      transition: {
        duration: ANIMATION_DURATION.slower,
        ease: EASING.easeOut
      }
    });
  }
  return particles;
};

// Export all animations as a collection
export const animations = {
  fadeIn,
  slideIn,
  slideUp,
  scaleIn,
  rotateIn,
  staggerContainer,
  staggerItem,
  hoverScale,
  hoverGlow,
  hoverLift,
  animateNumber,
  successPulse,
  successBounce,
  pageSlideLeft,
  pageSlideUp,
  pageFade,
  cardFlip,
  loadingDots,
  loadingRotate,
  parallax,
  swipeableCard,
  scrollFadeIn,
  rotate3D,
  morphPath
};

// Performance-optimized animation hook
export const useOptimizedAnimation = (animationVariant, dependencies = []) => {
  const shouldReduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  
  if (shouldReduceMotion) {
    return {
      initial: {},
      animate: {},
      exit: {},
      transition: { duration: 0 }
    };
  }
  
  return animationVariant;
};

// Batch animations for better performance
export const batchAnimate = (elements, animation, staggerDelay = 0.1) => {
  elements.forEach((element, index) => {
    setTimeout(() => {
      element.classList.add(animation);
    }, index * staggerDelay * 1000);
  });
};

export default animations;