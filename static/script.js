import { startVoiceInput, speakText } from "./js/voice.js";

// --- State Management ---
let chatHistory = [];
let adminToken = ""; // Stores password after successful login

// --- DOM Elements ---
const chatContainer = document.getElementById("chat-history");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const micBtn = document.getElementById("mic-btn");
const loadingIndicator = document.getElementById("loading-indicator");
const adminModal = document.getElementById("admin-modal");
const adminLogs = document.getElementById("admin-logs");
const themeBtn = document.getElementById("theme-toggle");
const htmlElement = document.documentElement;

// --- 1. Theme Toggle Logic ---
if (localStorage.getItem("theme") === "dark") {
    htmlElement.classList.add("dark");
}

themeBtn.addEventListener("click", () => {
    htmlElement.classList.toggle("dark");
    if (htmlElement.classList.contains("dark")) {
        localStorage.setItem("theme", "dark");
    } else {
        localStorage.setItem("theme", "light");
    }
});

// --- 2. Admin Modal Logic (Open/Close) ---
document.getElementById("admin-toggle-btn").addEventListener("click", () => {
    adminModal.classList.remove("hidden");
    // If not logged in, show login screen, else show dashboard
    if (!adminToken) {
        document.getElementById("admin-login-screen").classList.remove("hidden");
        document.getElementById("admin-dashboard").classList.add("hidden");
    }
});

// The Missing Fix: Close Button
document.getElementById("close-admin").addEventListener("click", () => {
    adminModal.classList.add("hidden");
});

// Close when clicking outside (Backdrop)
document.getElementById("admin-backdrop").addEventListener("click", () => {
    adminModal.classList.add("hidden");
});

// --- 3. Admin Login & Security ---
document.getElementById("admin-login-btn").addEventListener("click", async () => {
    const password = document.getElementById("admin-password-input").value;
    const errorMsg = document.getElementById("login-error");
    
    try {
        // Verify with backend
        const res = await fetch("/api/admin/verify", {
            method: "POST",
            headers: { "x-admin-password": password }
        });

        if (res.ok) {
            // Success: Unlock Dashboard
            adminToken = password;
            document.getElementById("admin-login-screen").classList.add("hidden");
            document.getElementById("admin-dashboard").classList.remove("hidden");
            errorMsg.classList.add("hidden");
            document.getElementById("admin-password-input").value = ""; // Clear input
        } else {
            // Fail
            errorMsg.classList.remove("hidden");
        }
    } catch (e) {
        console.error(e);
        errorMsg.textContent = "Server Error";
        errorMsg.classList.remove("hidden");
    }
});

// --- 4. Admin Tools Functions (Protected) ---
function log(msg) {
    adminLogs.innerHTML += `<div>> ${msg}</div>`;
    adminLogs.scrollTop = adminLogs.scrollHeight;
}

window.triggerCrawl = async function() {
    const url = document.getElementById("crawl-url").value;
    if(!url) return alert("Please enter a URL");
    
    log(`Crawling ${url}...`);
    try {
        const res = await fetch("/api/admin/crawl", {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "x-admin-password": adminToken // Auth Header
            },
            body: JSON.stringify({ url }),
        });

        if (res.status === 401) throw new Error("Unauthorized: Re-login required");
        
        const data = await res.json();
        log(`Success: ${data.pages_crawled} pages crawled.`);
    } catch(e) {
        log(`Error: ${e.message}`);
    }
};

window.uploadPDF = async function() {
    const fileInput = document.getElementById("pdf-upload");
    if(fileInput.files.length === 0) return alert("Select a PDF");

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    log("Uploading PDF...");
    try {
        const res = await fetch("/api/admin/upload", {
            method: "POST",
            headers: { "x-admin-password": adminToken }, // Auth Header
            body: formData,
        });

        if (res.status === 401) throw new Error("Unauthorized");

        const data = await res.json();
        log(`Uploaded: ${data.filename}`);
    } catch(e) {
        log(`Error: ${e.message}`);
    }
};

window.retrain = async function() {
    log("Retraining Vector DB (This may take a minute)...");
    try {
        const res = await fetch("/api/admin/retrain", { 
            method: "POST",
            headers: { "x-admin-password": adminToken } // Auth Header
        });
        
        if (res.status === 401) throw new Error("Unauthorized");
        
        const data = await res.json();
        log(data.message);
    } catch(e) {
        log(`Error: ${e.message}`);
    }
};

// --- 5. Chat Logic ---

function appendUserMessage(text) {
    const div = document.createElement("div");
    div.className = "flex gap-4 mb-6 flex-row-reverse animate-fade-in-up";
    div.innerHTML = `
        <div class="flex flex-col gap-2 max-w-[85%]">
            <div class="bg-gradient-to-br from-blue-500 to-teal-400 text-white p-4 rounded-2xl rounded-tr-none shadow-md text-sm leading-relaxed">
                ${escapeHtml(text)}
            </div>
        </div>
    `;
    chatContainer.appendChild(div);
    scrollToBottom();
}

function appendBotMessage(text, sources, files = []) {
    const div = document.createElement("div");
    div.className = "flex gap-4 mb-6 animate-fade-in-up";
    
    // Format Sources
    let sourceHtml = "";
    if (sources && sources.length > 0) {
        sourceHtml = `<div class="mt-3 pt-2 border-t border-slate-100 dark:border-slate-700 text-[10px] text-slate-400">
            <strong>Sources:</strong> ${sources.join(", ")}
        </div>`;
    }

    // Format Files (PDF Cards)
    let filesHtml = "";
    if (files && files.length > 0) {
        filesHtml = `<div class="mt-3 flex flex-col gap-2">`;
        files.forEach(file => {
            filesHtml += `
            <a href="${file.url}" target="_blank" class="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 rounded-xl hover:border-teal-400 transition group text-decoration-none">
                <div class="w-10 h-10 bg-red-100 dark:bg-red-900/30 text-red-500 rounded-lg flex items-center justify-center shrink-0">
                    <i class="fa-regular fa-file-pdf text-lg"></i>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-slate-700 dark:text-slate-200 truncate group-hover:text-teal-500 transition">${file.name}</p>
                    <p class="text-[10px] text-slate-400">PDF Document • Click to Open</p>
                </div>
                <i class="fa-solid fa-download text-slate-400 group-hover:text-teal-500"></i>
            </a>`;
        });
        filesHtml += `</div>`;
    }

    div.innerHTML = `
        <div class="w-10 h-10 rounded-full bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 shadow-sm flex items-center justify-center text-teal-500 shrink-0">
            <img src="../static/images/logos.jpg" alt="Campus Logo" class="w-9 h-9 rounded-xl"/>
        </div>
        <div class="flex flex-col gap-2 max-w-[85%]">
            <div class="bg-white dark:bg-slate-800 p-4 rounded-2xl rounded-tl-none shadow-sm text-sm leading-relaxed text-slate-600 dark:text-slate-300 border border-slate-100 dark:border-slate-700 relative group">
                ${formatText(text)}
                ${filesHtml}
                ${sourceHtml}
                <button class="speak-btn absolute top-2 right-2 text-slate-300 hover:text-teal-500 opacity-0 group-hover:opacity-100 transition">
                    <i class="fa-solid fa-volume-high"></i>
                </button>
            </div>
        </div>
    `;
    
    const btn = div.querySelector(".speak-btn");
    btn.onclick = () => speakText(text);

    chatContainer.appendChild(div);
    scrollToBottom();
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    userInput.value = "";
    appendUserMessage(text);
    
    loadingIndicator.classList.remove("hidden");
    scrollToBottom();

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: text, history: chatHistory }),
        });
        const data = await response.json();

        loadingIndicator.classList.add("hidden");
        appendBotMessage(data.answer, data.sources, data.files);
        
        chatHistory.push(`User: ${text}`);
        chatHistory.push(`AI: ${data.answer}`);

    } catch (e) {
        loadingIndicator.classList.add("hidden");
        appendBotMessage("Sorry, I'm having trouble connecting to the server.");
    }
}

function scrollToBottom() {
    const main = document.getElementById("chat-container");
    main.scrollTop = main.scrollHeight;
}

// --- 6. Global Event Listeners ---

sendBtn.addEventListener("click", sendMessage);

userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
});

micBtn.addEventListener("click", async () => {
    try {
        micBtn.classList.add("mic-active");
        const text = await startVoiceInput();
        userInput.value = text;
        micBtn.classList.remove("mic-active");
        sendMessage();
    } catch (e) {
        console.error("Mic error", e);
        micBtn.classList.remove("mic-active");
    }
});

// --- Utilities ---
function escapeHtml(text) {
    if (!text) return text;
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function formatText(text) {
    if (!text) return "";
    let formatted = escapeHtml(text);
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    formatted = formatted.replace(/\n/g, "<br>");
    return formatted;
}