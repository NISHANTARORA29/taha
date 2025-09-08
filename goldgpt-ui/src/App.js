import React, { useState, useEffect, useRef } from 'react';
import { Send, Plus, MessageSquare, Settings, User, Menu, X, Trash2, Edit3, MoreHorizontal, Share, Archive, Image as ImageIcon } from 'lucide-react';

const ChatGPTClone = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [chatHistory, setChatHistory] = useState({});
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [error, setError] = useState(null);
  const [isMobile, setIsMobile] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // API base URL - adjust this to match your Flask server
  const API_BASE_URL = 'http://127.0.0.1:5003';

  // Check if device is mobile
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadChatHistory();
  }, []);

  const loadChatHistory = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/history`);
      if (response.ok) {
        const history = await response.json();
        setChatHistory(history);
      } else {
        console.error('Failed to load chat history');
        const mockHistory = {
          '1': { title: 'Gold Investment Strategy', timestamp: Date.now() - 86400000 },
          '2': { title: 'Current Gold Prices Analysis', timestamp: Date.now() - 172800000 },
          '3': { title: 'Silver vs Gold Comparison', timestamp: Date.now() - 259200000 }
        };
        setChatHistory(mockHistory);
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
      const mockHistory = {
        '1': { title: 'Gold Investment Strategy', timestamp: Date.now() - 86400000 },
        '2': { title: 'Current Gold Prices Analysis', timestamp: Date.now() - 172800000 },
        '3': { title: 'Silver vs Gold Comparison', timestamp: Date.now() - 259200000 }
      };
      setChatHistory(mockHistory);
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setIsLoading(true);
    setError(null);

    const newMessages = [...messages, { role: 'user', content: userMessage }];
    setMessages(newMessages);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const assistantMessage = {
        role: 'assistant',
        content: data.response,
        chart: data.chart,
        image: data.image // Add image data
      };

      // Update session ID if new
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
        setCurrentSessionId(data.session_id);
      }
      
      const finalMessages = [...newMessages, assistantMessage];
      setMessages(finalMessages);
      
      // Save chat session
      if (data.session_id) {
        await saveChatSession(data.session_id, finalMessages);
      }
      
    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to send message. Please check if the Flask server is running on port 5003.');
      
      const errorMessage = {
        role: 'assistant',
        content: `I'm sorry, I'm having trouble connecting to the server. Please make sure the Flask API is running on ${API_BASE_URL}. Error: ${error.message}`
      };
      setMessages([...newMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const saveChatSession = async (sessionId, messages) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/session/${sessionId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: messages,
          title: messages.find(m => m.role === 'user')?.content.substring(0, 50) || 'New Chat'
        })
      });
      
      if (response.ok) {
        loadChatHistory();
      }
    } catch (error) {
      console.error('Error saving chat session:', error);
    }
  };

  const loadChatSession = async (sessionId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/session/${sessionId}`);
      if (response.ok) {
        const sessionData = await response.json();
        setMessages(sessionData.messages);
        setCurrentSessionId(sessionId);
        setSessionId(sessionId);
        if (isMobile) {
          setSidebarOpen(false);
        }
      }
    } catch (error) {
      console.error('Error loading chat session:', error);
    }
  };

  const startNewChat = () => {
    setMessages([]);
    setSessionId(null);
    setCurrentSessionId(null);
    setError(null);
    if (isMobile) {
      setSidebarOpen(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <div style={{ 
      display: 'flex', 
      height: '100vh', 
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      position: 'relative'
    }}>
      {/* Mobile Overlay */}
      {isMobile && sidebarOpen && (
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 999,
            backdropFilter: 'blur(2px)'
          }}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div style={{
        width: isMobile ? (sidebarOpen ? '280px' : '0px') : (sidebarOpen ? '260px' : '0px'),
        position: isMobile ? 'fixed' : 'relative',
        top: 0,
        left: 0,
        height: '100vh',
        transition: 'width 0.3s ease, transform 0.3s ease',
        backgroundColor: '#171717',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        zIndex: 1000,
        transform: isMobile && !sidebarOpen ? 'translateX(-100%)' : 'translateX(0)',
        boxShadow: isMobile ? '2px 0 10px rgba(0,0,0,0.1)' : 'none'
      }}>
        {/* Mobile Close Button */}
        {isMobile && (
          <div style={{ padding: '8px', display: 'flex', justifyContent: 'flex-end' }}>
            <button
              onClick={() => setSidebarOpen(false)}
              style={{
                padding: '8px',
                borderRadius: '8px',
                border: 'none',
                backgroundColor: 'transparent',
                color: 'white',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <X size={20} />
            </button>
          </div>
        )}

        {/* New Chat Button */}
        <div style={{ padding: '8px' }}>
          <button
            onClick={startNewChat}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px',
              borderRadius: '8px',
              border: '1px solid #4b5563',
              backgroundColor: 'transparent',
              color: 'white',
              cursor: 'pointer',
              fontSize: '14px',
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => e.target.style.backgroundColor = '#1f2937'}
            onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
          >
            <Plus size={16} />
            <span>New chat</span>
          </button>
        </div>
        
        {/* Chat History */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '0 8px' }}>
          {Object.entries(chatHistory).map(([id, chat]) => (
            <div
              key={id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '12px',
                borderRadius: '8px',
                cursor: 'pointer',
                marginBottom: '4px',
                color: 'white',
                fontSize: '14px',
                backgroundColor: currentSessionId === id ? '#1f2937' : 'transparent',
                transition: 'background-color 0.2s'
              }}
              onClick={() => loadChatSession(id)}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#1f2937'}
              onMouseLeave={(e) => e.target.style.backgroundColor = currentSessionId === id ? '#1f2937' : 'transparent'}
            >
              <MessageSquare size={16} style={{ flexShrink: 0 }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {chat.title}
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {/* User Section */}
        <div style={{ padding: '8px', borderTop: '1px solid #374151' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '8px',
            borderRadius: '8px',
            color: 'white',
            cursor: 'pointer',
            fontSize: '14px'
          }}>
            <div style={{
              width: '32px',
              height: '32px',
              backgroundColor: '#d97706',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontWeight: '500'
            }}>
              G
            </div>
            <span>GoldGPT User</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column', 
        backgroundColor: 'white',
        marginLeft: isMobile ? '0' : '0',
        width: isMobile ? '100%' : 'auto'
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: isMobile ? '8px 12px' : '12px 16px',
          borderBottom: '1px solid #e5e7eb',
          minHeight: isMobile ? '56px' : '60px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              style={{
                padding: '8px',
                borderRadius: '8px',
                border: 'none',
                backgroundColor: 'transparent',
                cursor: 'pointer',
                color: '#374151',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#f3f4f6'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
            >
              <Menu size={20} />
            </button>
            <h1 style={{ 
              fontSize: isMobile ? '16px' : '18px', 
              fontWeight: '600', 
              color: '#111827', 
              margin: 0,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}>
              {isMobile ? 'GoldGPT' : 'GoldGPT - Ayar-24 Kuwait'}
            </h1>
          </div>
          {error && (
            <div style={{
              backgroundColor: '#fee2e2',
              color: '#dc2626',
              padding: isMobile ? '6px 8px' : '8px 12px',
              borderRadius: '6px',
              fontSize: isMobile ? '11px' : '12px',
              border: '1px solid #fecaca',
              maxWidth: isMobile ? '120px' : 'none',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}>
              {isMobile ? 'Error' : 'Connection Error'}
            </div>
          )}
        </div>

        {/* Messages Area */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {messages.length === 0 ? (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              textAlign: 'center',
              padding: isMobile ? '16px 12px' : '16px'
            }}>
              <div style={{ maxWidth: isMobile ? '100%' : '448px', width: '100%' }}>
                <div style={{ marginBottom: isMobile ? '24px' : '32px' }}>
                  <h1 style={{
                    fontSize: isMobile ? '24px' : '36px',
                    fontWeight: '600',
                    color: '#111827',
                    marginBottom: '8px',
                    margin: 0,
                    lineHeight: '1.2'
                  }}>
                    🥇 Welcome to GoldGPT
                  </h1>
                  <p style={{ 
                    color: '#6b7280', 
                    fontSize: isMobile ? '14px' : '16px', 
                    margin: '8px 0 0 0',
                    lineHeight: '1.4'
                  }}>
                    Your AI expert for precious metals trading and investment
                  </p>
                </div>
                
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr',
                  gap: isMobile ? '8px' : '12px',
                  marginBottom: isMobile ? '24px' : '32px'
                }}>
                  {[
                    { text: "What's the current gold price?", icon: "📈", title: "Get current gold prices", desc: "Live precious metals market data and Kuwait prices" },
                    { text: "How should I invest in gold?", icon: "💰", title: "Investment advice", desc: "Personalized precious metals investment strategies" },
                    { text: "Generate a gold image", icon: "🖼️", title: "Create AI images", desc: "Generate stunning visuals of gold bars, jewelry and more" },
                    { text: "Show me available gold products", icon: "🏅", title: "Browse products", desc: "Exclusive gold bars, coins and jewelry from Ayar-24" }
                  ].map((item, index) => (
                    <button 
                      key={index}
                      style={{
                        padding: isMobile ? '12px' : '16px',
                        textAlign: 'left',
                        border: '1px solid #e5e7eb',
                        borderRadius: isMobile ? '8px' : '12px',
                        backgroundColor: 'white',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        borderLeftColor: '#d97706',
                        borderLeftWidth: '3px'
                      }}
                      onClick={() => setInputValue(item.text)}
                      onMouseEnter={(e) => {
                        e.target.style.backgroundColor = '#fffbeb';
                        e.target.style.borderColor = '#d97706';
                      }}
                      onMouseLeave={(e) => {
                        e.target.style.backgroundColor = 'white';
                        e.target.style.borderColor = '#e5e7eb';
                        e.target.style.borderLeftColor = '#d97706';
                      }}
                    >
                      <div style={{ 
                        fontSize: isMobile ? '13px' : '14px', 
                        fontWeight: '500', 
                        color: '#111827' 
                      }}>
                        {item.icon} {item.title}
                      </div>
                      <div style={{ 
                        fontSize: isMobile ? '11px' : '12px', 
                        color: '#6b7280', 
                        marginTop: '4px',
                        lineHeight: '1.3'
                      }}>
                        {item.desc}
                      </div>
                    </button>
                  ))}
                </div>
                
                <div style={{
                  fontSize: isMobile ? '10px' : '12px',
                  color: '#9ca3af',
                  textAlign: 'center',
                  padding: isMobile ? '12px' : '16px',
                  backgroundColor: '#f9fafb',
                  borderRadius: '8px',
                  border: '1px solid #e5e7eb',
                  lineHeight: '1.4'
                }}>
                  🏪 <strong>Ayar-24 Kuwait</strong>
                  {!isMobile && ' | 📞 00965-98793103 | 🌐 ayar-24.com'}
                  {isMobile && (
                    <>
                      <br />📞 00965-98793103
                      <br />🌐 ayar-24.com
                    </>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div style={{ 
              maxWidth: isMobile ? '100%' : '768px', 
              margin: '0 auto', 
              padding: isMobile ? '16px 12px' : '24px 16px' 
            }}>
              {messages.map((message, index) => (
                <div key={index} style={{ marginBottom: isMobile ? '24px' : '32px' }}>
                  <div style={{ 
                    display: 'flex', 
                    gap: isMobile ? '12px' : '16px',
                    alignItems: 'flex-start'
                  }}>
                    <div style={{
                      width: isMobile ? '28px' : '32px',
                      height: isMobile ? '28px' : '32px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                      backgroundColor: message.role === 'user' ? '#7c3aed' : '#d97706',
                      color: 'white',
                      fontWeight: '500',
                      fontSize: isMobile ? '12px' : '14px'
                    }}>
                      {message.role === 'user' ? 'U' : '🥇'}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{
                        whiteSpace: 'pre-wrap',
                        color: '#111827',
                        fontSize: isMobile ? '14px' : '16px',
                        lineHeight: isMobile ? '1.5' : '1.75',
                        wordBreak: 'break-word'
                      }}>
                        {message.content}
                      </div>

                      {/* Display Generated Image */}
                      {message.image && (
                        <div style={{
                          marginTop: isMobile ? '12px' : '16px',
                          padding: isMobile ? '12px' : '16px',
                          backgroundColor: '#f9fafb',
                          borderRadius: '12px',
                          border: '1px solid #e5e7eb'
                        }}>
                          <div style={{ 
                            fontSize: isMobile ? '13px' : '14px', 
                            fontWeight: '500', 
                            marginBottom: '12px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px'
                          }}>
                            <ImageIcon size={16} />
                            Generated Image
                          </div>
                          
                          <div style={{
                            position: 'relative',
                            borderRadius: '8px',
                            overflow: 'hidden',
                            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                          }}>
                            <img 
                              src={`data:image/png;base64,${message.image.base64}`}
                              alt="Generated gold image"
                              style={{
                                width: '100%',
                                height: 'auto',
                                maxWidth: '512px',
                                display: 'block',
                                borderRadius: '8px'
                              }}
                              onError={(e) => {
                                console.error('Image failed to load:', e);
                                e.target.style.display = 'none';
                                e.target.nextSibling.style.display = 'block';
                              }}
                            />
                            <div style={{
                              display: 'none',
                              padding: '20px',
                              textAlign: 'center',
                              color: '#6b7280',
                              backgroundColor: '#f3f4f6',
                              borderRadius: '8px'
                            }}>
                              <ImageIcon size={24} style={{ marginBottom: '8px' }} />
                              <div>Image failed to load</div>
                            </div>
                          </div>

                          {message.image.prompt && (
                            <div style={{ 
                              fontSize: isMobile ? '11px' : '12px', 
                              color: '#6b7280',
                              marginTop: '8px',
                              fontStyle: 'italic'
                            }}>
                              <strong>Prompt:</strong> {message.image.original_prompt || message.image.prompt}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Display Chart */}
                      {message.chart && (
                        <div style={{
                          marginTop: isMobile ? '12px' : '16px',
                          padding: isMobile ? '12px' : '16px',
                          backgroundColor: '#f9fafb',
                          borderRadius: '8px',
                          border: '1px solid #e5e7eb'
                        }}>
                          <div style={{ 
                            fontSize: isMobile ? '13px' : '14px', 
                            fontWeight: '500', 
                            marginBottom: '8px' 
                          }}>
                            📊 {message.chart.title}
                          </div>
                          <div style={{ 
                            fontSize: isMobile ? '11px' : '12px', 
                            color: '#6b7280' 
                          }}>
                            Chart data available - visualization would be rendered here
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div style={{ marginBottom: isMobile ? '24px' : '32px' }}>
                  <div style={{ 
                    display: 'flex', 
                    gap: isMobile ? '12px' : '16px',
                    alignItems: 'flex-start'
                  }}>
                    <div style={{
                      width: isMobile ? '28px' : '32px',
                      height: isMobile ? '28px' : '32px',
                      borderRadius: '50%',
                      backgroundColor: '#d97706',
                      color: 'white',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                      fontWeight: '500',
                      fontSize: isMobile ? '12px' : '14px'
                    }}>
                      🥇
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <div style={{
                          width: isMobile ? '6px' : '8px',
                          height: isMobile ? '6px' : '8px',
                          backgroundColor: '#d97706',
                          borderRadius: '50%',
                          animation: 'bounce 1s infinite'
                        }}></div>
                        <div style={{
                          width: isMobile ? '6px' : '8px',
                          height: isMobile ? '6px' : '8px',
                          backgroundColor: '#d97706',
                          borderRadius: '50%',
                          animation: 'bounce 1s infinite 0.1s'
                        }}></div>
                        <div style={{
                          width: isMobile ? '6px' : '8px',
                          height: isMobile ? '6px' : '8px',
                          backgroundColor: '#d97706',
                          borderRadius: '50%',
                          animation: 'bounce 1s infinite 0.2s'
                        }}></div>
                        <span style={{ 
                          marginLeft: '8px', 
                          color: '#d97706', 
                          fontSize: isMobile ? '13px' : '14px' 
                        }}>
                          GoldGPT is analyzing...
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div style={{ 
          borderTop: '1px solid #e5e7eb', 
          padding: isMobile ? '12px' : '16px',
          paddingBottom: isMobile ? '12px' : '16px'
        }}>
          <div style={{ 
            maxWidth: isMobile ? '100%' : '768px', 
            margin: '0 auto' 
          }}>
            <div style={{
              position: 'relative',
              display: 'flex',
              alignItems: 'flex-end',
              backgroundColor: 'white',
              border: '1px solid #d1d5db',
              borderRadius: isMobile ? '8px' : '12px',
              boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
            }}>
              <textarea
                ref={textareaRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask GoldGPT about precious metals, prices, investment advice... or try 'generate a gold image'"
                style={{
                  flex: 1,
                  backgroundColor: 'transparent',
                  border: 'none',
                  outline: 'none',
                  resize: 'none',
                  color: '#111827',
                  padding: isMobile ? '12px 40px 12px 12px' : '12px 48px 12px 16px',
                  minHeight: isMobile ? '44px' : '50px',
                  maxHeight: isMobile ? '120px' : '208px',
                  fontSize: isMobile ? '16px' : '16px',
                  lineHeight: '1.5'
                }}
                rows={1}
                onInput={(e) => {
                  e.target.style.height = 'auto';
                  const maxHeight = isMobile ? 120 : 208;
                  e.target.style.height = Math.min(e.target.scrollHeight, maxHeight) + 'px';
                }}
              />
              <button
                onClick={sendMessage}
                disabled={!inputValue.trim() || isLoading}
                style={{
                  position: 'absolute',
                  right: isMobile ? '6px' : '8px',
                  bottom: isMobile ? '6px' : '8px',
                  padding: isMobile ? '6px' : '8px',
                  borderRadius: isMobile ? '6px' : '8px',
                  border: 'none',
                  backgroundColor: inputValue.trim() && !isLoading ? '#d97706' : '#e5e7eb',
                  color: inputValue.trim() && !isLoading ? 'white' : '#9ca3af',
                  cursor: inputValue.trim() && !isLoading ? 'pointer' : 'not-allowed',
                  transition: 'background-color 0.2s',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <Send size={isMobile ? 14 : 16} />
              </button>
            </div>
            <div style={{
              fontSize: isMobile ? '10px' : '12px',
              color: '#6b7280',
              textAlign: 'center',
              marginTop: '8px',
              lineHeight: '1.3'
            }}>
              GoldGPT by Ayar-24 Kuwait - Your trusted precious metals advisor
              {!isMobile && ` | Connected to: ${API_BASE_URL}`}
            </div>
          </div>
        </div>
      </div>
      
      <style>
        {`
          @keyframes bounce {
            0%, 80%, 100% {
              transform: scale(0);
              opacity: 0.3;
            } 40% {
              transform: scale(1);
              opacity: 1;
            }
          }
          
          /* Mobile specific styles */
          @media (max-width: 768px) {
            html {
              -webkit-text-size-adjust: 100%;
            }
            
            * {
              -webkit-tap-highlight-color: transparent;
            }
            
            input, textarea {
              font-size: 16px !important; /* Prevent zoom on iOS */
            }
          }
        `}
      </style>
    </div>
  );
};

export default ChatGPTClone;