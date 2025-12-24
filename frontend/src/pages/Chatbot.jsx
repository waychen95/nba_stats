// src/pages/Chatbot.jsx
import "../styles/Chatbot.css";
import ReactMarkdown from 'react-markdown';
import { useEffect, useRef, useState } from "react";

const BASE_URL = import.meta.env.VITE_BASE_URL || 'http://localhost:3000';

function Chatbot() {
  const [sessionId] = useState(() => {
    const existing = localStorage.getItem("nbadle_session_id");
    if (existing) return existing;
    const id = `sess_${Math.random().toString(36).slice(2)}_${Date.now()}`;
    localStorage.setItem("nbadle_session_id", id);
    return id;
  });

  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [chat, setChat] = useState([
    {
      role: "assistant",
      text: "Hey! Ask me anything about the NBA, and I'll do my best to help!",
    },
  ]);

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat, loading]);

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  }, [message]);

  async function sendMessage() {
    const text = message.trim();
    if (!text || loading) return;

    setChat((prev) => [...prev, { role: "user", text }]);
    setMessage("");
    setLoading(true);

    try {
      const res = await fetch(`${BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: text }),
      });

      const data = await res.json();

      if (!res.ok || res.status === 500) {
        setChat((prev) => [
          ...prev,
          { 
            role: "assistant", 
            text: data?.error || "Something went wrong. Please try again." 
          },
        ]);
      } else {
        let answerText = data.answer;
      
        // Append internal link if metadata exists
        if (data.metadata && (data.metadata.player_id || data.metadata.team_id)) {
            if (data.metadata.player_id) {
                answerText += `\n\n[View ${data.metadata.player_name}'s Profile](/players/${data.metadata.player_id})`;
            } else if (data.metadata.team_id) {
                answerText += `\n\n[View ${data.metadata.team_name}'s Page](/teams/${data.metadata.team_id})`;
            }
        }

        setChat((prev) => [...prev, { role: "assistant", text: answerText, metadata: data.metadata || null }]);
      }
    } catch (e) {
      setChat((prev) => [
        ...prev,
        { 
          role: "assistant", 
          text: "Could not connect to the server. Please try again later." 
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div id="chatbot-container">
      <div id="chatbot-header">
        <h1>NBAdle Assistant</h1>
      </div>

      <div id="chat-window">
        {chat.map((m, idx) => (
          <div key={idx} className={`msg ${m.role}`}>
            <div className="bubble">
                {m.role === "assistant" ? (
                <>
                    {(m.metadata?.player_image_url || m.metadata?.team_image_url) && (
                    <img
                        src={m.metadata.player_image_url || m.metadata.team_image_url}
                        alt={
                        m.metadata?.player_name
                            ? `${m.metadata.player_name} headshot`
                            : m.metadata?.team_name
                            ? `${m.metadata.team_name} logo`
                            : "Image"
                        }
                        className="chatbot-headshot"
                        loading="lazy"
                    />
                    )}
                    <ReactMarkdown>{m.text}</ReactMarkdown>
                </>
                ) : (
                m.text
                )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="msg assistant">
            <div className="bubble">Typing...</div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div id="chat-input-area">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder='Ask about players, stats, teams...'
          rows={1}
          disabled={loading}
        />
        <button 
          className="button send" 
          onClick={sendMessage} 
          disabled={loading || !message.trim()}
        >
          {loading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}

export default Chatbot;