import React, { useState } from 'react';
import apiClient from '../../services/apiClient';
import { Upload } from 'lucide-react';

const EvidenceIngestionPanel = ({ caseId, evidenceList, onUploadSuccess }) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadingState, setUploadingState] = useState(''); // '', 'calculating_hash', 'uploading', 'done', 'error'
  const [uploadError, setUploadError] = useState('');

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      processSelectedFile(e.target.files[0]);
    }
  };

  // Client Side SHA-256 Hash Computation using Web Crypto API
  const calculateSHA256 = async (file) => {
    const arrayBuffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  };

  const processSelectedFile = async (file) => {
    setUploadError('');
    setUploadingState('calculating_hash');
    setUploadProgress(0);

    try {
      const sha256 = await calculateSHA256(file);
      
      // Local check
      if (evidenceList.some(ev => ev.sha256 === sha256)) {
        throw new Error('This exact file hash has already been ingested.');
      }
      
      setUploadingState('uploading');
      
      // Dispatch multipart stream
      const formData = new FormData();
      formData.append('file', file);

      await apiClient.post(`/cases/${caseId}/evidence`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        }
      });

      setUploadingState('done');
      onUploadSuccess();
      
      // Clear state indicator
      setTimeout(() => setUploadingState(''), 3000);
    } catch (err) {
      setUploadingState('error');
      setUploadError(err.message || err.response?.data?.detail || 'Ingestion upload failed.');
    }
  };

  return (
    <div className="bg-gray-900/40 border border-gray-850 p-6 rounded-2xl backdrop-blur-md space-y-4">
      <div>
        <h3 className="text-sm font-bold text-white">Ingest Forensic Artifacts</h3>
        <p className="text-gray-400 text-[11px] mt-1 leading-normal">
          Drag and drop EVTX Windows security logs, PCAP network traffic capture dumps, malware CSV logs, or JSON threat arrays directly into the sandbox.
        </p>
      </div>

      {/* Drag Area */}
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer relative ${
          dragActive
            ? 'border-accent bg-accent/5'
            : 'border-gray-800 hover:border-gray-700 bg-gray-955/40'
        }`}
      >
        <input
          type="file"
          id="evidence-file-input"
          onChange={handleFileChange}
          className="hidden"
          disabled={uploadingState === 'uploading' || uploadingState === 'calculating_hash'}
        />
        <label htmlFor="evidence-file-input" className="cursor-pointer space-y-3 block w-full">
          <Upload className="w-10 h-10 text-gray-500 mx-auto" />
          <div className="text-xs text-gray-300">
            <span className="font-semibold text-accent">Select file</span> or drop logs here
          </div>
          <div className="text-[10px] text-gray-500">Max size 250MB (EVTX, CSV, PCAP, JSON)</div>
        </label>
      </div>

      {/* Progress Indicators */}
      {uploadingState && (
        <div className="p-3 bg-gray-955 border border-gray-800 rounded-xl space-y-2">
          <div className="flex justify-between items-center text-xs">
            <span className="text-gray-400 font-medium">
              {uploadingState === 'calculating_hash' && 'Calculating SHA-256...'}
              {uploadingState === 'uploading' && 'Ingesting file...'}
              {uploadingState === 'done' && 'Upload succeeded! Ingest job active.'}
              {uploadingState === 'error' && 'Ingestion failed'}
            </span>
            {uploadingState === 'uploading' && (
              <span className="text-accent font-bold font-mono">{uploadProgress}%</span>
            )}
          </div>
          {uploadingState === 'uploading' && (
            <div className="w-full bg-gray-800 h-1.5 rounded-full overflow-hidden">
              <div 
                className="bg-accent h-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          )}
          {uploadingState === 'calculating_hash' && (
            <div className="w-full bg-gray-805 h-1.5 rounded-full overflow-hidden">
              <div className="bg-accent h-full w-1/3 rounded-full animate-ping" />
            </div>
          )}
          {uploadError && (
            <p className="text-[10px] text-red-400 mt-1 leading-normal">{uploadError}</p>
          )}
        </div>
      )}
    </div>
  );
};

export default EvidenceIngestionPanel;
