import React from 'react';
import ChatInterface from './ChatInterface';

// Demo Component showing the chat interface in action
export const ChatInterfaceDemo = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 relative overflow-hidden font-inter">
      {/* Demo Dashboard Background */}
      <div className="absolute inset-0">
        <div className="absolute top-20 left-20 w-96 h-64 bg-violet-500/10 rounded-3xl backdrop-blur-3xl border border-violet-500/20"></div>
        <div className="absolute bottom-20 right-40 w-80 h-48 bg-purple-500/10 rounded-3xl backdrop-blur-3xl border border-purple-500/20"></div>
      </div>

      {/* Demo Content */}
      <div className="relative z-10 p-8">
        <h1 className="text-3xl font-bold text-white mb-4">ContextKeeper Dashboard</h1>
        <p className="text-slate-300 mb-8">Click the chat button in the bottom-right corner to open the assistant.</p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Demo cards */}
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-slate-900/50 backdrop-blur-md border border-slate-800 rounded-xl p-6 hover:shadow-2xl hover:shadow-violet-500/10 transition-all">
              <h3 className="text-white font-medium mb-2">Project {i}</h3>
              <p className="text-slate-400 text-sm">Sample project card content to demonstrate the dashboard layout with the chat interface.</p>
            </div>
          ))}
        </div>
      </div>

      {/* Chat Interface Component */}
      <ChatInterface />
    </div>
  );
};

export default ChatInterfaceDemo;
