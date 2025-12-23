// src/pages/Chatbot.jsx
import "../styles/Chatbot.css";
import { Link } from "react-router-dom";
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
      text: "Ask me anything about NBA, and I'll do my best to help!",
    },
  ]);

  const messagesEndRef = useRef(null);

//   useEffect(() => {
//     messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
//   }, [chat, loading]);

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

      if (!res.ok || res.stats == 500) {
        setChat((prev) => [
          ...prev,
          { role: "assistant", text: data?.error || "Something went wrong." },
        ]);
      } else {
        setChat((prev) => [...prev, { role: "assistant", text: data.answer }]);
      }
    } catch (e) {
      setChat((prev) => [
        ...prev,
        { role: "assistant", text: "Could not connect to the server. Make sure the Flask API is running." },
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
                <ReactMarkdown>{m.text}</ReactMarkdown>
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
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder='Type your message here...'
          rows={1}
          disabled={loading}
        />
        <button className="button send" onClick={sendMessage} disabled={loading || !message.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}

export default Chatbot;
