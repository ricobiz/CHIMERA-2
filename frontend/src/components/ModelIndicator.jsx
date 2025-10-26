import React, { useState } from 'react';
import { CodeIcon, EyeIcon } from './Icons';

const ModelIndicator = ({ type, modelName, isActive }) => {
  const [showTooltip, setShowTooltip] = useState(false);

  const getColor = () => {
    if (type === 'code') return 'text-blue-400 hover:text-blue-300';
    return 'text-green-400 hover:text-green-300';
  };

  const getShadow = () => {
    if (type === 'code') return 'hover:drop-shadow-[0_0_8px_rgba(96,165,250,0.5)]';
    return 'hover:drop-shadow-[0_0_8px_rgba(74,222,128,0.5)]';
  };

  const Icon = type === 'code' ? CodeIcon : EyeIcon;

  if (!isActive && type === 'validator') return null;

  return (
    <div className="relative">
      <div
        className={`cursor-pointer p-2 rounded-lg bg-gray-800/50 hover:bg-gray-700/50 border border-gray-700 hover:border-gray-600 transition-all ${getColor()} ${getShadow()}`}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <Icon className="w-4 h-4" />
      </div>

      {showTooltip && (
        <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 px-3 py-1.5 bg-gray-900 border border-gray-600 rounded text-xs text-gray-200 whitespace-nowrap z-50 shadow-xl">
          <div className="text-gray-400 text-[9px] uppercase tracking-wider mb-0.5">
            {type === 'code' ? 'Code Model' : 'Validator Model'}
          </div>
          <div className="font-medium">
            {modelName || 'Not set'}
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelIndicator;