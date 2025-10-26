import React, { useState } from 'react';
import { Upload, FileText, AlertTriangle, CheckCircle, XCircle, Shield } from 'lucide-react';

const DocumentVerification = ({ onClose }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [documentType, setDocumentType] = useState('general');
  const [additionalContext, setAdditionalContext] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file) => {
    if (file.type.startsWith('image/') || file.type === 'application/pdf') {
      setSelectedFile(file);
      setVerificationResult(null);
    } else {
      alert('Please upload an image or PDF file');
    }
  };

  const analyzeDocument = async () => {
    if (!selectedFile) return;

    setIsAnalyzing(true);
    
    try {
      // Convert file to base64
      const base64 = await fileToBase64(selectedFile);
      
      // Call backend API
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/document-verification/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_base64: base64.split(',')[1], // Remove data:image/jpeg;base64, prefix
          document_type: documentType,
          additional_context: additionalContext
        })
      });

      const result = await response.json();
      setVerificationResult(result);
      
    } catch (error) {
      console.error('Verification error:', error);
      alert('Verification failed. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result);
      reader.onerror = error => reject(error);
    });
  };

  const getVerdictColor = (verdict) => {
    switch (verdict) {
      case 'AUTHENTIC': return 'text-green-400';
      case 'SUSPICIOUS': return 'text-yellow-400';
      case 'LIKELY_FAKE': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getVerdictIcon = (verdict) => {
    switch (verdict) {
      case 'AUTHENTIC': return <CheckCircle className="w-8 h-8 text-green-400" />;
      case 'SUSPICIOUS': return <AlertTriangle className="w-8 h-8 text-yellow-400" />;
      case 'LIKELY_FAKE': return <XCircle className="w-8 h-8 text-red-400" />;
      default: return <Shield className="w-8 h-8 text-gray-400" />;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#0f0f10]">
      {/* Header */}
      <div className="w-full">
        <div className="flex items-center justify-between p-4 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <Shield className="w-6 h-6 text-purple-400" />
            <h1 className="text-xl font-semibold text-white">Document Verification</h1>
            <span className="px-2 py-1 text-xs bg-purple-600/20 text-purple-400 rounded border border-purple-500/30">
              AI-Powered Fraud Detection
            </span>
          </div>
          <button
            onClick={onClose}
            className="px-2 md:px-3 py-1.5 md:py-2 rounded-lg bg-gray-800/50 hover:bg-gray-700/50 border border-gray-700 text-gray-300 transition-colors text-sm md:text-base"
          >
            ← Back
          </button>
        </div>

        <div className="p-6 overflow-y-auto" style={{ height: 'calc(100vh - 73px)' }}>
          <div className="max-w-6xl mx-auto space-y-6">
            
            {/* Upload Section */}
            {!verificationResult && (
              <div className="bg-gray-900/50 rounded-lg border border-gray-800 p-6">
                <h2 className="text-lg font-semibold text-white mb-4">Upload Document for Verification</h2>
                
                {/* Drag & Drop Zone */}
                <div
                  className={`border-2 border-dashed rounded-lg p-12 text-center transition-all ${
                    dragActive 
                      ? 'border-purple-500 bg-purple-500/10' 
                      : 'border-gray-700 bg-gray-800/30 hover:border-gray-600'
                  }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  {selectedFile ? (
                    <div className="space-y-4">
                      <FileText className="w-16 h-16 text-purple-400 mx-auto" />
                      <div>
                        <p className="text-white font-medium">{selectedFile.name}</p>
                        <p className="text-gray-400 text-sm">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                      </div>
                      <button
                        onClick={() => setSelectedFile(null)}
                        className="text-sm text-gray-400 hover:text-white transition-colors"
                      >
                        Remove file
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <Upload className="w-16 h-16 text-gray-500 mx-auto" />
                      <div>
                        <p className="text-white font-medium mb-1">
                          Drag & drop your document here
                        </p>
                        <p className="text-gray-400 text-sm">or</p>
                      </div>
                      <label className="inline-block">
                        <input
                          type="file"
                          className="hidden"
                          accept="image/*,.pdf"
                          onChange={handleFileInput}
                        />
                        <span className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg cursor-pointer transition-colors inline-block">
                          Browse Files
                        </span>
                      </label>
                      <p className="text-gray-500 text-xs">
                        Supported: Images (JPG, PNG) and PDF up to 10MB
                      </p>
                    </div>
                  )}
                </div>

                {/* Document Type Selection */}
                <div className="mt-6 grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Document Type</label>
                    <select
                      value={documentType}
                      onChange={(e) => setDocumentType(e.target.value)}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-purple-500 focus:outline-none"
                    >
                      <option value="general">General Document</option>
                      <option value="bank_statement">Bank Statement</option>
                      <option value="passport">Passport/ID</option>
                      <option value="invoice">Invoice/Receipt</option>
                      <option value="contract">Contract/Agreement</option>
                      <option value="certificate">Certificate</option>
                      <option value="financial">Financial Document</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Additional Context (Optional)</label>
                    <input
                      type="text"
                      value={additionalContext}
                      onChange={(e) => setAdditionalContext(e.target.value)}
                      placeholder="e.g., Expected amount, date range..."
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-600 focus:border-purple-500 focus:outline-none"
                    />
                  </div>
                </div>

                {/* Analyze Button */}
                <button
                  onClick={analyzeDocument}
                  disabled={!selectedFile || isAnalyzing}
                  className="w-full mt-6 px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 disabled:from-gray-700 disabled:to-gray-700 text-white font-medium rounded-lg transition-all disabled:cursor-not-allowed"
                >
                  {isAnalyzing ? (
                    <span className="flex items-center justify-center gap-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      Analyzing with AI models...
                    </span>
                  ) : (
                    'Verify Document Authenticity'
                  )}
                </button>
              </div>
            )}

            {/* Results Section */}
            {verificationResult && (
              <div className="space-y-6">
                {/* Verdict Card */}
                <div className="bg-gray-900/50 rounded-lg border border-gray-800 p-6">
                  <div className="flex items-start gap-4">
                    {getVerdictIcon(verificationResult.verdict)}
                    <div className="flex-1">
                      <h2 className={`text-2xl font-bold ${getVerdictColor(verificationResult.verdict)}`}>
                        {verificationResult.verdict.replace('_', ' ')}
                      </h2>
                      <p className="text-gray-400 mt-1">
                        Fraud Probability: <span className="text-white font-semibold">{verificationResult.fraud_probability}%</span>
                      </p>
                      <p className="text-gray-400">
                        Analysis Confidence: <span className="text-white font-semibold">{verificationResult.confidence_score}%</span>
                      </p>
                    </div>
                  </div>

                  {/* Fraud Probability Bar */}
                  <div className="mt-4">
                    <div className="w-full h-3 bg-gray-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all ${
                          verificationResult.fraud_probability >= 70 ? 'bg-red-500' :
                          verificationResult.fraud_probability >= 40 ? 'bg-yellow-500' :
                          'bg-green-500'
                        }`}
                        style={{ width: `${verificationResult.fraud_probability}%` }}
                      ></div>
                    </div>
                  </div>
                </div>

                {/* Multi-Model Analysis */}
                {verificationResult.multi_model_analysis && (
                  <div className="bg-gray-900/50 rounded-lg border border-gray-800 p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">🤖 Dual-Model Verification</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-gray-800/50 rounded-lg p-4">
                        <p className="text-sm text-gray-400 mb-2">{verificationResult.multi_model_analysis.primary_model.name}</p>
                        <p className={`text-lg font-semibold ${getVerdictColor(verificationResult.multi_model_analysis.primary_model.verdict)}`}>
                          {verificationResult.multi_model_analysis.primary_model.verdict}
                        </p>
                        <p className="text-sm text-gray-400 mt-1">
                          {verificationResult.multi_model_analysis.primary_model.fraud_probability}% fraud probability
                        </p>
                      </div>
                      <div className="bg-gray-800/50 rounded-lg p-4">
                        <p className="text-sm text-gray-400 mb-2">{verificationResult.multi_model_analysis.secondary_model.name}</p>
                        <p className={`text-lg font-semibold ${getVerdictColor(verificationResult.multi_model_analysis.secondary_model.verdict)}`}>
                          {verificationResult.multi_model_analysis.secondary_model.verdict}
                        </p>
                        <p className="text-sm text-gray-400 mt-1">
                          {verificationResult.multi_model_analysis.secondary_model.fraud_probability}% fraud probability
                        </p>
                      </div>
                    </div>
                    <p className="text-sm text-gray-400 mt-4">
                      Agreement Level: <span className="text-white font-semibold">{verificationResult.multi_model_analysis.agreement_level}%</span>
                    </p>
                  </div>
                )}

                {/* Red Flags */}
                {verificationResult.red_flags && verificationResult.red_flags.length > 0 && (
                  <div className="bg-red-900/20 border border-red-800 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-red-400 mb-3">🚨 Red Flags Detected</h3>
                    <ul className="space-y-2">
                      {verificationResult.red_flags.map((flag, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-gray-300">
                          <span className="text-red-400 mt-1">•</span>
                          <span>{flag}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Authenticity Indicators */}
                {verificationResult.authenticity_indicators && verificationResult.authenticity_indicators.length > 0 && (
                  <div className="bg-green-900/20 border border-green-800 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-green-400 mb-3">✓ Authenticity Indicators</h3>
                    <ul className="space-y-2">
                      {verificationResult.authenticity_indicators.map((indicator, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-gray-300">
                          <span className="text-green-400 mt-1">•</span>
                          <span>{indicator}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Detailed Analysis */}
                {verificationResult.analysis_details && (
                  <div className="bg-gray-900/50 rounded-lg border border-gray-800 p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">📊 Detailed Analysis</h3>
                    <div className="space-y-4">
                      {Object.entries(verificationResult.analysis_details).map(([key, value]) => (
                        <div key={key} className="bg-gray-800/50 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="text-sm font-semibold text-gray-300 capitalize">
                              {key.replace(/_/g, ' ')}
                            </h4>
                            {value.score !== undefined && (
                              <span className={`text-sm font-semibold ${
                                value.score >= 70 ? 'text-green-400' :
                                value.score >= 40 ? 'text-yellow-400' :
                                'text-red-400'
                              }`}>
                                {value.score}/100
                              </span>
                            )}
                            {value.likelihood !== undefined && (
                              <span className={`text-sm font-semibold ${
                                value.likelihood <= 30 ? 'text-green-400' :
                                value.likelihood <= 60 ? 'text-yellow-400' :
                                'text-red-400'
                              }`}>
                                {value.likelihood}% likelihood
                              </span>
                            )}
                          </div>
                          {value.findings && (
                            <ul className="text-sm text-gray-400 space-y-1">
                              {value.findings.slice(0, 3).map((finding, idx) => (
                                <li key={idx}>• {finding}</li>
                              ))}
                            </ul>
                          )}
                          {value.indicators && (
                            <ul className="text-sm text-gray-400 space-y-1">
                              {value.indicators.slice(0, 3).map((indicator, idx) => (
                                <li key={idx}>• {indicator}</li>
                              ))}
                            </ul>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-blue-400 mb-3">💡 Recommendations</h3>
                  <div className="text-gray-300 whitespace-pre-line">
                    {verificationResult.recommendations}
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-4">
                  <button
                    onClick={() => {
                      setVerificationResult(null);
                      setSelectedFile(null);
                    }}
                    className="flex-1 px-6 py-3 bg-purple-600 hover:bg-purple-500 text-white font-medium rounded-lg transition-colors"
                  >
                    Verify Another Document
                  </button>
                  <button
                    onClick={() => {
                      // Download report as JSON
                      const dataStr = JSON.stringify(verificationResult, null, 2);
                      const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
                      const exportFileDefaultName = `verification-report-${Date.now()}.json`;
                      const linkElement = document.createElement('a');
                      linkElement.setAttribute('href', dataUri);
                      linkElement.setAttribute('download', exportFileDefaultName);
                      linkElement.click();
                    }}
                    className="px-6 py-3 bg-gray-800 hover:bg-gray-700 text-white font-medium rounded-lg transition-colors border border-gray-700"
                  >
                    Download Report
                  </button>
                </div>
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentVerification;
