import React, { useState, useEffect } from 'react';
import { RefreshCw, Code, AlertCircle, CheckCircle, TrendingUp, Zap } from 'lucide-react';

const SelfImprovement = ({ onClose }) => {
  const [healthStatus, setHealthStatus] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedTarget, setSelectedTarget] = useState('full');
  const [modelAssignments, setModelAssignments] = useState(null);
  const [isOptimizing, setIsOptimizing] = useState(false);

  useEffect(() => {
    checkHealth();
    fetchCurrentModels();
  }, []);

  const fetchCurrentModels = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/self-improvement/model-assignments`);
      const data = await response.json();
      setModelAssignments(data);
    } catch (error) {
      console.error('Error fetching models:', error);
    }
  };

  const optimizeModels = async () => {
    setIsOptimizing(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/self-improvement/optimize-models`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      setModelAssignments(data);
      alert('✅ Models optimized successfully! Changes will apply after refresh.');
    } catch (error) {
      console.error('Optimization error:', error);
      alert('❌ Optimization failed');
    } finally {
      setIsOptimizing(false);
    }
  };

  const checkHealth = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/self-improvement/health-check`);
      const data = await response.json();
      setHealthStatus(data);
    } catch (error) {
      console.error('Health check error:', error);
    }
  };

  const analyzeCode = async () => {
    setIsAnalyzing(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/self-improvement/analyze-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target: selectedTarget,
          focus_areas: ['performance', 'security', 'code_quality', 'bugs']
        })
      });
      const data = await response.json();
      setAnalysis(data);
    } catch (error) {
      console.error('Analysis error:', error);
      alert('Analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const reloadServices = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/self-improvement/reload-services`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ services: ['backend', 'frontend'] })
      });
      const data = await response.json();
      alert(data.success ? 'Services reloaded!' : 'Reload failed');
      checkHealth();
    } catch (error) {
      console.error('Reload error:', error);
    }
  };

  return (
    <div className="flex h-screen bg-[#0f0f10]">
      <div className="w-full">
        <div className="flex items-center justify-between p-4 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <Zap className="w-6 h-6 text-blue-400" />
            <h1 className="text-xl font-semibold text-white">Self-Improvement System</h1>
          </div>
          <button onClick={onClose} className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg">← Back</button>
        </div>

        <div className="p-6 overflow-y-auto" style={{ height: 'calc(100vh - 73px)' }}>
          <div className="max-w-7xl mx-auto space-y-6">
            
            {/* Model Optimization Section */}
            <div className="bg-gradient-to-r from-purple-900/30 to-blue-900/30 rounded-lg border border-purple-700/50 p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-lg font-semibold text-white mb-1">🎯 Model Optimization</h2>
                  <p className="text-sm text-gray-400">Автоматически назначить оптимальные модели для всех задач</p>
                </div>
                <button 
                  onClick={optimizeModels} 
                  disabled={isOptimizing}
                  className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl"
                >
                  {isOptimizing ? (
                    <span className="flex items-center gap-2">
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Оптимизация...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <Zap className="w-4 h-4" />
                      Оптимизировать Модели
                    </span>
                  )}
                </button>
              </div>

              {modelAssignments && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                  {Object.entries(modelAssignments.assignments || {}).map(([task, info]) => (
                    <div key={task} className="bg-gray-900/70 border border-gray-700 rounded-lg p-4 hover:border-purple-500/50 transition-colors">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="text-white font-medium mb-1">{info.name || task}</h3>
                          <p className="text-xs text-gray-400 mb-2">{info.description}</p>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-blue-400 font-mono">{info.model}</span>
                            {info.is_free && <span className="px-2 py-0.5 bg-green-600/20 text-green-400 text-xs rounded-full border border-green-600/50">FREE</span>}
                          </div>
                        </div>
                        {info.cost_per_1m && (
                          <div className="text-right">
                            <p className="text-xs text-gray-500">Cost/1M tokens</p>
                            <p className="text-sm text-purple-400">${info.cost_per_1m}</p>
                          </div>
                        )}
                      </div>
                      {info.reason && (
                        <p className="text-xs text-gray-500 mt-2 border-t border-gray-800 pt-2">💡 {info.reason}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* System Health */}
            <div className="bg-gray-900/50 rounded-lg border border-gray-800 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white">System Health</h2>
                <button onClick={checkHealth} className="p-2 bg-blue-600 hover:bg-blue-500 rounded-lg">
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>
              
              {healthStatus && (
                <div className="grid grid-cols-3 gap-4">
                  {Object.entries(healthStatus.services).map(([name, info]) => (
                    <div key={name} className="bg-gray-800/50 rounded-lg p-4">
                      <div className="flex items-center gap-2">
                        {info.healthy ? <CheckCircle className="w-5 h-5 text-green-400" /> : <AlertCircle className="w-5 h-5 text-red-400" />}
                        <span className="text-white font-medium">{name}</span>
                      </div>
                      <p className={`text-sm mt-1 ${info.healthy ? 'text-green-400' : 'text-red-400'}`}>{info.status}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Code Analysis */}
            <div className="bg-gray-900/50 rounded-lg border border-gray-800 p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Code Analysis & Optimization</h2>
              
              <div className="flex gap-4 mb-4">
                <select value={selectedTarget} onChange={(e) => setSelectedTarget(e.target.value)} className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white">
                  <option value="full">Full Application</option>
                  <option value="backend">Backend Only</option>
                  <option value="frontend">Frontend Only</option>
                </select>
                
                <button onClick={analyzeCode} disabled={isAnalyzing} className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white rounded-lg disabled:opacity-50">
                  {isAnalyzing ? 'Analyzing...' : 'Analyze Code'}
                </button>
                
                <button onClick={reloadServices} className="px-6 py-2 bg-orange-600 hover:bg-orange-500 text-white rounded-lg">
                  Reload Services
                </button>
              </div>

              {analysis && (
                <div className="space-y-4 mt-6">
                  <div className="flex items-center gap-4">
                    <div className="text-3xl font-bold text-white">{analysis.overall_health_score}/100</div>
                    <div className="flex-1 h-4 bg-gray-800 rounded-full">
                      <div className={`h-full rounded-full ${analysis.overall_health_score >= 80 ? 'bg-green-500' : analysis.overall_health_score >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`} style={{ width: `${analysis.overall_health_score}%` }}></div>
                    </div>
                  </div>

                  {analysis.critical_issues && analysis.critical_issues.length > 0 && (
                    <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
                      <h3 className="text-red-400 font-semibold mb-2">Critical Issues ({analysis.critical_issues.length})</h3>
                      {analysis.critical_issues.slice(0, 5).map((issue, idx) => (
                        <div key={idx} className="text-sm text-gray-300 mb-2">
                          <span className="text-red-400 font-semibold">[{issue.severity}]</span> {issue.file}: {issue.issue}
                        </div>
                      ))}
                    </div>
                  )}

                  {analysis.improvements && analysis.improvements.length > 0 && (
                    <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-4">
                      <h3 className="text-blue-400 font-semibold mb-2">Improvements ({analysis.improvements.length})</h3>
                      {analysis.improvements.slice(0, 5).map((imp, idx) => (
                        <div key={idx} className="text-sm text-gray-300 mb-2">
                          <span className="text-blue-400 font-semibold">[{imp.category}]</span> {imp.file}: {imp.suggested}
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="bg-gray-800/50 rounded-lg p-4">
                    <h3 className="text-gray-300 font-semibold mb-2">Summary</h3>
                    <p className="text-gray-400 text-sm">{analysis.summary}</p>
                  </div>
                </div>
              )}
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

export default SelfImprovement;
