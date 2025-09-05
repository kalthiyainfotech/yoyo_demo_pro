function toggleMenu(el) {
    document.querySelectorAll('.chat-dropdown').forEach(menu => menu.classList.add('hidden'));
    let dropdown = el.nextElementSibling;
    dropdown.classList.toggle('hidden');
}

// Inline rename
function startRename(el, chatId) {
    let li = el.closest(".chat-item");
    let titleEl = li.querySelector(".chat-title");
    let oldTitle = titleEl.innerText;

    // Replace title with input
    titleEl.outerHTML = `<input class="rename-input" type="text" value="${oldTitle}" 
                          onblur="saveRename(this, '${chatId}')" 
                          onkeydown="if(event.key==='Enter'){this.blur();}">`;

    li.querySelector(".rename-input").focus();
}

function saveRename(input, chatId) {
    let newTitle = input.value.trim();
    if (!newTitle) {
        input.value = "Untitled";
        newTitle = "Untitled";
    }

    fetch(`/chat/${chatId}/rename/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({ title: newTitle })
    }).then(res => {
        if (res.ok) {
            input.outerHTML = `<span class="chat-title" onclick="window.location.href='/chat/${chatId}/'">${newTitle}</span>`;
        } else {
            input.outerHTML = `<span class="chat-title">${newTitle}</span>`;
        }
    });
}

// Delete chat
function deleteChat(chatId) {
    fetch(`/chat/${chatId}/delete/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        }
    }).then(res => {
        if (res.ok) {
            document.querySelector(`[data-chat-id="${chatId}"]`).remove();
        }
    });
}

// Get CSRF token (Django)
function getCSRFToken() {
    let cookieValue = null;
    let cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        let cookie = cookies[i].trim();
        if (cookie.startsWith("csrftoken=")) {
            cookieValue = cookie.substring("csrftoken=".length);
            break;
        }
    }
    return cookieValue;
}

// Close menus if clicking outside
document.addEventListener("click", function(e) {
    if (!e.target.classList.contains("chat-menu")) {
        document.querySelectorAll('.chat-dropdown').forEach(menu => menu.classList.add('hidden'));
    }
});
