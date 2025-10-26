import React from 'react';

const ChimeraLogo = ({ size = 'md' }) => {
  const sizes = {
    sm: 'text-xl',
    md: 'text-3xl',
    lg: 'text-5xl'
  };

  return (
    <div className="relative inline-flex items-center">
      {/* Animated glow background */}
      <div className="absolute inset-0 blur-xl opacity-60 animate-pulse">
        <div className="w-full h-full bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-600 rounded-lg"></div>
      </div>
      
      {/* Main logo container */}
      <div className="relative">
        <h1 className={`${sizes[size]} font-bold tracking-wider select-none`}>
          {/* Animated gradient text */}
          <span className="relative inline-block">
            <span className="absolute inset-0 bg-gradient-to-r from-purple-400 via-blue-400 to-cyan-400 bg-clip-text text-transparent animate-gradient-shift blur-sm">
              ХИМЕРА
            </span>
            <span className="relative bg-gradient-to-r from-purple-300 via-blue-300 to-cyan-300 bg-clip-text text-transparent">
              ХИМЕРА
            </span>
          </span>
        </h1>
        
        {/* Animated border frame */}
        <div className="absolute -inset-1 rounded-lg opacity-75 group-hover:opacity-100 transition-opacity">
          <div className="absolute inset-0 rounded-lg animate-border-flow"
               style={{
                 background: 'linear-gradient(90deg, #a855f7, #3b82f6, #06b6d4, #a855f7)',
                 backgroundSize: '200% 200%',
                 padding: '2px',
                 WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
                 WebkitMaskComposite: 'xor',
                 maskComposite: 'exclude'
               }}>
          </div>
        </div>
      </div>
      
      {/* Subtitle */}
      <div className="absolute -bottom-6 left-0 right-0 text-center">
        <span className="text-xs text-gray-400 tracking-widest uppercase">
          AI Automation Platform
        </span>
      </div>
      
      <style jsx>{`
        @keyframes gradient-shift {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        
        @keyframes border-flow {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        
        .animate-gradient-shift {
          background-size: 200% 200%;
          animation: gradient-shift 3s ease infinite;
        }
        
        .animate-border-flow {
          animation: border-flow 4s linear infinite;
        }
      `}</style>
    </div>
  );
};

export default ChimeraLogo;
