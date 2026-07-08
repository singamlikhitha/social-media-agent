// Configuration
const API_BASE = window.location.origin;
const APP_NAME = "social_media_adk";
const USER_ID = "web-user-" + Math.random().toString(36).substr(2, 9);
let sessionId = null;
let isStreaming = false;
let uploadedFile = null; // { name, type, base64 }

// DOM Elements
const messagesDiv = document.getElementById("messages");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const fileInput = document.getElementById("fileInput");
const filePreview = document.getElementById("filePreview");

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  createSession();
  autoResizeTextarea();
});

// Auto-resize textarea
function autoResizeTextarea() {
  userInput.addEventListener("input", () => {
    userInput.style.height = "auto";
    userInput.style.height = Math.min(userInput.scrollHeight, 120) + "px";
  });
}

// Create a new session
async function createSession() {
  try {
    const res = await fetch(
      `${API_BASE}/apps/${APP_NAME}/users/${USER_ID}/sessions`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      }
    );
    const session = await res.json();
    sessionId = session.id;
  } catch (err) {
    console.error("Failed to create session:", err);
  }
}

// Start new chat
async function newSession() {
  sessionId = null;
  clearFileUpload();
  messagesDiv.innerHTML = `
    <div class="welcome-message">
      <div class="welcome-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/>
          <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
          <line x1="9" y1="9" x2="9.01" y2="9"/>
          <line x1="15" y1="9" x2="15.01" y2="9"/>
        </svg>
      </div>
      <h3>Hey! I'm your Social Media Agent</h3>
      <p>I can help you create content, schedule posts, suggest hashtags, and maximize your reach on Instagram & YouTube.</p>
      <div class="welcome-chips">
        <button onclick="sendQuick('Generate 3 Instagram content ideas about travel')">Generate Content Ideas</button>
        <button onclick="sendQuick('Optimize this caption: Just had an amazing day at the beach!')">Optimize a Caption</button>
        <button onclick="sendQuick('Schedule a post on Instagram with image https://example.com/photo.jpg about food')">Schedule a Post</button>
      </div>
    </div>
  `;
  await createSession();
}

// File upload handling
function triggerFileUpload() {
  fileInput.click();
}

function handleFileSelect(event) {
  const file = event.target.files[0];
  if (!file) return;

  // Validate file type
  const allowedTypes = ["image/jpeg", "image/png", "image/gif", "image/webp", "video/mp4", "video/quicktime"];
  if (!allowedTypes.includes(file.type)) {
    alert("Please upload an image (JPG, PNG, GIF, WebP) or video (MP4, MOV).");
    return;
  }

  // Validate file size (max 20MB for videos, 10MB for images)
  const maxSize = file.type.startsWith("video/") ? 20 * 1024 * 1024 : 10 * 1024 * 1024;
  if (file.size > maxSize) {
    alert(`File size must be under ${file.type.startsWith("video/") ? "20MB" : "10MB"}.`);
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    const base64 = e.target.result.split(",")[1];
    uploadedFile = {
      name: file.name,
      type: file.type,
      base64: base64,
      previewUrl: e.target.result,
    };
    showFilePreview();
  };
  reader.readAsDataURL(file);
}

function showFilePreview() {
  if (!uploadedFile) return;
  filePreview.innerHTML = `
    <div class="file-preview-card">
      ${
        uploadedFile.type.startsWith("image/")
          ? `<img src="${uploadedFile.previewUrl}" alt="Preview" />`
          : `<div class="video-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
            </div>`
      }
      <span class="file-name">${uploadedFile.name}</span>
      <button class="file-remove" onclick="clearFileUpload()">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
  `;
  filePreview.style.display = "block";
}

function clearFileUpload() {
  uploadedFile = null;
  fileInput.value = "";
  filePreview.innerHTML = "";
  filePreview.style.display = "none";
}

// Handle Enter key
function handleKeyDown(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

// Send from quick action
function sendQuick(text) {
  userInput.value = text;
  sendMessage();
}

// Build message parts
function buildMessageParts(text) {
  const parts = [];

  // Add image if uploaded
  if (uploadedFile) {
    parts.push({
      inline_data: {
        mime_type: uploadedFile.type,
        data: uploadedFile.base64,
      },
    });
  }

  // Add text
  if (text) {
    parts.push({ text: text });
  }

  return parts;
}

// Send message
async function sendMessage() {
  const text = userInput.value.trim();
  if ((!text && !uploadedFile) || isStreaming) return;

  // Clear welcome message
  const welcome = messagesDiv.querySelector(".welcome-message");
  if (welcome) welcome.remove();

  // Ensure session exists
  if (!sessionId) await createSession();

  // Add user message with image preview
  addUserMessage(text, uploadedFile);
  const messageParts = buildMessageParts(text);

  userInput.value = "";
  userInput.style.height = "auto";
  clearFileUpload();

  // Show typing indicator
  const typingId = showTyping();

  isStreaming = true;
  sendBtn.disabled = true;

  try {
    const response = await fetch(`${API_BASE}/run_sse`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        app_name: APP_NAME,
        user_id: USER_ID,
        session_id: sessionId,
        new_message: {
          role: "user",
          parts: messageParts,
        },
        streaming: true,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    // Remove typing indicator
    removeTyping(typingId);

    // Create agent message bubble for streaming
    const agentBubble = addMessage("", "agent");
    let fullText = "";

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const data = line.slice(6).trim();
        if (!data) continue;

        try {
          const event = JSON.parse(data);

          // Extract text from any event that has content with text parts
          // ADK events can have different structures, so we check broadly
          if (event.content && event.content.parts) {
            let eventText = "";
            for (const part of event.content.parts) {
              if (part.text) {
                eventText += part.text;
              }
            }
            // Use the latest event's text (replaces, not appends)
            // This handles both streaming deltas and complete responses
            if (eventText) {
              fullText = eventText;
              agentBubble.innerHTML = renderMarkdown(fullText);
              scrollToBottom();
            }
          }

          // Also check for nested author-based events
          if (event.author && event.parts) {
            let eventText = "";
            for (const part of event.parts) {
              if (part.text) {
                eventText += part.text;
              }
            }
            if (eventText) {
              fullText = eventText;
              agentBubble.innerHTML = renderMarkdown(fullText);
              scrollToBottom();
            }
          }
        } catch (e) {
          // Skip malformed JSON
        }
      }
    }

    // Final render
    if (fullText) {
      agentBubble.innerHTML = renderMarkdown(fullText);
    } else {
      agentBubble.innerHTML =
        '<em style="color: var(--text-secondary)">The agent is processing your request. Please try again if no response appears.</em>';
    }
  } catch (err) {
    removeTyping(typingId);
    addMessage(`Sorry, something went wrong: ${err.message}`, "agent");
  } finally {
    isStreaming = false;
    sendBtn.disabled = false;
    scrollToBottom();
  }
}

// Add user message (with optional image preview)
function addUserMessage(text, file) {
  const msgDiv = document.createElement("div");
  msgDiv.className = "message user";

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = "Y";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";

  let html = "";
  if (file && file.type.startsWith("image/")) {
    html += `<img src="${file.previewUrl}" class="message-image" alt="Uploaded image" />`;
  } else if (file) {
    html += `<div class="message-file-badge">${file.name}</div>`;
  }
  if (text) {
    html += `<div>${text}</div>`;
  }
  bubble.innerHTML = html;

  msgDiv.appendChild(avatar);
  msgDiv.appendChild(bubble);
  messagesDiv.appendChild(msgDiv);
  scrollToBottom();
}

// Add agent message to chat
function addMessage(text, role) {
  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = role === "user" ? "Y" : "AI";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";

  if (role === "user") {
    bubble.textContent = text;
  } else {
    bubble.innerHTML = text ? renderMarkdown(text) : "";
  }

  msgDiv.appendChild(avatar);
  msgDiv.appendChild(bubble);
  messagesDiv.appendChild(msgDiv);
  scrollToBottom();

  return bubble;
}

// Typing indicator
function showTyping() {
  const id = "typing-" + Date.now();
  const msgDiv = document.createElement("div");
  msgDiv.className = "message agent";
  msgDiv.id = id;

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = "AI";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.innerHTML = `
    <div class="typing-indicator">
      <span></span><span></span><span></span>
    </div>
  `;

  msgDiv.appendChild(avatar);
  msgDiv.appendChild(bubble);
  messagesDiv.appendChild(msgDiv);
  scrollToBottom();

  return id;
}

function removeTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// Simple Markdown renderer
function renderMarkdown(text) {
  let html = text
    // Code blocks
    .replace(/```(\w*)\n([\s\S]*?)```/g, "<pre><code>$2</code></pre>")
    // Inline code
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    // Bold
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    // Italic
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    // Headers
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    // Unordered lists
    .replace(/^[\-\*] (.+)$/gm, "<li>$1</li>")
    // Ordered lists
    .replace(/^\d+\. (.+)$/gm, "<li>$1</li>")
    // Line breaks
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br/>");

  // Wrap consecutive <li> in <ul>
  html = html.replace(
    /(<li>.*?<\/li>)(?:\s*<br\/>)*(<li>)/g,
    "$1$2"
  );
  html = html.replace(
    /(<li>[\s\S]*?<\/li>)/g,
    function (match) {
      if (!match.startsWith("<ul>")) return "<ul>" + match + "</ul>";
      return match;
    }
  );

  // Clean up nested <ul> tags
  html = html.replace(/<\/ul>\s*<ul>/g, "");

  return `<p>${html}</p>`.replace(/<p><\/p>/g, "");
}

// Scroll to bottom
function scrollToBottom() {
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}
