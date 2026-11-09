import React, { useState, useRef, useEffect } from 'react';

// Chat Interface Component for ContextKeeper Dashboard
// Matches glass morphism design with dark theme
// WCAG AA compliant with keyboard navigation and screen reader support

const ChatInterface = () => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      content: 'Hello! I\'m your ContextKeeper Assistant. How can I help you today?',
      timestamp: new Date(Date.now() - 60000)
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Quick action buttons configuration
  const quickActions = [
    { id: 'status', label: 'Project Status', icon: '📊' },
    { id: 'events', label: 'Recent Events', icon: '🕒' },
    { id: 'help', label: 'Help', icon: '❓' }
  ];

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when panel expands
  useEffect(() => {
    if (isExpanded && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isExpanded]);

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    const newMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newMessage]);
    setInputValue('');

    // Simulate assistant typing
    setIsTyping(true);
    setTimeout(() => {
      setIsTyping(false);
      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: 'I understand your query. Let me help you with that information from the ContextKeeper knowledge base.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
    }, 2000);
  };

  const handleQuickAction = (actionId) => {
    const actionMessages = {
      status: 'Please show me the current project status and recent activity.',
      events: 'What are the latest events and changes in my projects?',
      help: 'How do I use ContextKeeper effectively?'
    };

    setInputValue(actionMessages[actionId]);
    inputRef.current?.focus();
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Intl.DateTimeFormat('en-AU', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    }).format(timestamp);
  };

  const TypingIndicator = () => (
    <div className="flex items-center space-x-1 p-3">
      <div className="flex space-x-1">
        <div className="w-2 h-2 bg-slate-400 rounded-full animate-pulse" style={{animationDelay: '0ms'}}></div>
        <div className="w-2 h-2 bg-slate-400 rounded-full animate-pulse" style={{animationDelay: '150ms'}}></div>
        <div className="w-2 h-2 bg-slate-400 rounded-full animate-pulse" style={{animationDelay: '300ms'}}></div>
      </div>
      <span className="text-xs text-slate-400 ml-2">Assistant is typing...</span>
    </div>
  );

  return (
    <>
      {/* Chat Panel */}
      <div
        className={`fixed top-0 right-0 h-full bg-slate-900/50 backdrop-blur-md border-l border-slate-800 transition-all duration-300 ease-in-out z-50 ${
          isExpanded ? 'w-[400px]' : 'w-0'
        } overflow-hidden`}
        role="dialog"
        aria-label="ContextKeeper Assistant Chat"
        aria-expanded={isExpanded}
      >
        {/* Chat Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900/80">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-br from-violet-500 to-purple-600 rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-bold">CK</span>
            </div>
            <div>
              <h2 className="text-white font-medium text-sm">ContextKeeper Assistant</h2>
              <p className="text-slate-400 text-xs">Always here to help</p>
            </div>
          </div>
          <button
            onClick={() => setIsExpanded(false)}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
            aria-label="Close chat"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 h-[calc(100vh-200px)]">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[280px] p-3 rounded-lg ${
                  message.type === 'user'
                    ? 'bg-violet-600 text-white ml-8'
                    : 'bg-slate-800 border border-slate-700 text-slate-100 mr-8'
                }`}
              >
                <p className="text-sm leading-relaxed">{message.content}</p>
                <p
                  className={`text-xs mt-1 ${
                    message.type === 'user' ? 'text-violet-200' : 'text-slate-400'
                  }`}
                >
                  {formatTimestamp(message.timestamp)}
                </p>
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-slate-800 border border-slate-700 rounded-lg mr-8">
                <TypingIndicator />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Actions */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/80">
          <div className="flex space-x-2 mb-3">
            {quickActions.map((action) => (
              <button
                key={action.id}
                onClick={() => handleQuickAction(action.id)}
                className="flex-1 p-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-violet-500 rounded-lg text-xs text-slate-300 hover:text-white transition-all duration-200 flex items-center justify-center space-x-1"
                aria-label={`Quick action: ${action.label}`}
              >
                <span>{action.icon}</span>
                <span className="hidden sm:inline">{action.label}</span>
              </button>
            ))}
          </div>

          {/* Input Area */}
          <div className="flex space-x-2">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything about your projects..."
                className="w-full p-3 bg-slate-800 border border-slate-700 focus:border-violet-500 rounded-lg text-white placeholder-slate-400 resize-none h-12 focus:outline-none focus:ring-2 focus:ring-violet-500/20 transition-all"
                rows="1"
                aria-label="Type your message"
              />
            </div>
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim()}
              className="p-3 bg-violet-600 hover:bg-violet-700 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-violet-500/20"
              aria-label="Send message"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Chat Toggle Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={`fixed bottom-6 right-6 p-4 bg-gradient-to-br from-violet-600 to-purple-700 hover:from-violet-700 hover:to-purple-800 text-white rounded-full shadow-2xl hover:shadow-violet-500/25 transition-all duration-300 z-40 focus:outline-none focus:ring-2 focus:ring-violet-500/20 ${
          isExpanded ? 'scale-0' : 'scale-100'
        }`}
        aria-label={isExpanded ? 'Close chat' : 'Open chat assistant'}
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      </button>

      {/* Mobile Backdrop */}
      {isExpanded && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 md:hidden"
          onClick={() => setIsExpanded(false)}
          aria-hidden="true"
        />
      )}

      {/* Custom Styles */}
      <style jsx>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 1; }
        }
        .animate-pulse {
          animation: pulse 1.5s ease-in-out infinite;
        }

        /* Mobile responsiveness */
        @media (max-width: 768px) {
          .fixed.right-0.w-\\[400px\\] {
            width: 100vw !important;
          }
        }

        /* Smooth transitions */
        .transition-all {
          transition-property: all;
          transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
        }

        /* Focus indicators for accessibility */
        button:focus,
        textarea:focus {
          outline: 2px solid rgba(139, 92, 246, 0.5);
          outline-offset: 2px;
        }

        /* Scrollbar styling for messages area */
        .overflow-y-auto::-webkit-scrollbar {
          width: 6px;
        }
        .overflow-y-auto::-webkit-scrollbar-track {
          background: rgba(51, 65, 85, 0.3);
        }
        .overflow-y-auto::-webkit-scrollbar-thumb {
          background: rgba(139, 92, 246, 0.5);
          border-radius: 3px;
        }
        .overflow-y-auto::-webkit-scrollbar-thumb:hover {
          background: rgba(139, 92, 246, 0.7);
        }
      `}</style>
    </>
  );
};
export default ChatInterface;
