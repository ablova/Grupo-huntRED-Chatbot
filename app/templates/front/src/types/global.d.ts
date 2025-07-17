// Type declarations for modules without types
declare module '@radix-ui/react-context-menu' {
  export * from '@radix-ui/react-context-menu';
}

// Add type declarations for other missing modules as needed
declare module 'embla-carousel-react' {
  import { EmblaOptionsType } from 'embla-carousel';
  import { CSSProperties, ReactNode } from 'react';

  export interface EmblaCarouselProps {
    children: ReactNode;
    options?: EmblaOptionsType;
    className?: string;
    style?: CSSProperties;
  }

  const EmblaCarousel: React.FC<EmblaCarouselProps>;
  export default EmblaCarousel;
}

// Add global type overrides
declare namespace JSX {
  interface IntrinsicElements {
    'style': React.DetailedHTMLProps<
      React.StyleHTMLAttributes<HTMLStyleElement> & { jsx?: boolean },
      HTMLStyleElement
    >;
  }
}

// Fix for react-day-picker custom components
declare module 'react-day-picker' {
  import { DayPickerProps } from 'react-day-picker';
  
  export interface CustomComponents extends DayPickerProps['components'] {
    IconLeft?: React.ComponentType<{ className?: string }>;
    IconRight?: React.ComponentType<{ className?: string }>;
  }
}
