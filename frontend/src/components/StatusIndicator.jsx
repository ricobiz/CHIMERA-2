import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const StatusIndicator = () => {
  const [status, setStatus] = useState(null);
  const [showTooltip, setShowTooltip] = useState(false);

  useEffect(() => {
    checkStatus();
    // Check every 30 seconds
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
        <div className="text-xs">
          <div className="font-semibold mb-1">System Operational</div>
          <div className="text-gray-400">✓ API Key: Valid</div>
          {status.balance !== null && status.balance !== undefined && (
            <div className="text-gray-400">✓ Balance: ${parseFloat(status.balance).toFixed(2)}</div>
          )}
        </div>
      );
    }
    
    return (
      <div className="text-xs">
        <div className="font-semibold mb-1 text-red-400">System Issue</div>
        <div className="text-gray-400">{status.message}</div>
        {!status.has_key && <div className="text-gray-400 mt-1">→ Add OpenRouter API key</div>}
        {status.has_key && !status.key_valid && <div className="text-gray-400 mt-1">→ Check API key validity</div>}
        {status.balance === 0 && <div className="text-gray-400 mt-1">→ Add credits to account</div>}
      </div>
    );
  };

  return (
    <div className="relative">
      <div
        className="flex items-center gap-1.5 cursor-help"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <div className={`w-1.5 h-1.5 rounded-full ${getStatusColor()} ${status.status === 'ok' ? 'animate-pulse' : ''}`}></div>
        <span className="text-[10px] text-gray-500">System</span>
      </div>

      {showTooltip && (
        <div className="absolute top-full left-0 mt-2 p-2.5 bg-gray-900 border border-gray-700 rounded-lg shadow-xl z-50 min-w-[200px]">
          {getTooltipContent()}
        </div>
      )}
    </div>
  );
};

export default StatusIndicator;
