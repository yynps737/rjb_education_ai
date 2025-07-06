/**
 * 带延迟的流式 API，让每个字符显示更明显
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

/**
 * 将字符串分割成词组的流（更自然的打字效果）
 */
async function* splitIntoChunks(text: string, delay: number = 50) {
  // 使用正则表达式分割文本，保留标点符号
  const chunks = text.match(/[\u4e00-\u9fa5]+|[a-zA-Z]+|\d+|[^\u4e00-\u9fa5\w\s]+|\s+/g) || [];
  
  for (const chunk of chunks) {
    yield chunk;
    if (delay > 0) {
      // 根据内容类型调整延迟
      let adjustedDelay = delay;
      if (chunk.match(/[。！？，、]$/)) {
        adjustedDelay = delay * 2; // 标点符号后稍微停顿
      } else if (chunk.trim() === '') {
        adjustedDelay = delay * 0.5; // 空格延迟较短
      }
      await new Promise(resolve => setTimeout(resolve, adjustedDelay));
    }
  }
}

export async function* streamAskQuestionWithDelay(
  query: string,
  courseId?: number,
  token?: string,
  endpoint: 'knowledge' | 'student' = 'student',
  charDelay: number = 30  // 每个字符的延迟（毫秒）
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
          
          if (data.type === 'content' && charDelay > 0) {
            // 将内容分割成词组并逐个发送
            for await (const chunk of splitIntoChunks(data.content, charDelay)) {
              yield {
                type: 'content',
                content: chunk
              } as StreamContent;
            }
          } else {
            yield data;
          }
        } catch (e) {
          console.error('Failed to parse SSE data:', e);
        }
      }
    }
    
    // 保留未完成的行
    buffer = lines[lines.length - 1];
  }
}