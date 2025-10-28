const chatBox = document.getElementById("chat-box");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-btn");
const chatForm = document.getElementById("chat-form");

function toggleSendButton() {
    sendButton.disabled = messageInput.value.trim() === "";
}

messageInput.addEventListener("input", toggleSendButton);

window.onload = () => {
    toggleSendButton();
    scrollToBottom(false);
};

function scrollToBottom(smooth = true) {
    if (smooth) {
        chatBox.scrollTo({
            top: chatBox.scrollHeight,
            behavior: 'smooth'
        });
    } else {
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

function formatBotResponse(html) {
    let formatted = html;
    formatted = formatted.replace(/(\d+\.\s)/g, '<br>$1');
    formatted = formatted.replace(/^(<br>)+/, '');
    formatted = formatted.replace(/\n\n/g, '<br>');
    formatted = formatted.replace(/\n/g, '<br>');
    return formatted;
}

function createMessage(sender, message, isTemp = false) {
    const wrapper = document.createElement("div");
    wrapper.classList.add("message-wrapper", sender);

    const avatar = document.createElement("div");
    avatar.classList.add("message-avatar");
    avatar.innerHTML = sender === "user" ? '👤' : '🤖';

    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender);

    const content = document.createElement("div");
    content.classList.add("message-content");

    if (sender === "bot" && !isTemp) {
        content.innerHTML = formatBotResponse(message);
    } else {
        content.textContent = message;
    }

    const time = document.createElement("div");
    time.classList.add("message-time");
    time.textContent = new Date().toLocaleTimeString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit'
    });

    messageDiv.appendChild(content);
    messageDiv.appendChild(time);
    wrapper.appendChild(avatar);
    wrapper.appendChild(messageDiv);

    if (isTemp) wrapper.dataset.temp = "true";

    return wrapper;
}

function addMessage(sender, message, isTemp = false) {
    const messageElement = createMessage(sender, message, isTemp);
    chatBox.appendChild(messageElement);
    scrollToBottom();
    return messageElement;
}

function createTypingIndicator() {
    const wrapper = document.createElement("div");
    wrapper.classList.add("message-wrapper", "bot");
    wrapper.dataset.temp = "true";

    const avatar = document.createElement("div");
    avatar.classList.add("message-avatar");
    avatar.innerHTML = '🤖';

    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", "bot");

    const typingDiv = document.createElement("div");
    typingDiv.classList.add("typing-indicator");
    typingDiv.innerHTML = '<span></span><span></span><span></span>';

    messageDiv.appendChild(typingDiv);
    wrapper.appendChild(avatar);
    wrapper.appendChild(messageDiv);

    return wrapper;
}

function removeTempMessages() {
    const tempMessages = chatBox.querySelectorAll("[data-temp='true']");
    tempMessages.forEach(msg => msg.remove());
}

document.addEventListener('DOMContentLoaded', function() {
    document.body.addEventListener('click', function(e) {
        const quickReplyBtn = e.target.closest('.quick-reply-btn');
        if (quickReplyBtn) {
            e.preventDefault();
            const message = quickReplyBtn.getAttribute('data-message');
            messageInput.value = message;
            toggleSendButton();

            const welcomeMsg = document.querySelector('.welcome-message');
            if (welcomeMsg) {
                welcomeMsg.style.animation = 'fadeOut 0.3s ease-out';
                setTimeout(() => welcomeMsg.remove(), 300);
            }

            setTimeout(() => {
                chatForm.requestSubmit();
            }, 100);
        }
    });
});

chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const userMessage = messageInput.value.trim();
    if (!userMessage) return;

    const welcomeMsg = document.querySelector('.welcome-message');
    if (welcomeMsg && !welcomeMsg.style.animation) {
        welcomeMsg.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => welcomeMsg.remove(), 300);
    }

    addMessage("user", userMessage);
    messageInput.value = "";
    toggleSendButton();
    messageInput.disabled = true;
    sendButton.disabled = true;

    const typingIndicator = createTypingIndicator();
    chatBox.appendChild(typingIndicator);
    scrollToBottom();

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userMessage })
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        removeTempMessages();

        if (data.response) {
            addMessage('bot', data.response);
        } else {
            addMessage('bot', 'Xin lỗi, tôi không thể tạo phản hồi lúc này.');
        }

    } catch (err) {
        console.error('Error:', err);
        removeTempMessages();
        addMessage("bot", "⚠️ Đã xảy ra lỗi kết nối. Vui lòng thử lại sau.");
    } finally {
        messageInput.disabled = false;
        messageInput.focus();
        toggleSendButton();
    }
});

const style = document.createElement('style');
style.textContent = `
@keyframes fadeOut {
    from { opacity: 1; transform: scale(1); }
    to { opacity: 0; transform: scale(0.95); }
}
`;
document.head.appendChild(style);
