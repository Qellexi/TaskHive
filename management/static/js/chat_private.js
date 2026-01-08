function openPrivateChat(user1, user2) {


    const protocol = location.protocol === "https:" ? "wss://" : "ws://";

     const socket = new WebSocket(
        protocol + window.location.host + `/ws/private/${user1}/${user2}/`
    );

    socket.onmessage = function(e) {
        const data = JSON.parse(e.data);

        if (data.type === "history") {
            data.messages.forEach(m => addMessage(m.sender_id, m.content, m.sender));
        }

        if (data.type === "message") {
            addMessage(data.sender_id, data.message, data.sender);
        }
    };

    function addMessage(senderId, content, senderName) {
        const log = document.getElementById("chat-log");

        const sideClass = senderId === currentUserId ? "message-right" : "message-left";

        log.innerHTML += `
            <div class="message ${sideClass}">
                <b>${senderId === currentUserId ? "You" : senderName}:</b> ${content}
            </div>
        `;

        log.scrollTop = log.scrollHeight;
    }

    document.getElementById("chat-message-submit").onclick = () => {
        socket.send(JSON.stringify({
            "message": document.getElementById("chat-message-input").value
        }));
        document.getElementById("chat-message-input").value = "";
    };

    return socket;
}
