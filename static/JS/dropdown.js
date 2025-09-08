
// ======================= COMMON MENU =======================
function toggleMenu(el) {
    document.querySelectorAll('.chat-dropdown').forEach(menu => menu.classList.add('hidden'));
    let dropdown = el.nextElementSibling;
    dropdown.classList.toggle('hidden');
}

// ======================= CHAT FUNCTIONS =======================

// Inline rename for Chat
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

// Open delete modal for Chat
function deleteChat(chatId) {
    openDeleteModal("chat", chatId);
}

// ======================= GEM FUNCTIONS =======================

// Inline rename for Gem
function startRenameGem(el, gemId) {
    let li = el.closest(".chat-item");
    let titleEl = li.querySelector(".chat-title");
    let oldTitle = titleEl.innerText;

    // Replace title with input
    titleEl.outerHTML = `<input class="rename-input" type="text" value="${oldTitle}" 
                          onblur="saveRenameGem(this, '${gemId}')" 
                          onkeydown="if(event.key==='Enter'){this.blur();}">`;

    li.querySelector(".rename-input").focus();
}

function saveRenameGem(input, gemId) {
    let newTitle = input.value.trim();
    if (!newTitle) {
        input.value = "Untitled Gem";
        newTitle = "Untitled Gem";
    }

    fetch(`/gem/${gemId}/rename/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({ name: newTitle })
    }).then(res => {
        if (res.ok) {
            input.outerHTML = `<span class="chat-title">${newTitle}</span>`;
        } else {
            input.outerHTML = `<span class="chat-title">${newTitle}</span>`;
        }
    });
}

// Open delete modal for Gem
function deleteGem(gemId) {
    openDeleteModal("gem", gemId);
}

// ======================= DELETE MODAL =======================

let deleteTarget = { type: null, id: null };

function openDeleteModal(type, id) {
    deleteTarget = { type, id };
    document.getElementById("deleteModal").classList.remove("hidden");
}

function closeDeleteModal() {
    deleteTarget = { type: null, id: null };
    document.getElementById("deleteModal").classList.add("hidden");
}

document.getElementById("confirmDeleteBtn").addEventListener("click", function() {
    if (!deleteTarget.type || !deleteTarget.id) return;

    let url = "";
    if (deleteTarget.type === "chat") {
        url = `/chat/${deleteTarget.id}/delete/`;
    } else if (deleteTarget.type === "gem") {
        url = `/gem/${deleteTarget.id}/delete/`;
    }

    fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        }
    }).then(res => {
        if (res.ok) {
            if (deleteTarget.type === "chat") {
                document.querySelector(`[data-chat-id="${deleteTarget.id}"]`).remove();
            } else if (deleteTarget.type === "gem") {
                document.querySelector(`[data-gem-id="${deleteTarget.id}"]`).remove();
            }
        }
        closeDeleteModal();
    });
});

// ======================= HELPERS =======================

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

