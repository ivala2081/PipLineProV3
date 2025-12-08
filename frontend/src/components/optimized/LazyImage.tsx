/**
 * Optimized Lazy Loading Image Component
 * Supports responsive images, lazy loading, and placeholder
 */

import React, { useState, useRef, useEffect } from 'react';

interface LazyImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string;
  alt: string;
  placeholder?: string;
  srcSet?: string;
  sizes?: string;
  loading?: 'lazy' | 'eager';
  onLoad?: () => void;
  onError?: () => void;
}

const LazyImage: React.FC<LazyImageProps> = ({
  src,
  alt,
  placeholder,
  srcSet,
  sizes,
  loading = 'lazy',
  onLoad,
  onError,
  className,
  ...props
}) => {
  const [imageSrc, setImageSrc] = useState<string>(placeholder || '');
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    if (!imgRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setImageSrc(src);
            observer.disconnect();
          }
        });
      },
      {
        rootMargin: '50px',
      }
    );

    if (loading === 'lazy') {
      observer.observe(imgRef.current);
    } else {
      setImageSrc(src);
    }

    return () => {
      observer.disconnect();
    };
  }, [src, loading]);

  const handleLoad = () => {
    setIsLoaded(true);
    onLoad?.();
  };

  const handleError = () => {
    setHasError(true);
    onError?.();
  };

  return (
    <div className={`relative overflow-hidden ${className || ''}`}>
      {!isLoaded && placeholder && (
        <img
          src={placeholder}
          alt=""
          className="absolute inset-0 w-full h-full object-cover blur-sm"
          aria-hidden="true"
        />
      )}
      <img
        ref={imgRef}
        src={imageSrc}
        alt={alt}
        srcSet={srcSet}
        sizes={sizes}
        loading={loading}
        onLoad={handleLoad}
        onError={handleError}
        className={`transition-opacity duration-300 ${
          isLoaded ? 'opacity-100' : 'opacity-0'
        } ${hasError ? 'hidden' : ''}`}
        {...props}
      />
      {hasError && (
        <div className="flex items-center justify-center w-full h-full bg-gray-200 text-gray-500">
          <span>Failed to load image</span>
        </div>
      )}
    </div>
  );
};

export default LazyImage;

