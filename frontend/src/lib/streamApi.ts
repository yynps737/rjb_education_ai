/**
 * 流式 API 调用示例
 */

interface StreamMetadata {
  type: 'metadata';
  question: string;
  sources: any[];
  has_context: boolean;
}

interface StreamContent {
  type: 'content';
  content: string;
}

interface StreamDone {
  type: 'done';
}

interface StreamError {
  type: 'error';
  error: string;
}

type StreamData = StreamMetadata | StreamContent | StreamDone | StreamError;

export async function* streamAskQuestion(
  query: string,
  courseId?: number,
  token?: string,
  endpoint: 'knowledge' | 'student' = 'student'
) {
  const apiUrl = endpoint === 'student' 
    ? '/api/student/learning/ask-stream'
    : '/api/knowledge/ask-stream';
    
  const bodyData = endpoint === 'student'
    ? {
        question: query,
        course_id: courseId,
      }
    : {
        query,
        context_type: 'general',
        course_id: courseId,
      };
  
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${apiUrl}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : '',
    },
    body: JSON.stringify(bodyData),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    throw new Error('No response body');
  }

  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    
    // 处理完整的行
    for (let i = 0; i < lines.length - 1; i++) {
      const line = lines[i].trim();
      
      if (line.startsWith('data: ')) {
        try {
          const data: StreamData = JSON.parse(line.slice(6));
          yield data;
        } catch (e) {
          console.error('Failed to parse SSE data:', e);
        }
      }
    }
    
    // 保留未完成的行
    buffer = lines[lines.length - 1];
  }
}

// 使用示例
export async function useStreamQuestion(query: string, courseId?: number, endpoint: 'knowledge' | 'student' = 'student') {
  const token = localStorage.getItem('token');
  let fullAnswer = '';
  let metadata: StreamMetadata | null = null;

  try {
    for await (const data of streamAskQuestion(query, courseId, token || undefined, endpoint)) {
      switch (data.type) {
        case 'metadata':
          metadata = data;
          console.log('收到元数据:', metadata);
          break;
          
        case 'content':
          fullAnswer += data.content;
          // 在这里可以实时更新 UI
          console.log('收到内容片段:', data.content);
          break;
          
        case 'done':
          console.log('流式传输完成');
          break;
          
        case 'error':
          console.error('流式传输错误:', data.error);
          throw new Error(data.error);
      }
    }
    
    return {
      answer: fullAnswer,
      sources: metadata?.sources || [],
      hasContext: metadata?.has_context || false,
    };
  } catch (error) {
    console.error('流式传输失败:', error);
    throw error;
  }
}