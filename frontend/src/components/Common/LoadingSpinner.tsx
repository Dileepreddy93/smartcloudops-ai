import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  className?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  text = 'Loading...',
  className = '' 
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  };

  return (
    <div 
      className={`flex flex-col items-center justify-center ${className}`}
      role="status"
      aria-live="polite"
      aria-label={text}
    >
      <div
        className={`${sizeClasses[size]} animate-spin rounded-full border-4 border-gray-200 border-t-blue-600`}
        aria-hidden="true"
      />
      {text && (
        <p className="mt-2 text-sm text-gray-600" aria-label={text}>
          {text}
        </p>
      )}
    </div>
  );
};

export default LoadingSpinner;
