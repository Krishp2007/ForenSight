import React, { useState } from 'react';
import { 
  FileText, Copy, Check, HardDrive, RefreshCw, 
  Inbox, AlertTriangle, Trash2 
} from 'lucide-react';
import apiClient from '../../services/apiClient';

const EvidenceRepositoryList = ({ evidenceList, onDeleteSuccess }) => {
  const [copiedHash, setCopiedHash] = useState('');
  const [deletingId, setDeletingId] = useState(null);
  const [deleteError, setDeleteError] = useState('');

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(text);
    setTimeout(() => setCopiedHash(''), 2050);
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleDelete = async (evidenceId, filename) => {
    const message = `Are you sure you want to permanently delete "${filename}"?\n\nThis will remove the file from storage and clear all associated events from the timeline, threat map, and similarity engines.`;
    if (!window.confirm(message)) {
      return;
    }
    
    setDeletingId(evidenceId);
    setDeleteError('');
    try {
      await apiClient.delete(`/evidence/${evidenceId}`);
      if (onDeleteSuccess) {
        await onDeleteSuccess();
      }
    } catch (err) {
      console.error("Failed to delete evidence file", err);
      setDeleteError(err.response?.data?.detail || 'Failed to delete evidence.');
    } finally {
      setDeletingId(null);
    }
  };

  const isParsingActive = evidenceList.some(
    (ev) => ev.status === 'uploaded' || ev.status === 'queued' || ev.status === 'parsing'
  );

  return (
    <div className="bg-gray-900/60 border border-gray-800 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-md">
      <div className="p-5 border-b border-gray-800 bg-gray-900/80 flex items-center justify-between">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <HardDrive className="w-4 h-4 text-accent" />
          Case Evidence Repository
        </h3>
        <div className="flex items-center gap-2">
          {isParsingActive && (
            <span className="flex items-center gap-1.5 text-[10px] font-semibold text-accent animate-pulse font-mono bg-accent/15 px-2 py-0.5 border border-accent/20 rounded">
              <RefreshCw className="w-3 h-3 animate-spin" />
              PARSING LOGS...
            </span>
          )}
          <span className="text-[10px] font-bold text-gray-500 uppercase">
            Total Files: {evidenceList.length}
          </span>
        </div>
      </div>

      {deleteError && (
        <div className="mx-5 mt-5 p-3 bg-red-950/20 border border-red-905/30 text-red-400 text-xs rounded-xl flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-red-500" />
          <span>{deleteError}</span>
        </div>
      )}

      {evidenceList.length === 0 ? (
        <div className="py-24 text-center">
          <Inbox className="w-10 h-10 text-gray-700 mx-auto mb-4" />
          <h4 className="text-gray-400 font-bold text-xs">No Evidence Logs Ingested</h4>
          <p className="text-gray-500 text-[11px] mt-1">Upload sandbox artifacts to start structural forensic pipeline parsing.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left">
            <thead>
              <tr className="border-b border-gray-800 bg-gray-900/30 text-gray-400 text-[10px] font-bold uppercase tracking-wider">
                <th className="p-4">File Name</th>
                <th className="p-4">Type</th>
                <th className="p-4">Size</th>
                <th className="p-4">SHA-256 Checksum</th>
                <th className="p-4">Lifecycle State</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {evidenceList.map((e) => (
                <tr key={e.id} className="hover:bg-gray-800/20 text-xs text-gray-300">
                  <td className="p-4 font-bold text-white max-w-[200px] truncate" title={e.filename}>
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-blue-400 shrink-0" />
                      {e.filename}
                    </div>
                  </td>
                  <td className="p-4 font-mono text-[10px] uppercase text-gray-400">{e.file_type}</td>
                  <td className="p-4 text-gray-400">{formatBytes(e.size_bytes)}</td>
                  <td className="p-4">
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono text-[10px] text-gray-500" title={e.sha256}>
                        {e.sha256.slice(0, 8)}...{e.sha256.slice(-8)}
                      </span>
                      <button
                        onClick={() => copyToClipboard(e.sha256)}
                        className="text-gray-600 hover:text-white p-1 rounded hover:bg-gray-800 transition-all cursor-pointer"
                      >
                        {copiedHash === e.sha256 ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
                      </button>
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[9px] px-2 py-0.5 border rounded-full font-mono uppercase tracking-wider font-semibold ${
                          e.status === 'parsed'
                            ? 'bg-green-950/20 border-green-500/40 text-green-400'
                            : e.status === 'failed'
                              ? 'bg-red-950/20 border-red-500/40 text-red-400'
                              : e.status === 'parsing'
                                ? 'bg-accent/15 border-accent/30 text-accent animate-pulse'
                                : 'bg-gray-850 border-gray-700 text-gray-400'
                        }`}
                      >
                        {e.status}
                      </span>
                      {e.error_message && (
                        <AlertTriangle 
                          className="w-3.5 h-3.5 text-red-500 cursor-help" 
                          title={e.error_message}
                        />
                      )}
                    </div>
                  </td>
                  <td className="p-4 text-right">
                    <button
                      disabled={deletingId === e.id}
                      onClick={() => handleDelete(e.id, e.filename)}
                      className={`text-gray-500 hover:text-red-400 p-1.5 rounded-lg hover:bg-red-500/10 transition-all cursor-pointer inline-flex items-center justify-center ${
                        deletingId === e.id ? 'text-red-400 animate-pulse' : ''
                      }`}
                      title="Delete Evidence File"
                    >
                      {deletingId === e.id ? (
                        <RefreshCw className="w-4 h-4 animate-spin" />
                      ) : (
                        <Trash2 className="w-4 h-4" />
                      )}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default EvidenceRepositoryList;
