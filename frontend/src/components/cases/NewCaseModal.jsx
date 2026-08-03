import React, { useState } from 'react';

const NewCaseModal = ({ isOpen, onClose, onCreate }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmit, setIsSubmit] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;
    setIsSubmit(true);
    try {
      await onCreate({ title, description });
      setTitle('');
      setDescription('');
    } finally {
      setIsSubmit(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-950/80 backdrop-blur-sm">
      <div className="relative w-full max-w-md bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl p-6 overflow-hidden">
        <h3 className="text-lg font-bold text-white mb-4">Launch Forensic Case Container</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-gray-300 text-xs font-semibold uppercase tracking-wider mb-2">
              Case Title
            </label>
            <input
              type="text"
              required
              placeholder="APT29 Lateral Movement Analysis"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent text-sm"
            />
          </div>
          <div>
            <label className="block text-gray-300 text-xs font-semibold uppercase tracking-wider mb-2">
              Description
            </label>
            <textarea
              rows="3"
              placeholder="Analysis of process execution logs, domain connects, and remote command injection patterns."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 bg-gray-950 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent text-sm"
            />
          </div>
          <div className="flex gap-3 justify-end pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-700 hover:border-gray-500 text-gray-300 rounded-lg text-xs font-semibold hover:text-white transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmit}
              className="px-4 py-2 bg-accent hover:bg-accent-hover text-white rounded-lg text-xs font-semibold transition-all cursor-pointer disabled:opacity-50"
            >
              {isSubmit ? 'Creating...' : 'Initialize'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default NewCaseModal;
