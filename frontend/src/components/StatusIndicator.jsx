import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const StatusIndicator = () => {
  const [status, setStatus] = useState(null);
  const [showTooltip, setShowTooltip] = useState(false);

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkStatus = async () => {
    try {
      const response = await axios.get(`${API}/system-status`);
      setStatus(response.data);
    } catch (error) {
      setStatus({
        status: 'error',
        message: 'Cannot connect to server',
        has_key: false,
        key_valid: false,
        balance: null
      });
    }
  };

  if (!status) return null;

  const getStatusColor = () => {
    if (status.status === 'ok') return 'bg-green-500';
    if (status.status === 'warning') return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getTooltipContent = () => {
    if (status.status === 'ok') {
      return (
        <div className="text-[10px]">
          <div className="font-semibold mb-1 text-green-400">Operational</div>
          {status.balance !== null && status.balance !== undefined && (
            <div className="text-gray-400">Balance: ${parseFloat(status.balance).toFixed(2)}</div>
          )}
        </div>
      );
    }
    
    return (
      <div className="text-[10px]">
        <div className="font-semibold mb-1 text-red-400">Issue</div>
        <div className="text-gray-400">{status.message}</div>
      </div>
    );
  };

  return (
    <div className="relative flex items-center gap-1.5">
      <div
        className={`w-1.5 h-1.5 rounded-full ${getStatusColor()} ${status.status === 'ok' ? 'animate-pulse' : ''} cursor-help`}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      ></div>
      
      {/* Balance always visible */}
      {status.balance !== null && status.balance !== undefined && (
        <span className="text-[9px] text-gray-600 font-mono">
          ${parseFloat(status.balance).toFixed(2)}
        </span>
      )}

      {showTooltip && (
        <div className="absolute top-full right-0 mt-2 p-2 bg-gray-900 border border-gray-700 rounded shadow-xl z-50 min-w-[140px]">
          {getTooltipContent()}
        </div>
      )}
    </div>
  );
};

export default StatusIndicator;