(function () {
    if (window.RafikiWidget) {
        return;
    }

    var currentScript = document.currentScript;
    var scriptUrl = currentScript ? new URL(currentScript.src, window.location.href) : null;
    var config = window.RafikiWidgetConfig || {};
    var apiBase = (config.apiBase || (scriptUrl ? scriptUrl.origin : window.location.origin)).replace(/\/$/, "");
    var staticBase = config.staticBase || (scriptUrl ? scriptUrl.origin : window.location.origin);
    var primaryColor = config.primaryColor || "#8bc53f";
    var headerColor = config.headerColor || "#1c3c54";
    var title = config.title || "Rafiki IT";
    var subtitle = config.subtitle || "MOHI Support";
    var logoUrl = config.logoUrl || (staticBase + "/static/mohi-it-logo.png");

    var quickActions = config.quickActions || [
        { label: "IT Office Location", message: "Where is the IT office located and what are the extensions?" },
        { label: "Portal Lockout Help", message: "My portal account is locked, what should I do?" },
        { label: "Apply for Leave", message: "Show me the steps to apply for employee leave." }
    ];

    var state = {
        open: false,
        typing: false,
        history: []
    };

    function ensureStyles() {
        if (document.getElementById("rafiki-widget-styles")) {
            return;
        }

        var style = document.createElement("style");
        style.id = "rafiki-widget-styles";
        style.textContent = [
            ".rafiki-widget-root{position:fixed;right:24px;bottom:24px;z-index:2147483000;font-family:Inter,Arial,sans-serif;color:#0f172a}",
            ".rafiki-widget-root *{box-sizing:border-box}",
            ".rafiki-widget-fab{width:64px;height:64px;border:none;border-radius:999px;background:" + primaryColor + ";color:#fff;cursor:pointer;box-shadow:0 16px 32px rgba(0,0,0,.2);font-size:28px}",
            ".rafiki-widget-panel{width:min(400px,calc(100vw - 24px));height:min(600px,calc(100vh - 32px));display:none;flex-direction:column;background:#fff;border-radius:24px;overflow:hidden;box-shadow:0 30px 60px rgba(15,23,42,.25)}",
            ".rafiki-widget-root.open .rafiki-widget-panel{display:flex}",
            ".rafiki-widget-root.open .rafiki-widget-fab{display:none}",
            ".rafiki-widget-header{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;background:" + headerColor + ";color:#fff}",
            ".rafiki-widget-brand{display:flex;align-items:center;gap:12px}",
            ".rafiki-widget-brand img{width:40px;height:40px;background:#fff;border-radius:12px;padding:4px;object-fit:contain}",
            ".rafiki-widget-brand strong{display:block;font-size:14px;line-height:1.1}",
            ".rafiki-widget-brand span{display:block;color:" + primaryColor + ";font-size:20px;line-height:1.1}",
            ".rafiki-widget-icon-btn{border:none;background:transparent;color:inherit;cursor:pointer;font-size:18px;width:36px;height:36px;border-radius:999px}",
            ".rafiki-widget-body{flex:1;overflow-y:auto;background:#f8fafc;padding:16px}",
            ".rafiki-widget-welcome{text-align:center;padding:24px 0}",
            ".rafiki-widget-welcome h3{margin:0 0 8px}",
            ".rafiki-widget-welcome p{margin:0;color:#475569}",
            ".rafiki-widget-quick{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}",
            ".rafiki-widget-quick.center{justify-content:center}",
            ".rafiki-widget-quick button{border:1px solid transparent;border-radius:999px;padding:10px 14px;background:#eef2f7;color:#1c3c54;cursor:pointer;font-size:12px}",
            ".rafiki-widget-msg{display:flex;flex-direction:column;margin-bottom:12px}",
            ".rafiki-widget-msg.user{align-items:flex-end}",
            ".rafiki-widget-msg.assistant{align-items:flex-start}",
            ".rafiki-widget-bubble{max-width:85%;padding:12px 14px;border-radius:18px;line-height:1.5;font-size:14px}",
            ".rafiki-widget-msg.user .rafiki-widget-bubble{background:" + primaryColor + ";color:#fff;border-bottom-right-radius:6px}",
            ".rafiki-widget-msg.assistant .rafiki-widget-bubble{background:" + headerColor + ";color:#fff;border-bottom-left-radius:6px}",
            ".rafiki-widget-bubble p{margin:0 0 8px}",
            ".rafiki-widget-bubble p:last-child{margin-bottom:0}",
            ".rafiki-widget-bubble ul,.rafiki-widget-bubble ol{margin:8px 0 0;padding-left:20px}",
            ".rafiki-widget-typing{display:none;gap:6px;padding:12px 14px;background:" + headerColor + ";width:max-content;border-radius:18px;border-bottom-left-radius:6px;margin-bottom:12px}",
            ".rafiki-widget-typing.show{display:flex}",
            ".rafiki-widget-typing span{width:8px;height:8px;border-radius:999px;background:" + primaryColor + ";animation:rafiki-typing 1.4s infinite ease-in-out both}",
            ".rafiki-widget-typing span:nth-child(2){animation-delay:-.16s}",
            ".rafiki-widget-typing span:nth-child(3){animation-delay:-.32s}",
            ".rafiki-widget-actions{padding:12px 16px;border-top:1px solid #dbe4ee;background:#fff;display:none;overflow-x:auto}",
            ".rafiki-widget-actions.show{display:flex}",
            ".rafiki-widget-input{display:flex;gap:10px;padding:14px 16px;border-top:1px solid #dbe4ee;background:#fff}",
            ".rafiki-widget-input input{flex:1;border:none;border-radius:999px;padding:14px 16px;background:#f1f5f9;font:inherit}",
            ".rafiki-widget-input button{width:48px;height:48px;border:none;border-radius:999px;background:" + primaryColor + ";color:#fff;cursor:pointer}",
            ".rafiki-widget-input button:disabled{background:#cbd5e1;color:#64748b;cursor:not-allowed}",
            "@keyframes rafiki-typing{0%,80%,100%{transform:scale(0);opacity:.5}40%{transform:scale(1);opacity:1}}",
            "@media (max-width: 640px){.rafiki-widget-root{right:12px;bottom:12px}.rafiki-widget-panel{width:calc(100vw - 24px);height:calc(100vh - 24px)}}"
        ].join("");
        document.head.appendChild(style);
    }

    function escapeHtml(text) {
        return String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    function formatMarkdown(text) {
        var html = escapeHtml(text).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
        var lines = html.split("\n");
        var parts = [];
        var listType = null;

        lines.forEach(function (line) {
            var trimmed = line.trim();
            if (!trimmed) {
                if (listType) {
                    parts.push("</" + listType + ">");
                    listType = null;
                }
                return;
            }

            var ordered = trimmed.match(/^\d+\.\s+(.*)$/);
            var unordered = trimmed.match(/^-+\s+(.*)$/);

            if (ordered) {
                if (listType !== "ol") {
                    if (listType) parts.push("</" + listType + ">");
                    parts.push("<ol>");
                    listType = "ol";
                }
                parts.push("<li>" + ordered[1] + "</li>");
                return;
            }

            if (unordered) {
                if (listType !== "ul") {
                    if (listType) parts.push("</" + listType + ">");
                    parts.push("<ul>");
                    listType = "ul";
                }
                parts.push("<li>" + unordered[1] + "</li>");
                return;
            }

            if (listType) {
                parts.push("</" + listType + ">");
                listType = null;
            }
            parts.push("<p>" + trimmed + "</p>");
        });

        if (listType) {
            parts.push("</" + listType + ">");
        }

        return parts.join("");
    }

    function buildUi() {
        ensureStyles();

        var root = document.createElement("div");
        root.className = "rafiki-widget-root";
        root.innerHTML = [
            '<button class="rafiki-widget-fab" type="button" aria-label="Open chat">?</button>',
            '<section class="rafiki-widget-panel" aria-live="polite">',
            '  <header class="rafiki-widget-header">',
            '    <div class="rafiki-widget-brand">',
            '      <img alt="Rafiki logo" src="' + logoUrl + '">',
            "      <div><strong>" + escapeHtml(subtitle) + "</strong><span>" + escapeHtml(title) + "</span></div>",
            "    </div>",
            '    <button class="rafiki-widget-icon-btn" type="button" data-close aria-label="Close chat">x</button>',
            "  </header>",
            '  <div class="rafiki-widget-body">',
            '    <section class="rafiki-widget-welcome">',
            "      <h3>Hello! I'm Rafiki</h3>",
            "      <p>Your friendly IT assistant. How can I help you today?</p>",
            '      <div class="rafiki-widget-quick center" data-welcome-actions></div>',
            "    </section>",
            '    <div class="rafiki-widget-typing" data-typing><span></span><span></span><span></span></div>',
            "  </div>",
            '  <div class="rafiki-widget-actions" data-actions></div>',
            '  <form class="rafiki-widget-input">',
            '    <input type="text" placeholder="Ask Rafiki about IT support..." autocomplete="off">',
            '    <button type="submit" disabled>&gt;</button>',
            "  </form>",
            "</section>"
        ].join("");

        document.body.appendChild(root);

        var refs = {
            root: root,
            fab: root.querySelector(".rafiki-widget-fab"),
            panel: root.querySelector(".rafiki-widget-panel"),
            close: root.querySelector("[data-close]"),
            body: root.querySelector(".rafiki-widget-body"),
            welcome: root.querySelector(".rafiki-widget-welcome"),
            typing: root.querySelector("[data-typing]"),
            welcomeActions: root.querySelector("[data-welcome-actions]"),
            actions: root.querySelector("[data-actions]"),
            form: root.querySelector("form"),
            input: root.querySelector("input"),
            send: root.querySelector("button[type='submit']")
        };

        refs.fab.addEventListener("click", function () {
            state.open = true;
            refs.root.classList.add("open");
            setTimeout(function () { refs.input.focus(); }, 50);
        });

        refs.close.addEventListener("click", function () {
            state.open = false;
            refs.root.classList.remove("open");
        });

        refs.input.addEventListener("input", function () {
            refs.send.disabled = !refs.input.value.trim() || state.typing;
        });

        refs.form.addEventListener("submit", function (event) {
            event.preventDefault();
            sendMessage(refs, refs.input.value);
        });

        refs.input.addEventListener("keydown", function (event) {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                sendMessage(refs, refs.input.value);
            }
        });

        quickActions.forEach(function (action) {
            var button = document.createElement("button");
            button.type = "button";
            button.textContent = action.label;
            button.addEventListener("click", function () {
                sendMessage(refs, action.message);
            });
            refs.welcomeActions.appendChild(button);
            refs.actions.appendChild(button.cloneNode(true));
        });

        Array.prototype.forEach.call(refs.actions.children, function (button, index) {
            button.addEventListener("click", function () {
                sendMessage(refs, quickActions[index].message);
            });
        });
    }

    function appendMessage(refs, role, content) {
        var wrap = document.createElement("div");
        wrap.className = "rafiki-widget-msg " + role;

        var bubble = document.createElement("div");
        bubble.className = "rafiki-widget-bubble";
        bubble.innerHTML = formatMarkdown(content);
        wrap.appendChild(bubble);

        refs.body.insertBefore(wrap, refs.typing);
        refs.welcome.style.display = "none";
        refs.actions.classList.add("show");
        state.history.push({ role: role, content: content });
        refs.body.scrollTop = refs.body.scrollHeight;
    }

    function setTyping(refs, typing) {
        state.typing = typing;
        refs.typing.classList.toggle("show", typing);
        refs.send.disabled = !refs.input.value.trim() || typing;
        if (typing) {
            refs.body.scrollTop = refs.body.scrollHeight;
        }
    }

    function sendMessage(refs, message) {
        var trimmed = String(message || "").trim();
        if (!trimmed || state.typing) {
            return;
        }

        appendMessage(refs, "user", trimmed);
        refs.input.value = "";
        setTyping(refs, true);

        fetch(apiBase + "/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: trimmed,
                history: state.history
            })
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("Chat request failed");
                }
                return response.json();
            })
            .then(function (data) {
                appendMessage(refs, "assistant", data.response || "I could not generate a response.");
            })
            .catch(function () {
                appendMessage(refs, "assistant", "I could not reach Rafiki right now. Please try again shortly.");
            })
            .finally(function () {
                setTyping(refs, false);
            });
    }

    window.RafikiWidget = {
        mount: buildUi
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", buildUi);
    } else {
        buildUi();
    }
})();
