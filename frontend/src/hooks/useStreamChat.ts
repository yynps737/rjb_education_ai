import { useState, useCallback } from 'react';
import { streamAskQuestion } from '@/lib/streamApi';

interface UseStreamChatResult {
  answer: string;
  isStreaming: boolean;
  error: string | null;
  sources: any[];
  askQuestion: (query: string, courseId?: number) => Promise<void>;
  reset: () => void;
}

export function useStreamChat(): UseStreamChatResult {
  const [answer, setAnswer] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sources, setSources] = useState<any[]>([]);

  const reset = useCallback(() => {
    setAnswer('');
    setError(null);
    setSources([]);
    setIsStreaming(false);
  }, []);

  const askQuestion = useCallback(async (query: string, courseId?: number) => {
    reset();
    setIsStreaming(true);
    
    const token = localStorage.getItem('token');
    let fullAnswer = '';

    try {
      for await (const data of streamAskQuestion(query, courseId, token || undefined)) {
        switch (data.type) {
          case 'metadata':
            setSources(data.sources);
            break;
            
          case 'content':
            fullAnswer += data.content;
            setAnswer(fullAnswer);
            break;
            
          case 'done':
            setIsStreaming(false);
            break;
            
          case 'error':
            throw new Error(data.error);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '未知错误');
      setIsStreaming(false);
    }
  }, [reset]);

  return {
    answer,
    isStreaming,
    error,
    sources,
    askQuestion,
    reset,
  };
}