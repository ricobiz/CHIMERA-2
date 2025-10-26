import React from 'react';

const ChimeraLogo = ({ className = '' }) => {
  return (
    <div className={`inline-flex flex-col items-start ${className}`}>
      {/* Main logo text with gradient animation */}
      <div className="relative">
        <h1 className="text-lg font-bold tracking-wide select-none leading-none">
          {/* Animated gradient text - letters shimmer */}
          <span className="relative inline-block animate-gradient-text bg-gradient-to-r from-purple-400 via-blue-400 to-purple-400 bg-clip-text text-transparent bg-[length:200%_100%]">
            CHIMERA
          </span>
        </h1>
      </div>
      
      {/* Subtitle - smaller text */}
      <span className="text-[10px] text-gray-500 tracking-wider uppercase mt-0.5">
        Automation System
      </span>
      
      <style jsx>{`
        @keyframes gradient-text {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        
        .animate-gradient-text {
          animation: gradient-text 3s ease infinite;
        }
      `}</style>
    </div>
  );
};

export default ChimeraLogo;
