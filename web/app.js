/* ══════════════════════════════════════════════════════════════
   RAG AI — Frontend Application Logic
   ══════════════════════════════════════════════════════════════ */

// ── State ─────────────────────────────────────────────────────
const state = {
  isLoading: false,
  chatHistory: [],     // { role, content, time }
  currentTab: 'chat',
};

// ── DOM Refs ──────────────────────────────────────────────────
const $ = id => document.getElementById(id);

// ── Init ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadStatus();
  loadFiles();
  setInterval(loadStatus, 30000); // refresh status every 30s
});

// ══════════════════════════════════════════════════════════════
// TAB NAVIGATION
// ══════════════════════════════════════════════════════════════
function switchTab(tab) {
  state.currentTab = tab;

  // Update nav buttons
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  $(`nav${cap(tab)}`).classList.add('active');

  // Update panels
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  $(`tab${cap(tab)}`).classList.add('active');

  if (tab === 'files') loadFiles();
  if (tab === 'embed') loadStatus();
}

function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

// ══════════════════════════════════════════════════════════════
// STATUS
// ══════════════════════════════════════════════════════════════
async function loadStatus() {
  const dot   = $('statusDot');
  const label = $('statusLabel');
  const stats = $('statusStats');

  dot.className = 'status-dot loading';
  label.textContent = 'กำลังตรวจสอบ...';

  try {
    const res  = await fetch('/api/status');
    const data = await res.json();

    if (data.kb_ready) {
      dot.className = 'status-dot ready';
      label.textContent = 'พร้อมใช้งาน';
    } else {
      dot.className = 'status-dot error';
      label.textContent = 'ยังไม่มี Knowledge Base';
    }

    stats.innerHTML = `
      <div>🗄 Vectors: <strong>${data.vector_count.toLocaleString()}</strong></div>
      <div>📄 ไฟล์: <strong>${data.file_count}</strong> | Indexed: <strong>${data.indexed_count}</strong></div>
      ${data.pending_files.length ? `<div style="color:#f59e0b">⏳ รอ embed: ${data.pending_files.length} ไฟล์</div>` : ''}
    `;

    // Update embed tab stats
    $('kbVectors').textContent  = data.vector_count.toLocaleString();
    $('kbFiles').textContent    = data.file_count;
    $('kbIndexed').textContent  = data.indexed_count;
    $('pendingFileBadge').textContent = data.pending_files.length
      ? `${data.pending_files.length} ใหม่` : '✓ อัปเดตแล้ว';
    $('pendingUrlBadge').textContent = data.pending_url_count > 0
      ? `${data.pending_url_count} URL` : '✓ อัปเดตแล้ว';

  } catch (err) {
    dot.className = 'status-dot error';
    label.textContent = 'เชื่อมต่อไม่ได้';
    stats.textContent = 'ตรวจสอบว่า server รันอยู่';
  }
}

// ══════════════════════════════════════════════════════════════
// CHAT
// ══════════════════════════════════════════════════════════════
function handleKeyDown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendQuestion();
  }
}

function autoResize(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = Math.min(textarea.scrollHeight, 160) + 'px';
}

function fillQuestion(text) {
  const input = $('questionInput');
  input.value = text;
  autoResize(input);
  input.focus();
}

async function sendQuestion() {
  if (state.isLoading) return;

  const input    = $('questionInput');
  const question = input.value.trim();
  if (!question) return;

  // Clear welcome screen on first message
  const welcome = $('welcomeScreen');
  if (welcome) welcome.style.display = 'none';

  // Add user message
  appendMessage('user', question);
  input.value = '';
  input.style.height = 'auto';

  // Show typing indicator
  state.isLoading = true;
  $('sendBtn').disabled = true;
  const typingEl = showTyping();

  try {
    const res  = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();

    typingEl.remove();
    if (data.error) {
      appendMessage('bot', `❌ ${data.error}`, true);
    } else {
      appendMessage('bot', data.answer);
    }
  } catch (err) {
    typingEl.remove();
    appendMessage('bot', '❌ ไม่สามารถเชื่อมต่อกับ server ได้ กรุณาตรวจสอบว่า app.py รันอยู่', true);
  } finally {
    state.isLoading = false;
    $('sendBtn').disabled = false;
    input.focus();
  }
}

function appendMessage(role, content, isError = false) {
  const list    = $('messagesList');
  const time    = new Date().toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' });
  const isUser  = role === 'user';

  const wrapper = document.createElement('div');
  wrapper.className = `message ${role}`;
  wrapper.innerHTML = `
    <div class="msg-avatar">${isUser ? '👤' : '🤖'}</div>
    <div>
      <div class="msg-bubble${isError ? ' error-bubble' : ''}">${escapeHtml(content)}</div>
      <div class="msg-meta">${time}</div>
    </div>
  `;

  list.appendChild(wrapper);
  scrollToBottom();
}

function showTyping() {
  const list = $('messagesList');
  const el   = document.createElement('div');
  el.className = 'message bot';
  el.id = 'typingMsg';
  el.innerHTML = `
    <div class="msg-avatar">🤖</div>
    <div>
      <div class="msg-bubble typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>
  `;
  list.appendChild(el);
  scrollToBottom();
  return el;
}

function scrollToBottom() {
  const wrapper = $('messagesWrapper');
  requestAnimationFrame(() => {
    wrapper.scrollTop = wrapper.scrollHeight;
  });
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br/>');
}

// ══════════════════════════════════════════════════════════════
// FILE MANAGEMENT
// ══════════════════════════════════════════════════════════════
function handleDragOver(e) {
  e.preventDefault();
  $('uploadZone').classList.add('drag-over');
}
function handleDragLeave() {
  $('uploadZone').classList.remove('drag-over');
}
function handleDrop(e) {
  e.preventDefault();
  $('uploadZone').classList.remove('drag-over');
  const files = e.dataTransfer.files;
  if (files.length) uploadFiles(files);
}
function handleFileSelect(e) {
  uploadFiles(e.target.files);
}

async function uploadFiles(fileList) {
  const progressSection = $('uploadProgress');
  const progressBar     = $('progressBar');
  const progressLabel   = $('progressLabel');

  progressSection.classList.remove('hidden');
  progressBar.style.width = '10%';
  progressLabel.textContent = `กำลังอัปโหลด ${fileList.length} ไฟล์...`;

  const formData = new FormData();
  for (const f of fileList) formData.append('files', f);

  try {
    progressBar.style.width = '50%';
    const res  = await fetch('/api/upload', { method: 'POST', body: formData });
    const data = await res.json();

    progressBar.style.width = '100%';

    const uploadedNames = data.uploaded || [];
    const skippedNames  = data.skipped  || [];

    if (uploadedNames.length) {
      progressLabel.textContent = `✅ อัปโหลดสำเร็จ ${uploadedNames.length} ไฟล์`;
      showToast('success', `✅ อัปโหลด ${uploadedNames.length} ไฟล์สำเร็จ`);
      loadFiles();
      loadStatus();
    }
    if (skippedNames.length) {
      showToast('info', `⚠️ ข้ามไฟล์ ${skippedNames.length} รายการ (นามสกุลไม่รองรับ)`);
    }

    setTimeout(() => {
      progressSection.classList.add('hidden');
      progressBar.style.width = '0%';
    }, 2000);

  } catch (err) {
    progressLabel.textContent = '❌ อัปโหลดล้มเหลว';
    showToast('error', '❌ อัปโหลดล้มเหลว กรุณาลองใหม่');
  }

  // Reset file input
  $('fileInput').value = '';
}

async function loadFiles() {
  const list = $('fileList');
  list.innerHTML = '<div class="loading-files">กำลังโหลด...</div>';

  try {
    const res  = await fetch('/api/files');
    const data = await res.json();
    const files = data.files || [];

    if (!files.length) {
      list.innerHTML = '<div class="empty-files">📭 ยังไม่มีไฟล์ — วางไฟล์ในช่องด้านบน</div>';
      return;
    }

    list.innerHTML = '';
    files.forEach(f => {
      const icon = getFileIcon(f.name);
      const size = formatBytes(f.size);
      const item = document.createElement('div');
      item.className = 'file-item';
      item.innerHTML = `
        <div class="file-icon">${icon}</div>
        <div class="file-info">
          <div class="file-name" title="${escapeHtml(f.name)}">${escapeHtml(f.name)}</div>
          <div class="file-size">${size}</div>
        </div>
        <span class="file-status ${f.indexed ? 'indexed' : 'pending'}">${f.indexed ? 'Indexed' : 'รอ Embed'}</span>
        <button class="file-delete-btn" onclick="deleteFile('${escapeHtml(f.name)}')" title="ลบไฟล์">🗑</button>
      `;
      list.appendChild(item);
    });
  } catch (err) {
    list.innerHTML = '<div class="empty-files">❌ โหลดไฟล์ไม่ได้</div>';
  }
}

async function deleteFile(name) {
  if (!confirm(`ยืนยันการลบ "${name}"?`)) return;
  try {
    const res  = await fetch(`/api/files/${encodeURIComponent(name)}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.error) {
      showToast('error', `❌ ${data.error}`);
    } else {
      showToast('success', `🗑 ลบ ${name} เรียบร้อย`);
      loadFiles();
      loadStatus();
    }
  } catch (err) {
    showToast('error', '❌ ลบไฟล์ไม่สำเร็จ');
  }
}

function getFileIcon(name) {
  const ext = name.split('.').pop().toLowerCase();
  const icons = {
    pdf: '📕', txt: '📄', md: '📝', docx: '📘',
    csv: '📊', json: '🔧', xlsx: '📗', xls: '📗',
  };
  return icons[ext] || '📎';
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

// ══════════════════════════════════════════════════════════════
// EMBED
// ══════════════════════════════════════════════════════════════
async function startEmbed() {
  const btn      = $('embedBtn');
  const btnText  = $('embedBtnText');
  const logSec   = $('embedLogSection');
  const log      = $('embedLog');
  const embedUrls = $('embedUrlsToggle').checked;

  btn.disabled  = true;
  btnText.textContent = 'กำลัง Embed...';
  logSec.classList.remove('hidden');
  log.textContent = '⏳ กำลังเริ่มต้น embed...\n';

  // Simulate streaming log (server doesn't stream, so we poll-like)
  const loadingLines = [
    '📥 กำลังโหลดข้อมูล...',
    '✂️  กำลังตัด chunks...',
    '🔄 กำลัง embed ด้วย nomic-embed-text...',
    '   (อาจใช้เวลาสักครู่ขึ้นกับขนาดข้อมูล)',
    '⏳ กรุณารอ...',
  ];
  let lineIdx = 0;
  const logTimer = setInterval(() => {
    if (lineIdx < loadingLines.length) {
      log.textContent += loadingLines[lineIdx++] + '\n';
      log.scrollTop = log.scrollHeight;
    }
  }, 1200);

  try {
    const res  = await fetch('/api/embed', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ embed_urls: embedUrls }),
    });
    clearInterval(logTimer);
    const data = await res.json();

    if (data.error) {
      log.textContent += `\n❌ Error: ${data.error}\n`;
      showToast('error', `❌ Embed ล้มเหลว: ${data.error}`);
    } else {
      log.textContent += `\n✅ ${data.message}\n`;
      showToast('success', `✅ ${data.message}`);
      loadStatus();
      loadFiles();
    }
  } catch (err) {
    clearInterval(logTimer);
    log.textContent += '\n❌ ไม่สามารถเชื่อมต่อ server\n';
    showToast('error', '❌ เชื่อมต่อ server ไม่ได้');
  } finally {
    btn.disabled  = false;
    btnText.textContent = 'เริ่ม Embed';
    log.scrollTop = log.scrollHeight;
  }
}

// ══════════════════════════════════════════════════════════════
// TOAST NOTIFICATIONS
// ══════════════════════════════════════════════════════════════
const toastIcons = { success: '✅', error: '❌', info: 'ℹ️' };

function showToast(type, message, duration = 4000) {
  const container = $('toastContainer');
  const toast     = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${toastIcons[type] || 'ℹ️'}</span>
    <span>${message}</span>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('removing');
    toast.addEventListener('animationend', () => toast.remove(), { once: true });
  }, duration);
}
