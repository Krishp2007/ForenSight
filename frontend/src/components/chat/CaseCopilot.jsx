import React, { useState, useEffect, useRef } from 'react';
import apiClient from '../../services/apiClient';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { Bot, RefreshCw, Trash2 } from 'lucide-react';

const CaseCopilot = ({ caseId }) => {
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem(`copilot_chat_${caseId}`);
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (e) {
      console.error("Failed to parse saved chat history:", e);
    }
    return [
      {
        id: 'welcome',
        sender: 'copilot',
        text: 'Greetings Analyst. I am the ForenSight AI Copilot. I have mapped the telemetry of active cases and can explain indicators of compromise (IoC), process logs, and outline recommendations. How may I assist?'
      }
    ];
  });
  const [inputVal, setInputVal] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorWord, setErrorWord] = useState('');

  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Sync messages from localStorage when caseId changes
  useEffect(() => {
    try {
      const saved = localStorage.getItem(`copilot_chat_${caseId}`);
      if (saved) {
        setMessages(JSON.parse(saved));
      } else {
        setMessages([
          {
            id: 'welcome',
            sender: 'copilot',
            text: 'Greetings Analyst. I am the ForenSight AI Copilot. I have mapped the telemetry of active cases and can explain indicators of compromise (IoC), process logs, and outline recommendations. How may I assist?'
          }
        ]);
      }
    } catch (e) {
      console.error("Failed to load chat history:", e);
    }
    setErrorWord('');
  }, [caseId]);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(`copilot_chat_${caseId}`, JSON.stringify(messages));
    } catch (e) {
      console.error("Failed to save chat history:", e);
    }
  }, [messages, caseId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputVal.trim() || loading) return;

    const userPrompt = inputVal;
    setErrorWord('');
    setInputVal('');

    // Prepend user message
    const userMsg = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: userPrompt
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await apiClient.post(`/cases/${caseId}/copilot`, {
        question: userPrompt
      });

      const copilotResponse = {
        id: `copilot-${Date.now()}`,
        sender: 'copilot',
        text: res.data.analysis || 'No analysis details generated.'
      };
      setMessages((prev) => [...prev, copilotResponse]);
    } catch (err) {
      setErrorWord(err.response?.data?.detail || 'AI Copilot querying failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleClearChat = () => {
    if (!window.confirm("Confirm clearing this session's AI conversation log?")) return;
    setMessages([
      {
        id: 'welcome',
        sender: 'copilot',
        text: 'Greetings Analyst. I am the ForenSight AI Copilot. I have mapped the telemetry of active cases and can explain indicators of compromise (IoC), process logs, and outline recommendations. How may I assist?'
      }
    ]);
    setErrorWord('');
  };

  return (
    <div className="bg-gray-900/60 border border-gray-805 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-md flex flex-col h-[650px]">
      {/* Header operations row */}
      <div className="p-4 border-b border-gray-800 bg-gray-901 flex items-center justify-between">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <Bot className="w-4 h-4 text-accent animate-pulse" />
          Antigravity AI Copilot Workbench
        </h3>
        <button
          onClick={handleClearChat}
          className="p-1.5 border border-gray-808 bg-gray-955 hover:bg-gray-850 hover:text-white rounded text-gray-500 transition-all cursor-pointer"
          title="Clear Conversation thread"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Messages Thread Log Viewport */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((m) => (
          <ChatMessage key={m.id} msg={m} />
        ))}

        {loading && (
          <div className="flex gap-4 p-5 rounded-2xl border bg-gray-900/30 border-gray-850/60">
            <div className="w-8 h-8 rounded-lg shrink-0 flex items-center justify-center border bg-accent/20 border-accent/40 text-accent">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <div className="flex-1 space-y-2">
              <span className="text-[10px] font-bold tracking-wider uppercase text-gray-500">
                AI Copilot
              </span>
              <div className="flex items-center gap-1.5 text-xs text-gray-450 mt-1">
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-accent" />
                Thinking, compiling evidence vectors...
              </div>
            </div>
          </div>
        )}

        {errorWord && (
          <div className="p-4 bg-red-950/20 border border-red-900/30 text-red-00 text-xs rounded-xl text-center">
            {errorWord}
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Dedicated Input Panel area */}
      <div className="p-6 border-t border-gray-800 bg-gray-901">
        <ChatInput
          value={inputVal}
          onChange={setInputVal}
          onSubmit={handleSubmit}
          disabled={loading}
          setPrompt={setInputVal}
        />
      </div>
    </div>
  );
};

export default CaseCopilot;
