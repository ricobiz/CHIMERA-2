import React, { useState, useEffect } from 'react';
import { X, Search, AlertCircle, CheckCircle, Loader, Download, Copy } from 'lucide-react';
import { Button } from '../ui/button';
import { toast } from '../../hooks/use-toast';

const BlockchainAnalyzer = ({ onClose }) => {
  const [input, setInput] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [selectedBlockchain, setSelectedBlockchain] = useState('ethereum');
  
  // Models from localStorage
  const [blockchainModel, setBlockchainModel] = useState(
    localStorage.getItem('blockchainModel') || 'openai/gpt-5'
  );

  useEffect(() => {
    // Load analysis history from localStorage
    const history = localStorage.getItem('blockchain_analysis_history');
    if (history) {
      try {
        setAnalysisHistory(JSON.parse(history));
      } catch (e) {
        console.error('Failed to load history:', e);
      }
    }
  }, []);

  const saveToHistory = (analysis) => {
    const newHistory = [
      {
        ...analysis,
        timestamp: Date.now()
      },
      ...analysisHistory
    ].slice(0, 50); // Keep last 50
    
    setAnalysisHistory(newHistory);
    localStorage.setItem('blockchain_analysis_history', JSON.stringify(newHistory));
  };

  const handleAnalyze = async () => {
    if (!input.trim()) {
      toast({
        title: "Input Required",
        description: "Please enter a blockchain address or transaction hash",
        variant: "destructive"
      });
      return;
    }

    setIsAnalyzing(true);
    setAnalysisResult(null);

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/blockchain/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input: input.trim(),
          blockchain: selectedBlockchain,
          model: blockchainModel
        })
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }

      const data = await response.json();
      setAnalysisResult(data);
      saveToHistory(data);

      toast({
        title: "Analysis Complete",
        description: "Blockchain data analyzed successfully",
      });
    } catch (error) {
      console.error('Analysis error:', error);
      toast({
        title: "Analysis Failed",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied",
      description: "Text copied to clipboard",
    });
  };

  const exportResults = () => {
    if (!analysisResult) return;
    
    const dataStr = JSON.stringify(analysisResult, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `blockchain_analysis_${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col h-screen bg-[#0f0f10] text-gray-100">
      {/* Header */}
      <div className="flex-shrink-0 bg-gradient-to-r from-orange-900/30 to-orange-800/30 border-b border-orange-700/50 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center">
              <Search className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Blockchain OSINT Analyzer</h1>
              <p className="text-sm text-gray-400">Analyze blockchain addresses and transactions</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
            title="Close"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-6 space-y-6">
        {/* Input Section */}
        <div className="bg-gray-900/50 rounded-lg p-6 border border-gray-800">
          <div className="space-y-4">
            {/* Blockchain Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Blockchain Network
              </label>
              <div className="flex gap-2">
                {['ethereum', 'bitcoin', 'solana', 'polygon', 'bsc'].map((chain) => (
                  <button
                    key={chain}
                    onClick={() => setSelectedBlockchain(chain)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      selectedBlockchain === chain
                        ? 'bg-orange-600 text-white'
                        : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                    }`}
                  >
                    {chain.charAt(0).toUpperCase() + chain.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Input Field */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Address or Transaction Hash
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !isAnalyzing) {
                      handleAnalyze();
                    }
                  }}
                  placeholder="Enter blockchain address or transaction hash..."
                  className="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500"
                  disabled={isAnalyzing}
                />
                <Button
                  onClick={handleAnalyze}
                  disabled={isAnalyzing || !input.trim()}
                  className="px-6 py-3 bg-orange-600 hover:bg-orange-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isAnalyzing ? (
                    <>
                      <Loader className="w-5 h-5 animate-spin mr-2" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Search className="w-5 h-5 mr-2" />
                      Analyze
                    </>
                  )}
                </Button>
              </div>
            </div>

            {/* Model Selection */}
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">
                AI Model: <span className="text-orange-400 font-medium">{blockchainModel}</span>
              </span>
              <button
                onClick={() => {
                  // TODO: Open settings to change model
                  toast({
                    title: "Model Settings",
                    description: "Go to Settings to change AI model",
                  });
                }}
                className="text-orange-400 hover:text-orange-300 underline"
              >
                Change Model
              </button>
            </div>
          </div>
        </div>

        {/* Analysis Results */}
        {analysisResult && (
          <div className="bg-gray-900/50 rounded-lg p-6 border border-gray-800 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                Analysis Results
              </h2>
              <div className="flex gap-2">
                <button
                  onClick={() => copyToClipboard(JSON.stringify(analysisResult, null, 2))}
                  className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                  title="Copy to clipboard"
                >
                  <Copy className="w-4 h-4 text-gray-400" />
                </button>
                <button
                  onClick={exportResults}
                  className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                  title="Export as JSON"
                >
                  <Download className="w-4 h-4 text-gray-400" />
                </button>
              </div>
            </div>

            {/* Result Content */}
            <div className="space-y-4">
              {analysisResult.type && (
                <div>
                  <span className="text-sm text-gray-400">Type: </span>
                  <span className="text-sm text-white font-medium">
                    {analysisResult.type === 'address' ? 'Blockchain Address' : 'Transaction'}
                  </span>
                </div>
              )}

              {analysisResult.blockchain && (
                <div>
                  <span className="text-sm text-gray-400">Network: </span>
                  <span className="text-sm text-white font-medium capitalize">
                    {analysisResult.blockchain}
                  </span>
                </div>
              )}

              {analysisResult.summary && (
                <div>
                  <h3 className="text-sm font-medium text-gray-300 mb-2">Summary</h3>
                  <p className="text-sm text-gray-100 leading-relaxed whitespace-pre-wrap">
                    {analysisResult.summary}
                  </p>
                </div>
              )}

              {analysisResult.risk_score !== undefined && (
                <div>
                  <h3 className="text-sm font-medium text-gray-300 mb-2">Risk Assessment</h3>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${
                          analysisResult.risk_score > 70
                            ? 'bg-red-500'
                            : analysisResult.risk_score > 40
                            ? 'bg-yellow-500'
                            : 'bg-green-500'
                        }`}
                        style={{ width: `${analysisResult.risk_score}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-white">
                      {analysisResult.risk_score}/100
                    </span>
                  </div>
                </div>
              )}

              {analysisResult.details && (
                <div>
                  <h3 className="text-sm font-medium text-gray-300 mb-2">Detailed Analysis</h3>
                  <div className="bg-gray-800/50 rounded-lg p-4">
                    <pre className="text-xs text-gray-300 whitespace-pre-wrap overflow-x-auto">
                      {JSON.stringify(analysisResult.details, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {analysisResult.recommendations && (
                <div>
                  <h3 className="text-sm font-medium text-gray-300 mb-2">Recommendations</h3>
                  <ul className="space-y-2">
                    {analysisResult.recommendations.map((rec, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-gray-100">
                        <AlertCircle className="w-4 h-4 text-orange-400 flex-shrink-0 mt-0.5" />
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Analysis History */}
        {analysisHistory.length > 0 && (
          <div className="bg-gray-900/50 rounded-lg p-6 border border-gray-800">
            <h2 className="text-lg font-semibold text-white mb-4">Recent Analyses</h2>
            <div className="space-y-2">
              {analysisHistory.slice(0, 10).map((item, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-gray-800/50 rounded-lg hover:bg-gray-800 transition-colors cursor-pointer"
                  onClick={() => {
                    setInput(item.input || '');
                    setSelectedBlockchain(item.blockchain || 'ethereum');
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 truncate">
                      <p className="text-sm text-gray-300 font-medium truncate">
                        {item.input}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {item.blockchain} • {new Date(item.timestamp).toLocaleString()}
                      </p>
                    </div>
                    {item.risk_score !== undefined && (
                      <div className="ml-4">
                        <span className={`text-xs font-medium px-2 py-1 rounded ${
                          item.risk_score > 70
                            ? 'bg-red-900/50 text-red-400'
                            : item.risk_score > 40
                            ? 'bg-yellow-900/50 text-yellow-400'
                            : 'bg-green-900/50 text-green-400'
                        }`}>
                          Risk: {item.risk_score}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BlockchainAnalyzer;
