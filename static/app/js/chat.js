(function () {
    const QUICK_ACTIONS = [
        { id: "location", label: "IT Office Location", message: "Where is the IT office located and what are the extensions?" },
        { id: "lockout", label: "Portal Lockout Help", message: "My portal account is locked, what should I do?" },
        { id: "leave", label: "Apply for Leave", message: "Show me the steps to apply for employee leave." },
    ];

    const FEEDBACK_REASONS = [
        { id: "confused", label: "Still confused" },
        { id: "more-detail", label: "Need more detail" },
        { id: "wrong", label: "Wrong answer" },
        { id: "human", label: "Need human help" },
        { id: "other", label: "Other reason" },
    ];

    const state = {
        isOpen: false,
        isDark: localStorage.getItem("rafiki-theme") === "dark",
        isTyping: false,
        history: [],
        feedback: {},
    };

    const el = {
        body: document.body,
        fab: document.getElementById("chat-fab-button"),
        widget: document.getElementById("chat-widget-container"),
        close: document.getElementById("chat-close-button"),
        themeToggle: document.getElementById("theme-toggle-button"),
        messages: document.getElementById("chat-messages"),
        welcome: document.getElementById("welcome-state"),
        typing: document.getElementById("typing-indicator"),
        quickWelcome: document.getElementById("quick-actions-welcome"),
        quickBar: document.getElementById("quick-actions-bar"),
        form: document.getElementById("chat-form"),
        input: document.getElementById("chat-input"),
        send: document.getElementById("chat-send-button"),
    };

    function applyTheme() {
        el.body.classList.toggle("dark", state.isDark);
        el.themeToggle.textContent = state.isDark ? "☀" : "◐";
        localStorage.setItem("rafiki-theme", state.isDark ? "dark" : "light");
    }

    function toggleWidget(open) {
        state.isOpen = open;
        el.widget.classList.toggle("hidden", !open);
        el.fab.classList.toggle("hidden", open);
        if (open) {
            setTimeout(function () {
                el.input.focus();
            }, 50);
        }
    }

    function updateSendButton() {
        el.send.disabled = !el.input.value.trim() || state.isTyping;
    }

    function setTyping(isTyping) {
        state.isTyping = isTyping;
        el.typing.classList.toggle("hidden", !isTyping);
        updateSendButton();
        if (isTyping) {
            scrollMessages();
        }
    }

    function scrollMessages() {
        el.messages.scrollTop = el.messages.scrollHeight;
    }

    function createQuickActionButton(action) {
        const button = document.createElement("button");
        button.className = "quick-action-btn";
        button.type = "button";
        button.textContent = action.label;
        button.addEventListener("click", function () {
            sendMessage(action.message);
        });
        return button;
    }

    function renderQuickActions() {
        QUICK_ACTIONS.forEach(function (action) {
            el.quickWelcome.appendChild(createQuickActionButton(action));
            el.quickBar.appendChild(createQuickActionButton(action));
        });
    }

    function escapeHtml(text) {
        return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    function formatMarkdown(text) {
        let html = escapeHtml(text).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
        const lines = html.split("\n");
        const parts = [];
        let listType = null;

        lines.forEach(function (line) {
            const trimmed = line.trim();
            if (!trimmed) {
                if (listType) {
                    parts.push("</" + listType + ">");
                    listType = null;
                }
                return;
            }

            const ordered = trimmed.match(/^\d+\.\s+(.*)$/);
            const unordered = trimmed.match(/^-+\s+(.*)$/);

            if (ordered) {
                if (listType !== "ol") {
                    if (listType) {
                        parts.push("</" + listType + ">");
                    }
                    parts.push("<ol>");
                    listType = "ol";
                }
                parts.push("<li>" + ordered[1] + "</li>");
                return;
            }

            if (unordered) {
                if (listType !== "ul") {
                    if (listType) {
                        parts.push("</" + listType + ">");
                    }
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

    function lookupReason(reasonId) {
        const match = FEEDBACK_REASONS.find(function (item) {
            return item.id === reasonId;
        });
        return match ? match.label : "Feedback noted";
    }

    function submitFeedback(messageIndex, feedbackData, currentNode) {
        state.feedback[messageIndex] = feedbackData;

        fetch(window.rafikiConfig.feedbackUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                messageIndex: messageIndex,
                messageContent: state.history[messageIndex] ? state.history[messageIndex].content : null,
                feedbackType: feedbackData.type,
                feedbackReason: feedbackData.reason,
                timestamp: new Date().toISOString(),
            }),
        }).catch(function () {});

        const saved = document.createElement("div");
        saved.className = "feedback-row";
        saved.textContent = feedbackData.type === "positive" ? "Helpful feedback saved." : "Feedback noted: " + lookupReason(feedbackData.reason);
        currentNode.replaceWith(saved);
        scrollMessages();
    }

    function renderFeedback(messageIndex) {
        const container = document.createElement("div");
        container.className = "feedback-row";
        container.appendChild(document.createTextNode("Was this helpful?"));

        const thumbsUp = document.createElement("button");
        thumbsUp.type = "button";
        thumbsUp.textContent = "👍";
        thumbsUp.addEventListener("click", function () {
            submitFeedback(messageIndex, { type: "positive", reason: null }, container);
        });

        const thumbsDown = document.createElement("button");
        thumbsDown.type = "button";
        thumbsDown.textContent = "👎";
        thumbsDown.addEventListener("click", function () {
            const reasons = document.createElement("div");
            reasons.className = "feedback-reasons";

            FEEDBACK_REASONS.forEach(function (reason) {
                const chip = document.createElement("button");
                chip.type = "button";
                chip.className = "feedback-chip";
                chip.textContent = reason.label;
                chip.addEventListener("click", function () {
                    submitFeedback(messageIndex, { type: "negative", reason: reason.id }, reasons);
                });
                reasons.appendChild(chip);
            });

            container.replaceWith(reasons);
        });

        container.appendChild(thumbsUp);
        container.appendChild(thumbsDown);
        return container;
    }

    function appendMessage(role, content) {
        const historyIndex = state.history.length;
        const wrap = document.createElement("div");
        wrap.className = "message-wrap " + role;

        const bubble = document.createElement("div");
        bubble.className = "message-bubble";
        bubble.innerHTML = formatMarkdown(content);
        wrap.appendChild(bubble);

        el.messages.insertBefore(wrap, el.typing);
        state.history.push({ role: role, content: content });

        if (role === "assistant") {
            wrap.appendChild(renderFeedback(historyIndex));
        }

        el.welcome.classList.add("hidden");
        el.quickBar.classList.remove("hidden");
        scrollMessages();
    }

    function sendMessage(messageText) {
        const trimmed = (messageText || "").trim();
        if (!trimmed || state.isTyping) {
            return;
        }

        appendMessage("user", trimmed);
        el.input.value = "";
        updateSendButton();
        setTyping(true);

        fetch(window.rafikiConfig.chatUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: trimmed,
                history: state.history,
            }),
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("Bad response");
                }
                return response.json();
            })
            .then(function (data) {
                appendMessage("assistant", data.response || "I could not generate a response.");
            })
            .catch(function () {
                appendMessage("assistant", "I couldn't reach the server. Please check your connection or contact the IT Department if this continues.");
            })
            .finally(function () {
                setTyping(false);
            });
    }

    el.fab.addEventListener("click", function () {
        toggleWidget(true);
    });

    el.close.addEventListener("click", function () {
        toggleWidget(false);
    });

    el.themeToggle.addEventListener("click", function () {
        state.isDark = !state.isDark;
        applyTheme();
    });

    el.input.addEventListener("input", updateSendButton);

    el.form.addEventListener("submit", function (event) {
        event.preventDefault();
        sendMessage(el.input.value);
    });

    el.input.addEventListener("keydown", function (event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage(el.input.value);
        }
    });

    applyTheme();
    renderQuickActions();
})();
