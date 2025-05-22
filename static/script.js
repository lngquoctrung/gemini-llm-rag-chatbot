const chatBox = document.getElementById("chat-box");
const input = document.getElementById("message-input");
const button = document.querySelector("button[type='submit']");
const form = document.getElementById("chat-form");

function toggleButton() {
    button.disabled = input.value.trim() === "";
}

input.addEventListener("input", toggleButton);
window.onload = toggleButton;

function addMessage(sender, message, isTemp = false) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender);
    messageDiv.textContent = message;
    if (isTemp) messageDiv.dataset.temp = "true";
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
    return messageDiv;
}

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const userMessage = input.value.trim();
    if (!userMessage) return;

    // Hiển thị message người dùng
    addMessage("user", userMessage);
    input.value = "";
    toggleButton();

    // Hiển thị loading
    const loadingDiv = addMessage("bot", "Đang trả lời...", true);

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userMessage })
        });

        const data = await response.json();
        if (data.bot_response) {
            loadingDiv.innerHTML = data.bot_response;
        } else {
            loadingDiv.textContent = "Lỗi khi nhận phản hồi từ bot.";
        }
    } catch (err) {
        loadingDiv.textContent = "Lỗi kết nối đến máy chủ.";
    }
});
