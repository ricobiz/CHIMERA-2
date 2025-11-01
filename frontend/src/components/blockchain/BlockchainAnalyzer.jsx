import React, { useState } from 'react';
import { X, Search, TrendingUp, AlertTriangle, Clock, DollarSign, Link as LinkIcon, Activity } from 'lucide-react';
import { Button } from '../ui/button';
import { toast } from '../../hooks/use-toast';

const BlockchainAnalyzer = ({ onClose }) => {
  const [address, setAddress] = useState('');
  const [blockchain, setBlockchain] = useState('ethereum');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisHistory, setAnalysisHistory] = useState([]);

  const handleAnalyze = async () => {
    if (!address.trim()) {
      toast({
        title: "Input Required",
        description: "Please enter a blockchain address or transaction hash.",
        variant: "destructive"
      });
      return;
    }

    setIsAnalyzing(true);
    
    try {
      // Simulate API call for blockchain analysis
      // In production, this would call your backend API
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const mockResult = {
        address: address,
        blockchain: blockchain,
        timestamp: new Date().toISOString(),
        balance: '15.47 ETH',
        totalTransactions: 1247,
        firstSeen: '2021-03-15',
        lastActivity: '2024-10-28',
        riskScore: 'Low',
        labels: ['Exchange', 'Active Trader'],
        topInteractions: [
          { address: '0x742d35...', count: 45, type: 'DeFi Protocol' },
          { address: '0x8f3a21...', count: 32, type: 'Token Contract' },
          { address: '0x1c4e7b...', count: 28, type: 'Exchange' }
        ],
        recentTransactions: [
          { hash: '0xabc123...', value: '2.5 ETH', timestamp: '2h ago', type: 'out' },
          { hash: '0xdef456...', value: '1.2 ETH', timestamp: '5h ago', type: 'in' },
          { hash: '0xghi789...', value: '0.8 ETH', timestamp: '1d ago', type: 'out' }
        ],
        tokens: [
          { symbol: 'USDT', balance: '45,230.50', value: '$45,230.50' },
          { symbol: 'USDC', balance: '12,500.00', value: '$12,500.00' },
          { symbol: 'DAI', balance: '8,750.25', value: '$8,750.25' }
        ]
      };

      setAnalysisResult(mockResult);
      setAnalysisHistory(prev => [mockResult, ...prev.slice(0, 9)]);
      
      toast({
        title: "Analysis Complete",
        description: "Blockchain OSINT analysis finished successfully.",
      });
    } catch (error) {
      toast({
        title: "Analysis Failed",
        description: "Failed to analyze blockchain data. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getRiskColor = (risk) => {
    switch(risk.toLowerCase()) {
      case 'low': return 'text-green-500';
      case 'medium': return 'text-yellow-500';
      case 'high': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  return (
    <div className="fixed inset-0 bg-black/95 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-xl w-full max-w-7xl h-[90vh] flex flex-col border border-orange-500/20 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-amber-500 rounded-lg flex items-center justify-center">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">Blockchain OSINT Analyzer</h2>
              <p className="text-sm text-gray-400">Advanced blockchain intelligence and transaction analysis</p>
            </div>
          </div>
          <Button
            onClick={onClose}
            variant="ghost"
            size="icon"
            className="text-gray-400 hover:text-white hover:bg-gray-800"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        <div className="flex-1 overflow-hidden flex gap-6 p-6">
          {/* Left Panel - Analysis Input */}
          <div className="w-1/3 flex flex-col gap-4">
            <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Search className="w-5 h-5 text-orange-500" />
                Analysis Input
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Blockchain Network
                  </label>
                  <select
                    value={blockchain}
                    onChange={(e) => setBlockchain(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-orange-500"
                    disabled={isAnalyzing}
                  >
                    <option value="ethereum">Ethereum</option>
                    <option value="bitcoin">Bitcoin</option>
                    <option value="binance">Binance Smart Chain</option>
                    <option value="polygon">Polygon</option>
                    <option value="arbitrum">Arbitrum</option>
                    <option value="optimism">Optimism</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Address or Transaction Hash
                  </label>
                  <textarea
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    placeholder="Enter wallet address or transaction hash..."
                    className="w-full bg-gray-900 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-orange-500 resize-none"
                    rows={3}
                    disabled={isAnalyzing}
                  />
                </div>

                <Button
                  onClick={handleAnalyze}
                  disabled={isAnalyzing}
                  className="w-full bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-semibold py-3 rounded-lg transition-all"
                >
                  {isAnalyzing ? (
                    <span className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Analyzing...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <Search className="w-4 h-4" />
                      Analyze
                    </span>
                  )}
                </Button>
              </div>
            </div>

            {/* Analysis History */}
            <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700 flex-1 overflow-y-auto">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Clock className="w-5 h-5 text-orange-500" />
                Recent Analyses
              </h3>
              
              {analysisHistory.length === 0 ? (
                <p className="text-gray-500 text-sm text-center py-8">
                  No analysis history yet
                </p>
              ) : (
                <div className="space-y-2">
                  {analysisHistory.map((item, idx) => (
                    <div
                      key={idx}
                      onClick={() => setAnalysisResult(item)}
                      className="bg-gray-900/50 rounded-lg p-3 cursor-pointer hover:bg-gray-900 transition-all border border-gray-700 hover:border-orange-500/50"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-orange-500 uppercase">
                          {item.blockchain}
                        </span>
                        <span className="text-xs text-gray-500">
                          {new Date(item.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="text-sm text-white font-mono truncate">
                        {item.address}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Panel - Analysis Results */}
          <div className="flex-1 bg-gray-800/50 rounded-lg p-6 border border-gray-700 overflow-y-auto">
            {!analysisResult ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <Activity className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-gray-400 mb-2">
                    No Analysis Yet
                  </h3>
                  <p className="text-gray-500">
                    Enter an address or transaction hash to begin analysis
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Overview */}
                <div>
                  <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-orange-500" />
                    Analysis Overview
                  </h3>
                  
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                      <div className="flex items-center gap-2 mb-2">
                        <DollarSign className="w-4 h-4 text-green-500" />
                        <span className="text-sm text-gray-400">Balance</span>
                      </div>
                      <div className="text-2xl font-bold text-white">
                        {analysisResult.balance}
                      </div>
                    </div>
                    
                    <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                      <div className="flex items-center gap-2 mb-2">
                        <LinkIcon className="w-4 h-4 text-blue-500" />
                        <span className="text-sm text-gray-400">Transactions</span>
                      </div>
                      <div className="text-2xl font-bold text-white">
                        {analysisResult.totalTransactions.toLocaleString()}
                      </div>
                    </div>
                    
                    <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                      <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle className="w-4 h-4 text-yellow-500" />
                        <span className="text-sm text-gray-400">Risk Score</span>
                      </div>
                      <div className={`text-2xl font-bold ${getRiskColor(analysisResult.riskScore)}`}>
                        {analysisResult.riskScore}
                      </div>
                    </div>
                    
                    <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                      <div className="flex items-center gap-2 mb-2">
                        <Clock className="w-4 h-4 text-purple-500" />
                        <span className="text-sm text-gray-400">Last Activity</span>
                      </div>
                      <div className="text-lg font-bold text-white">
                        {analysisResult.lastActivity}
                      </div>
                    </div>
                  </div>

                  <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                    <div className="text-sm text-gray-400 mb-1">Address</div>
                    <div className="text-white font-mono text-sm break-all">
                      {analysisResult.address}
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                      <span>First Seen: {analysisResult.firstSeen}</span>
                      <span>•</span>
                      <span>Network: {analysisResult.blockchain}</span>
                    </div>
                  </div>
                </div>

                {/* Labels */}
                {analysisResult.labels && analysisResult.labels.length > 0 && (
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-3">Labels & Tags</h4>
                    <div className="flex flex-wrap gap-2">
                      {analysisResult.labels.map((label, idx) => (
                        <span
                          key={idx}
                          className="bg-orange-500/20 text-orange-400 px-3 py-1 rounded-full text-sm border border-orange-500/30"
                        >
                          {label}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Top Interactions */}
                {analysisResult.topInteractions && (
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-3">Top Interactions</h4>
                    <div className="space-y-2">
                      {analysisResult.topInteractions.map((interaction, idx) => (
                        <div
                          key={idx}
                          className="bg-gray-900/50 rounded-lg p-3 border border-gray-700 flex items-center justify-between"
                        >
                          <div>
                            <div className="text-white font-mono text-sm">{interaction.address}</div>
                            <div className="text-xs text-gray-500">{interaction.type}</div>
                          </div>
                          <div className="text-orange-500 font-semibold">{interaction.count} txns</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Token Holdings */}
                {analysisResult.tokens && (
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-3">Token Holdings</h4>
                    <div className="space-y-2">
                      {analysisResult.tokens.map((token, idx) => (
                        <div
                          key={idx}
                          className="bg-gray-900/50 rounded-lg p-3 border border-gray-700 flex items-center justify-between"
                        >
                          <div>
                            <div className="text-white font-semibold">{token.symbol}</div>
                            <div className="text-sm text-gray-400">{token.balance}</div>
                          </div>
                          <div className="text-green-500 font-semibold">{token.value}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recent Transactions */}
                {analysisResult.recentTransactions && (
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-3">Recent Transactions</h4>
                    <div className="space-y-2">
                      {analysisResult.recentTransactions.map((tx, idx) => (
                        <div
                          key={idx}
                          className="bg-gray-900/50 rounded-lg p-3 border border-gray-700"
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-white font-mono text-sm">{tx.hash}</span>
                            <span className={`text-sm font-semibold ${tx.type === 'in' ? 'text-green-500' : 'text-red-500'}`}>
                              {tx.type === 'in' ? '+' : '-'} {tx.value}
                            </span>
                          </div>
                          <div className="text-xs text-gray-500">{tx.timestamp}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BlockchainAnalyzer;
