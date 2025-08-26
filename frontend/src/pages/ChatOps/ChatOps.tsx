import React, { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { apiService } from '../../services/api';
import LoadingSpinner from '../../components/Common/LoadingSpinner';
import toast from 'react-hot-toast';
import {
  PaperAirplaneIcon,
  CommandLineIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  status?: 'success' | 'error' | 'pending';
  metadata?: any;
}

const ChatOps: React.FC = () => {
  const [command, setCommand] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  const { data: supportedIntents, isLoading: intentsLoading } = useQuery(
    'supported-intents',
    apiService.getSupportedIntents
  );

  const { data: commandHistory, isLoading: historyLoading } = useQuery(
    'command-history',
    () => apiService.getCommandHistory(20)
  );

  const processCommandMutation = useMutation(
    (command: string) => apiService.processChatOpsCommand(command),
    {
      onSuccess: (data) => {
        const assistantMessage: ChatMessage = {
          id: Date.now().toString(),
          type: 'assistant',
          content: data.response || 'Command processed successfully',
          timestamp: new Date(),
          status: 'success',
          metadata: data,
        };
        setMessages(prev => [...prev, assistantMessage]);
        setIsProcessing(false);
        queryClient.invalidateQueries('command-history');
        queryClient.invalidateQueries('chatops-statistics');
        toast.success('Command executed successfully');
      },
      onError: (error: any) => {
        const assistantMessage: ChatMessage = {
          id: Date.now().toString(),
          type: 'assistant',
          content: error.response?.data?.error || 'Failed to process command',
          timestamp: new Date(),
          status: 'error',
        };
        setMessages(prev => [...prev, assistantMessage]);
        setIsProcessing(false);
        toast.error('Failed to process command');
      },
    }
  );

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!command.trim() || isProcessing) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: command,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsProcessing(true);
    processCommandMutation.mutate(command);
    setCommand('');
  };

  const handleQuickCommand = (quickCommand: string) => {
    setCommand(quickCommand);
  };

  const quickCommands = [
    'Show system status',
    'Check CPU usage',
    'List running services',
    'Show recent logs',
    'Check disk space',
    'Monitor network traffic',
  ];

  if (intentsLoading || historyLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="md:flex md:items-center md:justify-between mb-6">
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            ChatOps
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Interact with your infrastructure using natural language commands
          </p>
        </div>
      </div>

      <div className="flex-1 flex flex-col bg-white rounded-lg shadow">
        {/* Quick Commands */}
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-sm font-medium text-gray-900 mb-3">Quick Commands</h3>
          <div className="flex flex-wrap gap-2">
            {quickCommands.map((quickCommand) => (
              <button
                key={quickCommand}
                onClick={() => handleQuickCommand(quickCommand)}
                className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 hover:bg-indigo-200 transition-colors"
              >
                <CommandLineIcon className="h-3 w-3 mr-1" />
                {quickCommand}
              </button>
            ))}
          </div>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 py-8">
              <CommandLineIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>Start a conversation by typing a command below</p>
            </div>
          )}
          
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                  message.type === 'user'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <div className="flex items-start space-x-2">
                  <div className="flex-1">
                    <p className="text-sm">{message.content}</p>
                    {message.metadata && (
                      <div className="mt-2 text-xs opacity-75">
                        <p><strong>Intent:</strong> {message.metadata.intent}</p>
                        <p><strong>Confidence:</strong> {message.metadata.confidence}%</p>
                        {message.metadata.entities && (
                          <p><strong>Entities:</strong> {message.metadata.entities.join(', ')}</p>
                        )}
                      </div>
                    )}
                  </div>
                  {message.status && (
                    <div className="flex-shrink-0">
                      {message.status === 'success' ? (
                        <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      ) : message.status === 'error' ? (
                        <XCircleIcon className="h-4 w-4 text-red-500" />
                      ) : (
                        <LoadingSpinner size="sm" />
                      )}
                    </div>
                  )}
                </div>
                <p className="text-xs opacity-75 mt-1">
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}
          
          {isProcessing && (
            <div className="flex justify-start">
              <div className="bg-gray-100 text-gray-900 max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
                <div className="flex items-center space-x-2">
                  <LoadingSpinner size="sm" />
                  <span className="text-sm">Processing command...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Command Input */}
        <div className="p-4 border-t border-gray-200">
          <form onSubmit={handleSubmit} className="flex space-x-4">
            <div className="flex-1">
              <input
                type="text"
                value={command}
                onChange={(e) => setCommand(e.target.value)}
                placeholder="Type your command here..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                disabled={isProcessing}
              />
            </div>
            <button
              type="submit"
              disabled={!command.trim() || isProcessing}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <PaperAirplaneIcon className="h-4 w-4" />
              <span>Send</span>
            </button>
          </form>
        </div>
      </div>

      {/* Supported Intents */}
      {supportedIntents && (
        <div className="mt-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Supported Commands</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {supportedIntents.intents?.map((intent: any) => (
              <div key={intent.name} className="bg-white p-4 rounded-lg shadow">
                <h4 className="font-medium text-gray-900">{intent.name}</h4>
                <p className="text-sm text-gray-500 mt-1">{intent.description}</p>
                <div className="mt-2">
                  <span className="text-xs font-medium text-indigo-600 bg-indigo-100 px-2 py-1 rounded">
                    {intent.category}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatOps;
