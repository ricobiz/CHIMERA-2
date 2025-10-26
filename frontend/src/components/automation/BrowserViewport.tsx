import React from 'react';
import { BrowserState, HighlightBox } from '../../agent/types.ts';

interface BrowserViewportProps {
  browserState: BrowserState;
  status: string;
}

const BrowserViewport: React.FC<BrowserViewportProps> = ({ browserState, status }) => {
  return (
    <div className="flex flex-col bg-gray-900 border border-gray-800 rounded-lg overflow-hidden" style={{ height: '100%', minHeight: '300px' }}>
      {/* Viewport Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700 flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
          </div>
          <span className="text-xs text-gray-400 ml-3">Browser Viewport</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500">{browserState.pageTitle || 'Loading...'}</span>
          {status && (
            <span className={`text-xs px-2 py-1 rounded ${
              status === 'executing' ? 'bg-blue-900 text-blue-300' :
              status === 'completed' ? 'bg-green-900 text-green-300' :
              status === 'failed' ? 'bg-red-900 text-red-300' :
              'bg-gray-700 text-gray-400'
            }`}>
              {status.toUpperCase()}
            </span>
          )}
        </div>
      </div>

      {/* URL Bar */}
      <div className="px-4 py-2 bg-gray-850 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          <div className="flex-1 bg-gray-900 border border-gray-700 rounded px-3 py-1.5">
            <span className="text-sm text-gray-400 font-mono">
              {browserState.currentUrl || 'about:blank'}
            </span>
          </div>
        </div>
      </div>

      {/* Browser Content Area */}
      <div className="flex-1 relative overflow-hidden bg-gray-950">
        {browserState.screenshot ? (
          <div className="relative w-full h-full">
            {/* Screenshot */}
            <img
              src={browserState.screenshot}
              alt="Browser viewport"
              className="w-full h-full object-contain"
            />

            {/* Highlight Boxes Overlay */}
            {browserState.highlightBoxes && browserState.highlightBoxes.length > 0 && (
              <div className="absolute inset-0 pointer-events-none">
                {browserState.highlightBoxes.map((box, index) => (
                  <div
                    key={index}
                    className="absolute border-2 rounded transition-all duration-300 animate-pulse"
                    style={{
                      left: `${box.x}px`,
                      top: `${box.y}px`,
                      width: `${box.w}px`,
                      height: `${box.h}px`,
                      borderColor: box.color || '#3b82f6',
                      boxShadow: `0 0 20px ${box.color || '#3b82f6'}80`
                    }}
                  >
                    {box.label && (
                      <div
                        className="absolute -top-6 left-0 px-2 py-1 rounded text-xs font-medium whitespace-nowrap"
                        style={{
                          backgroundColor: box.color || '#3b82f6',
                          color: 'white'
                        }}
                      >
                        {box.label}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          /* Empty State */
          <div className="flex flex-col items-center justify-center h-full text-gray-600">
            <svg className="w-24 h-24 mb-4 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <p className="text-lg font-medium">No Active Session</p>
            <p className="text-sm mt-1">Start automation to see browser activity</p>
          </div>
        )}
      </div>

      {/* Status Bar */}
      <div className="px-4 py-1.5 bg-gray-800 border-t border-gray-700">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Ready</span>
          <span>{new Date(browserState.timestamp || Date.now()).toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  );
};

export default BrowserViewport;
