document.addEventListener("DOMContentLoaded", function () {

    const chatCards = document.querySelectorAll(".chat-card");
    let currentSocket = null;

    chatCards.forEach(card => {
        card.addEventListener("click", function () {

            const chatId = this.dataset.id;
            const userId = this.dataset.userId;
            const isPrivate = this.dataset.private === "1";
            const chatName = this.innerText.trim();

            // Set title
            document.getElementById("chat-title").innerText = chatName;

            // Clear chat
            document.getElementById("chat-log").innerHTML = "";

            // Close previous socket
            if (currentSocket) {
                currentSocket.close();
            }

            // Open new socket AFTER previous one closes
            setTimeout(() => {
                currentSocket = isPrivate
                    ? openPrivateChat(currentUserId, userId)
                    : openGroupChat(chatId);
            }, 50);
        });
    });
});
