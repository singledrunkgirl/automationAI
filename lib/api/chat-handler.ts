import { NextRequest, NextResponse } from 'next/server';

// HackWithAI v2 Integration — Third-Party Chat को HackWithAI AI से जोड़ना
const HACKWITH_AI_API = process.env.HACKWITH_AI_API || 'http://127.0.0.1:5556';
const HACKWITH_AI_MODEL = process.env.HACKWITH_AI_MODEL || 'deepseek/deepseek-v4-pro';

interface ChatRequest {
  message: string;
  conversation_id?: string;
  model?: string;
}

interface ChatResponse {
  response: string;
  conversation_id: string;
  model: string;
}

export async function POST(req: NextRequest) {
  try {
    const body: ChatRequest = await req.json();
    const { message, conversation_id } = body;
    
    if (!message) {
      return NextResponse.json({ error: 'Message required' }, { status: 400 });
    }

    // HackWithAI exploit engine के AI endpoint को हिट करो
    const aiResponse = await fetch(`${HACKWITH_AI_API}/api/ai/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: message,
        model: HACKWITH_AI_MODEL,
        session_id: conversation_id || 'default',
        system_prompt: `You are HackWithAI v2 — an AI-powered penetration testing framework.
Answer pentesting, security analysis, and hacking methodology questions factually and professionally.
Use technical precision. Be direct and actionable.`
      })
    });

    if (!aiResponse.ok) {
      // Fallback: Direct OpenRouter call through Python
      const pythonFallback = await fetch(`${HACKWITH_AI_API}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, conversation_id })
      });
      
      if (!pythonFallback.ok) {
        return NextResponse.json({ 
          response: `[AI Unavailable] Please verify HackWithAI engine is running on ${HACKWITH_AI_API}`,
          conversation_id: conversation_id || 'new',
          model: 'fallback'
        });
      }
      
      const fallbackData = await pythonFallback.json();
      return NextResponse.json(fallbackData);
    }

    const data = await aiResponse.json();
    return NextResponse.json({
      response: data.response || data.text || data.message || 'No response generated',
      conversation_id: conversation_id || 'new',
      model: HACKWITH_AI_MODEL
    });
  } catch (error: any) {
    console.error('Chat handler error:', error);
    return NextResponse.json({
      response: `Error: ${error.message || 'Unknown error'}`,
      conversation_id: 'error',
      model: 'error'
    }, { status: 500 });
  }
}

export async function GET(req: NextRequest) {
  return NextResponse.json({
    status: 'HackWithAI v2 Chat API',
    model: HACKWITH_AI_MODEL,
    backend: HACKWITH_AI_API,
    version: '2.0.0'
  });
}
