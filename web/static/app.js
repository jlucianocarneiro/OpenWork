const chat = document.getElementById("chat");
const welcome = document.getElementById("welcome");
const form = document.getElementById("chat-form");
const input = document.getElementById("input");
const btnSend = document.getElementById("btn-send");
const btnClear = document.getElementById("btn-clear");
const btnTheme = document.getElementById("btn-theme");
const skillSelect = document.getElementById("skill-select");
const modelBadge = document.getElementById("model-badge");
const statusDot = document.getElementById("status-dot");
const skillChips = document.getElementById("skill-chips");

let sending = false;

// Theme

function initTheme() {
  const saved = localStorage.getItem("ow-theme");
  if (saved) {
    document.documentElement.setAttribute("data-theme", saved);
    btnTheme.textContent = saved === "light" ? "☀" : "☽";
  }
}

btnTheme.addEventListener("click", () => {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "light" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("ow-theme", next);
  btnTheme.textContent = next === "light" ? "☀" : "☽";
});

// Auto-resize textarea

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 150) + "px";
});

// Markdown rendering

function renderMarkdown(text) {
  let html = text;

  // Code blocks
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    const escaped = escapeHtml(code.trimEnd());
    return `<pre><code class="language-${lang}">${escaped}</code></pre>`;
  });

  // Inline code
  html = html.replace(/`([^`\n]+)`/g, "<code>$1</code>");

  // Headers
  html = html.replace(/^######\s+(.+)$/gm, "<h6>$1</h6>");
  html = html.replace(/^#####\s+(.+)$/gm, "<h5>$1</h5>");
  html = html.replace(/^####\s+(.+)$/gm, "<h4>$1</h4>");
  html = html.replace(/^###\s+(.+)$/gm, "<h3>$1</h3>");
  html = html.replace(/^##\s+(.+)$/gm, "<h2>$1</h2>");
  html = html.replace(/^#\s+(.+)$/gm, "<h1>$1</h1>");

  // Horizontal rules
  html = html.replace(/^---+$/gm, "<hr>");

  // Bold and italic
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>");
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");

  // Blockquotes
  html = html.replace(/^>\s+(.+)$/gm, "<blockquote>$1</blockquote>");

  // Tables
  html = html.replace(
    /^(\|.+\|)\n(\|[-| :]+\|)\n((?:\|.+\|\n?)+)/gm,
    (_, header, sep, body) => {
      const ths = header.split("|").filter(c => c.trim()).map(c => `<th>${c.trim()}</th>`).join("");
      const rows = body.trim().split("\n").map(row => {
        const tds = row.split("|").filter(c => c.trim()).map(c => `<td>${c.trim()}</td>`).join("");
        return `<tr>${tds}</tr>`;
      }).join("");
      return `<table><thead><tr>${ths}</tr></thead><tbody>${rows}</tbody></table>`;
    }
  );

  // Unordered lists
  html = html.replace(/^(\s*)[-*]\s+(.+)$/gm, "$1<li>$2</li>");
  html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, "<ul>$1</ul>");

  // Ordered lists
  html = html.replace(/^(\s*)\d+\.\s+(.+)$/gm, "$1<li>$2</li>");

  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

  // Paragraphs
  html = html.replace(/\n\n+/g, "\n\n");
  html = html.split("\n\n").map(block => {
    block = block.trim();
    if (!block) return "";
    if (/^<(?:h[1-6]|ul|ol|li|table|thead|tbody|tr|pre|blockquote|hr)/.test(block)) return block;
    return `<p>${block.replace(/\n/g, "<br>")}</p>`;
  }).join("\n");

  return html;
}

function escapeHtml(text) {
  const el = document.createElement("div");
  el.textContent = text;
  return el.innerHTML;
}

// Chat

function addMessage(role, content) {
  if (welcome) welcome.style.display = "none";

  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${role}`;

  const contentDiv = document.createElement("div");
  contentDiv.className = "message-content";

  if (role === "assistant") {
    contentDiv.innerHTML = renderMarkdown(content);
  } else {
    contentDiv.innerHTML = `<p>${escapeHtml(content).replace(/\n/g, "<br>")}</p>`;
  }

  msgDiv.appendChild(contentDiv);
  chat.appendChild(msgDiv);
  chat.scrollTop = chat.scrollHeight;
  return contentDiv;
}

function createStreamingMessage() {
  if (welcome) welcome.style.display = "none";

  const msgDiv = document.createElement("div");
  msgDiv.className = "message assistant";

  const contentDiv = document.createElement("div");
  contentDiv.className = "message-content typing-indicator";

  msgDiv.appendChild(contentDiv);
  chat.appendChild(msgDiv);
  chat.scrollTop = chat.scrollHeight;
  return contentDiv;
}

async function sendMessage(text) {
  if (sending || !text.trim()) return;
  sending = true;
  btnSend.disabled = true;

  addMessage("user", text);
  const target = createStreamingMessage();
  let fullText = "";

  try {
    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const data = line.slice(6);
        if (data === "[DONE]") continue;

        try {
          const chunk = JSON.parse(data);
          if (chunk.error) {
            target.classList.remove("typing-indicator");
            target.innerHTML = `<p class="error-text">${escapeHtml(chunk.error)}</p>`;
            sending = false;
            btnSend.disabled = false;
            return;
          }
          if (chunk.content) {
            fullText += chunk.content;
            target.classList.remove("typing-indicator");
            target.innerHTML = renderMarkdown(fullText);
            chat.scrollTop = chat.scrollHeight;
          }
        } catch (_) {}
      }
    }
  } catch (err) {
    target.classList.remove("typing-indicator");
    target.innerHTML = `<p class="error-text">Erro de conexão: ${escapeHtml(err.message)}</p>`;
  }

  target.classList.remove("typing-indicator");
  if (fullText) {
    target.innerHTML = renderMarkdown(fullText);
  }
  sending = false;
  btnSend.disabled = false;
  input.focus();
}

// Events

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (text) {
    input.value = "";
    input.style.height = "auto";
    sendMessage(text);
  }
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.dispatchEvent(new Event("submit"));
  }
});

btnClear.addEventListener("click", async () => {
  await fetch("/api/clear", { method: "POST" });
  chat.innerHTML = "";
  if (welcome) {
    chat.appendChild(welcome);
    welcome.style.display = "";
  }
});

skillSelect.addEventListener("change", async () => {
  const name = skillSelect.value;
  await fetch("/api/skill", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  await fetch("/api/clear", { method: "POST" });
  chat.innerHTML = "";
  if (welcome) {
    chat.appendChild(welcome);
    welcome.style.display = "";
  }
  updateStatus();
});

// Init

async function loadSkills() {
  try {
    const resp = await fetch("/api/skills");
    const data = await resp.json();

    skillSelect.innerHTML = '<option value="">Sem skill</option>';
    skillChips.innerHTML = "";

    for (const s of data.skills) {
      const opt = document.createElement("option");
      opt.value = s.name;
      opt.textContent = s.title;
      if (s.name === data.active) opt.selected = true;
      skillSelect.appendChild(opt);

      const chip = document.createElement("button");
      chip.className = "skill-chip";
      chip.textContent = s.title;
      chip.addEventListener("click", () => {
        skillSelect.value = s.name;
        skillSelect.dispatchEvent(new Event("change"));
      });
      skillChips.appendChild(chip);
    }

    modelBadge.textContent = data.model;
  } catch (_) {}
}

async function updateStatus() {
  try {
    const resp = await fetch("/api/status");
    const data = await resp.json();
    statusDot.className = "status-dot" + (data.available ? " online" : "");
    modelBadge.textContent = data.model;
  } catch (_) {
    statusDot.className = "status-dot";
  }
}

initTheme();
loadSkills();
updateStatus();
setInterval(updateStatus, 30000);
