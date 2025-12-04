/**
 * AILogo Component - Premium 3D Rotating Atomic Structure Logo
 * 
 * INSTALLATION:
 * 1. Install dependencies:
 *    npm install framer-motion
 *    or
 *    yarn add framer-motion
 * 
 * 2. Copy this file to your project
 * 
 * 3. Import and use:
 *    import { AILogo } from './components/AILogo';
 *    <AILogo />
 * 
 * CUSTOMIZATION:
 * - Adjust size by wrapping in a container with width/height
 * - Change colors by modifying the gradient stop colors
 * - Adjust animation speed by changing the duration values
 * - Add/remove orbital rings by modifying the array in line 55
 */

import { motion } from 'framer-motion';

export function AILogo() {
  return (
    <div 
      className="relative w-96 h-96 flex items-center justify-center"
      style={{
        perspective: 1000,
        transformStyle: 'preserve-3d',
      }}
    >
      {/* 3D Orbital rings with electrons */}
      {[0, 1, 2, 3, 4, 5, 6, 7].map((orbitIndex) => {
        const baseRadius = 70 + orbitIndex * 22;
        const duration = 4 + orbitIndex * 0.6;
        const rotationX = 60 + (orbitIndex * 15) % 60;
        const rotationY = orbitIndex * 45;
        const electronCount = 1;
        
        return (
          <div key={`orbit-${orbitIndex}`}>
            {/* Orbital ring */}
            <motion.div
              className="absolute"
              style={{
                width: baseRadius * 2,
                height: baseRadius * 2,
                left: '50%',
                top: '50%',
                marginLeft: -baseRadius,
                marginTop: -baseRadius,
                transformStyle: 'preserve-3d',
              }}
              animate={{
                rotateX: [rotationX, rotationX],
                rotateY: [rotationY, rotationY],
                rotateZ: [0, 360],
              }}
              transition={{
                rotateZ: {
                  duration: duration,
                  repeat: Infinity,
                  ease: "linear",
                },
              }}
            >
              <div 
                className="w-full h-full rounded-full border-2 border-purple-500/25"
                style={{
                  boxShadow: '0 0 15px rgba(168, 85, 247, 0.15)',
                }}
              />
            </motion.div>
            
            {/* Electrons moving along the ring */}
            {[...Array(electronCount)].map((_, electronIndex) => {
              const phaseOffset = (electronIndex * (360 / electronCount)) + (orbitIndex * 30);
              const wobbleDuration = 1.8 + (orbitIndex * 0.2);
              
              return (
                <motion.div
                  key={`electron-${orbitIndex}-${electronIndex}`}
                  className="absolute"
                  style={{
                    width: baseRadius * 2,
                    height: baseRadius * 2,
                    left: '50%',
                    top: '50%',
                    marginLeft: -baseRadius,
                    marginTop: -baseRadius,
                    transformStyle: 'preserve-3d',
                  }}
                  animate={{
                    rotateX: [rotationX, rotationX],
                    rotateY: [rotationY, rotationY],
                    rotateZ: [phaseOffset, phaseOffset + 360],
                  }}
                  transition={{
                    rotateZ: {
                      duration: duration,
                      repeat: Infinity,
                      ease: "linear",
                    },
                  }}
                >
                  <motion.div
                    className="absolute w-2.5 h-2.5 rounded-full bg-gradient-to-br from-purple-400 to-pink-500"
                    style={{
                      top: '50%',
                      left: '100%',
                      marginTop: -5,
                      marginLeft: -5,
                      boxShadow: '0 0 10px rgba(236, 72, 153, 0.9), 0 0 5px rgba(168, 85, 247, 0.7)',
                    }}
                    animate={{
                      scale: [1, 1.3, 1],
                      boxShadow: [
                        '0 0 10px rgba(236, 72, 153, 0.9), 0 0 5px rgba(168, 85, 247, 0.7)',
                        '0 0 15px rgba(236, 72, 153, 1), 0 0 8px rgba(168, 85, 247, 0.9)',
                        '0 0 10px rgba(236, 72, 153, 0.9), 0 0 5px rgba(168, 85, 247, 0.7)',
                      ],
                    }}
                    transition={{
                      duration: wobbleDuration,
                      repeat: Infinity,
                      ease: "easeInOut",
                    }}
                  />
                </motion.div>
              );
            })}
          </div>
        );
      })}

      {/* Main 3D rotating sparkle core */}
      <motion.div
        className="relative z-10"
        style={{ 
          perspective: 1200,
          transformStyle: 'preserve-3d',
        }}
        animate={{
          rotateY: [0, 360],
          rotateX: [0, 15, 0, -15, 0],
        }}
        transition={{
          rotateY: {
            duration: 4,
            repeat: Infinity,
            ease: "linear",
          },
          rotateX: {
            duration: 6,
            repeat: Infinity,
            ease: "easeInOut",
          },
        }}
      >
        <svg
          width="140"
          height="140"
          viewBox="0 0 140 140"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          style={{ filter: 'drop-shadow(0 0 60px rgba(168, 85, 247, 0.9)) drop-shadow(0 0 30px rgba(236, 72, 153, 0.6))' }}
        >
          <defs>
            <linearGradient id="spark1" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#c084fc" />
              <stop offset="50%" stopColor="#f472b6" />
              <stop offset="100%" stopColor="#818cf8" />
            </linearGradient>
            <linearGradient id="spark2" x1="100%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#a855f7" />
              <stop offset="50%" stopColor="#ec4899" />
              <stop offset="100%" stopColor="#6366f1" />
            </linearGradient>
            <linearGradient id="sparkHighlight" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#ffffff" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
            </linearGradient>
            <radialGradient id="glow1">
              <stop offset="0%" stopColor="#ffffff" stopOpacity="1" />
              <stop offset="30%" stopColor="#fbbf24" stopOpacity="0.8" />
              <stop offset="60%" stopColor="#f472b6" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#a855f7" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="centerGlow">
              <stop offset="0%" stopColor="#ffffff" stopOpacity="1" />
              <stop offset="100%" stopColor="#fbbf24" stopOpacity="0.8" />
            </radialGradient>
            <filter id="innerGlow">
              <feGaussianBlur stdDeviation="2" result="blur"/>
              <feComposite in="blur" in2="SourceGraphic" operator="atop"/>
            </filter>
          </defs>
          
          {/* Main sparkle core */}
          <g transform="translate(70, 70)">
            {/* Four main beams - with depth */}
            <path
              d="M 0,-50 L 6,-12 L 6,12 L 0,50 L -6,12 L -6,-12 Z"
              fill="url(#spark1)"
            />
            <path
              d="M 0,-50 L 3,-12 L 3,12 L 0,50 L -3,12 L -3,-12 Z"
              fill="url(#sparkHighlight)"
              opacity="0.6"
            />
            
            <path
              d="M -50,0 L -12,-6 L 12,-6 L 50,0 L 12,6 L -12,6 Z"
              fill="url(#spark2)"
            />
            <path
              d="M -50,0 L -12,-3 L 12,-3 L 50,0 L 12,3 L -12,3 Z"
              fill="url(#sparkHighlight)"
              opacity="0.6"
            />
            
            {/* Diagonal beams */}
            <path
              d="M -35,-35 L -10,-8 L -8,-10 L -35,-35 M 35,35 L 10,8 L 8,10 L 35,35 Z"
              fill="url(#spark1)"
              opacity="0.9"
            />
            <path
              d="M 35,-35 L 8,-10 L 10,-8 L 35,-35 M -35,35 L -8,10 L -10,8 L -35,35 Z"
              fill="url(#spark2)"
              opacity="0.9"
            />
            
            {/* Secondary smaller beams */}
            <path
              d="M 0,-30 L 2,-10 L 2,10 L 0,30 L -2,10 L -2,-10 Z"
              fill="url(#sparkHighlight)"
              opacity="0.4"
              transform="rotate(22.5)"
            />
            <path
              d="M -30,0 L -10,-2 L 10,-2 L 30,0 L 10,2 L -10,2 Z"
              fill="url(#sparkHighlight)"
              opacity="0.4"
              transform="rotate(22.5)"
            />
            

          </g>
        </svg>
      </motion.div>

      {/* Energy particles bursting outward */}
      {[...Array(8)].map((_, i) => {
        const angle = (i * 45) * (Math.PI / 180);
        const distance = 100 + (i % 2) * 30;
        const x = Math.cos(angle) * distance;
        const y = Math.sin(angle) * distance;
        const delay = i * 0.5;
        
        return (
          <motion.div
            key={`particle-${i}`}
            className="absolute w-1 h-1 rounded-full"
            style={{
              left: '50%',
              top: '50%',
              background: 'linear-gradient(135deg, #a855f7, #ec4899)',
              boxShadow: '0 0 8px rgba(168, 85, 247, 0.8)',
            }}
            animate={{
              x: [0, x, 0],
              y: [0, y, 0],
              z: [0, Math.random() * 50 - 25, 0],
              scale: [0, 1.5, 0],
              opacity: [0, 1, 0],
            }}
            transition={{
              duration: 4,
              repeat: Infinity,
              delay: delay,
              ease: "easeOut",
            }}
          />
        );
      })}
    </div>
  );
}
