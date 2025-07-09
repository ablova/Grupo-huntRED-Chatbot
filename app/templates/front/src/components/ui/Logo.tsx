import React from 'react';

interface LogoProps {
  className?: string;
  color?: string;
  secondaryColor?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | number;
}

/**
 * Logo de Grupo huntRED®
 * Componente SVG inline para mayor flexibilidad de estilo
 */
export const Logo: React.FC<LogoProps> = ({ 
  className = "", 
  color = "#ffffff", 
  secondaryColor = "#ff3b30",
  size = 'md' 
}) => {
  // Mapeo de tamaños para facilitar el uso
  const sizeMap = {
    sm: 24,
    md: 32,
    lg: 48,
    xl: 64
  };
  
  // Determinar el tamaño final
  const finalSize = typeof size === 'number' ? size : sizeMap[size];
  
  return (
    <svg 
      className={className} 
      width={finalSize} 
      height={finalSize} 
      viewBox="0 0 512 512"
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Círculo exterior */}
      <circle cx="256" cy="256" r="240" fill="transparent" stroke={color} strokeWidth="16" />
      
      {/* Letra "h" estilizada */}
      <path 
        d="M150 130v252M150 256h100M250 130v252" 
        stroke={color} 
        strokeWidth="32" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      />
      
      {/* Punto rojo - marca característica */}
      <circle cx="350" cy="200" r="40" fill={secondaryColor} />
    </svg>
  );
};

export default Logo;
