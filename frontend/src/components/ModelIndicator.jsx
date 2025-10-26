import React, { useState } from 'react';
import { CodeIcon, EyeIcon } from './Icons';

const ModelIndicator = ({ type, modelName, isActive }) => {
  const [showTooltip, setShowTooltip] = useState(false);

  const getColor = () => {
    if (type === 'code') return 'text-blue-400';
    return 'text-green-400';
  };

  const Icon = type === 'code' ? CodeIcon : EyeIcon;

  if (!isActive && type === 'validator') return null;

  return (
    <div className="relative">
      <div
        className={`cursor-pointer ${getColor()} opacity-60 hover:opacity-100 transition-opacity`}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <Icon className="w-4 h-4" />
      </div>

      {showTooltip && (
        <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 px-2 py-1 bg-gray-900 border border-gray-700 rounded text-[10px] text-gray-300 whitespace-nowrap z-50 shadow-xl">
          {modelName || 'Not set'}
        </div>
      )}
    </div>
  );
};

export default ModelIndicator;