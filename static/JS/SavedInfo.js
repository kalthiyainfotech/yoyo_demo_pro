const textareaMessage = document.getElementById('message');
const submitBtn = document.getElementById('submitBtn');
const addInfo = document.getElementById('add-info');
const saveinfoForm = document.getElementById('saveinfo-form');
const saveformcancle = document.getElementById('saveform-cancle');
const exampleInfo = document.getElementById('example-info');
const exampleForm = document.getElementById('example-form');
const examplecloseicon = document.getElementById('example-close-icon');
const exampleclose = document.getElementById('example-close');
const switchbox = document.getElementById('switch-box');
const infoP = document.getElementById('info-p');
const geminitool = document.getElementById('gemini-tool');
const geminitoolShow = document.getElementById('gemini-tool-show');
let updateID = null;

// Function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

textareaMessage.addEventListener('input', function () {
    submitBtn.disabled = textareaMessage.value.trim() === '';
});

geminitool.addEventListener('click', function () {
    geminitoolShow.classList.toggle('hidden');
})

switchbox.addEventListener('click', function () {
    addInfo.disabled = !switchbox.checked;
    if (infoP) {
        infoP.classList.toggle('text-[#7C7C7C]', !switchbox.checked);
    }

})

addInfo.addEventListener('click', function () {
    saveinfoForm.classList.remove('hidden')
})

saveformcancle.addEventListener('click', function () {
    saveinfoForm.classList.add('hidden')

})

exampleInfo.addEventListener('click', function () {
    exampleForm.classList.remove('hidden')
})

examplecloseicon.addEventListener('click', function () {
    exampleForm.classList.add('hidden')
})

exampleclose.addEventListener('click', function () {
    exampleForm.classList.add('hidden')
})




document.addEventListener('DOMContentLoaded', () => {
    if (saveinfoForm) {
        saveinfoForm.addEventListener('submit', handleSaveInfo);
    }


    const savedInfoDeleteModal = document.getElementById('savedInfoDeleteModal');
    const deleteAllModal = document.getElementById('deleteAllModal');
    const cancelSavedInfoDeleteBtn = document.getElementById('cancel-saved-info-delete-btn');
    const confirmSavedInfoDeleteBtn = document.getElementById('confirm-saved-info-delete-btn');
    const confirmDeleteAll = document.getElementById('confirm-delete-all');
    const cancelDeleteAll = document.getElementById('cancel-delete-all');

    if (cancelSavedInfoDeleteBtn) {
        cancelSavedInfoDeleteBtn.addEventListener('click', () => {
            savedInfoDeleteModal.classList.add('hidden');
        });
    }

    if (confirmSavedInfoDeleteBtn) {
        confirmSavedInfoDeleteBtn.addEventListener('click', () => {
            handleDeleteConfirmed();
        });
    }

    if (cancelDeleteAll) {
        cancelDeleteAll.addEventListener('click', () => {
            deleteAllModal.classList.add('hidden');
        });
    }

    if (confirmDeleteAll) {
        confirmDeleteAll.addEventListener('click', () => {
            handleDeleteAllinfo();
        });
    }

     


    Display();
});


const handleSaveInfo = async (event) => {
    event.preventDefault();

    const message = textareaMessage.value.trim();

    if (!message) {
        console.warn("Message is empty, not saving.");
        return;
    }

    const data = { info_text: message };

    try {
        let response;
        if (updateID) {
            // Update existing info
            response = await fetch(`/update-saved-info/${updateID}/`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie('csrftoken')
                },
                body: JSON.stringify(data),
            });
        } else {
            // Create new info
            response = await fetch("/save-info/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie('csrftoken')
                },
                body: JSON.stringify(data),
            });
        }

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        if (result.success) {
            textareaMessage.value = '';
            updateID = null;
            // Refresh the page to show updated data
            window.location.reload();
        } else {
            console.error("Error saving/updating info:", result.message);
        }

    } catch (error) {
        console.error("Error saving/updating info:", error);
    }
};

const Display = async (event) => {
    if (event) event.preventDefault();

    try {
        // Get saved info data from the template (passed from Django view)
        const savedInfoData = typeof window.savedInfos === 'string' ? JSON.parse(window.savedInfos) : (window.savedInfos || []);
        
        let deleteAllButtonHtml = savedInfoData.length > 0 ?
            `<button id="deleteall-info" onclick="handleDeleteall()"
                class="text-[--input-border-focus] border flex justify-center gap-2 text-md hover:bg-[--examples-btn-hover] py-2 items-center px-5 rounded-3xl font-semibold">
                <span class="material-symbols-outlined">delete</span>
                Delete all
            </button>` : '';

        let print = savedInfoData.length > 0 ? '<p class="font-semibold mb-2">Saved today</p>' : `<p id="info-p" class="text-[--sidebar-text] text-center">You haven't asked YOYO to save anything about you yet</p>`

        savedInfoData.map((v, index) => {
            const onlyOne = savedInfoData.length === 1;
            const firstDiv = index === 0;
            const lastDiv = index === savedInfoData.length - 1;

            let borderRadius = ' ';
            if (onlyOne) {
                borderRadius = 'rounded-t-xl rounded-b-xl';
            } else if (firstDiv) {
                borderRadius = 'rounded-t-xl rounded-b-sm';
            } else if (lastDiv) {
                borderRadius = 'rounded-t-sm rounded-b-xl';
            } else {
                borderRadius = 'rounded-t-sm rounded-b-sm';
            }

            print += `
                <div class="saveshowdata bg-[--sidebar-bg] w-full py-3 px-4 mb-1 flex items-center justify-between ${borderRadius}">
                    <p class="break-words text-md text-[--sidebar-text]">${v.info_text}</p>
                    <div class="relative">
                        <span id="action-ED-${index}" data-id="${v.id}" onClick="handleActionBtn(${index})"
                            class="action material-symbols-outlined rounded-full hover:bg-[--bg-hover] w-[40px] h-[40px] items-center justify-center flex cursor-pointer">more_vert</span>
                        <!-- Inline dropdown kept for semantics but not used; real menu is portal -->
                        <div id="action-data-${index}" class="hidden"></div>
                    </div>
                </div>
            `;
        });

        document.getElementById('all-delete').innerHTML = deleteAllButtonHtml;
        document.getElementById('savedData').innerHTML = print;

    } catch (error) {
        console.error(error);
    }
};

function handleActionBtn(index) {
    // Create or reuse a global portal container
    let portal = document.getElementById('saved-info-portal-menu');
    if (!portal) {
        portal = document.createElement('div');
        portal.id = 'saved-info-portal-menu';
        portal.style.position = 'fixed';
        portal.style.zIndex = '100000';
        portal.style.minWidth = '160px';
        portal.style.borderRadius = '12px';
        portal.style.background = '#1B1C1D';
        portal.style.boxShadow = '0 8px 24px rgba(0,0,0,0.4)';
        portal.style.display = 'none';
        portal.innerHTML = `
            <ul style="padding:8px 0; margin:0; list-style:none; background:#1B1C1D;">
                <li id="portal-edit" class="flex items-center px-3 py-2 cursor-pointer text-md" style="background:#1B1C1D; color: var(--text-main);">
                    <span class="material-symbols-outlined text-2xl mr-3">edit</span> Edit
                </li>
                <li id="portal-delete" class="flex items-center px-3 py-2 cursor-pointer text-md" style="background:#1B1C1D; color: var(--text-main);">
                    <span class="material-symbols-outlined text-2xl mr-3">delete</span> Delete
                </li>
            </ul>
        `;
        document.body.appendChild(portal);
    }

    // Close if open for another item
    if (portal.style.display === 'block' && portal.getAttribute('data-index') == String(index)) {
        portal.style.display = 'none';
        return;
    }

    // Attach handlers for this item
    const btn = document.getElementById(`action-ED-${index}`);
    const id = btn ? btn.getAttribute('data-id') : null;
    portal.querySelector('#portal-edit').onclick = () => { if (id) handleEdit(id); portal.style.display = 'none'; };
    portal.querySelector('#portal-delete').onclick = () => { if (id) handleDelete(id); };

    // Position near the trigger button
    if (btn) {
        const rect = btn.getBoundingClientRect();
        const top = rect.bottom + 6; // small gap
        const left = Math.min(window.innerWidth - 200, rect.right - 160); // align to right of button
        portal.style.top = `${Math.min(top, window.innerHeight - 10)}px`;
        portal.style.left = `${Math.max(8, left)}px`;
    }

    portal.setAttribute('data-index', String(index));
    portal.style.display = 'block';
  }


document.addEventListener('click', (event) => {
    const portal = document.getElementById('saved-info-portal-menu');
    if (!portal) return;
    const isTrigger = event.target.closest && event.target.closest('[id^="action-ED-"]');
    if (portal.style.display === 'block' && !portal.contains(event.target) && !isTrigger) {
        portal.style.display = 'none';
    }
});


const handleDeleteall = () => {
    const deleteAllModal = document.getElementById('deleteAllModal');
    if (deleteAllModal) {
        deleteAllModal.classList.remove('hidden');
    }
};

const handleDeleteAllinfo = async () => {
    try {
        // Show loading state
        const confirmBtn = document.getElementById('confirm-delete-all');
        const originalText = confirmBtn.textContent;
        confirmBtn.textContent = 'Deleting...';
        confirmBtn.disabled = true;

        const response = await fetch('/delete-all-saved-info/', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        if (result.success) {
            // Refresh the page to show updated data
            window.location.reload();
        } else {
            console.error("Error deleting all info:", result.message);
            alert("Error: " + result.message);
        }
    } catch (error) {
        console.error("Error deleting all info:", error);
        alert("Error deleting all info. Please try again.");
    } finally {
        // Reset button state
        const confirmBtn = document.getElementById('confirm-delete-all');
        if (confirmBtn) {
            confirmBtn.textContent = 'Delete all';
            confirmBtn.disabled = false;
        }
    }
}

const handleEdit = async (id) => {
    try {
        document.querySelectorAll('[id^="action-data-"]').forEach(drop => {
            drop.classList.add("hidden");
        });

        // Get data from the already loaded savedInfos
        const savedInfoData = typeof window.savedInfos === 'string' ? JSON.parse(window.savedInfos) : (window.savedInfos || []);
        const obj = savedInfoData.find((v) => v.id == id);

        if (obj) {
            textareaMessage.value = obj.info_text;
            updateID = obj.id;
            saveinfoForm.classList.remove('hidden');
            textareaMessage.focus();
        } else {
            console.warn(`No item found with ID: ${id}`);
        }
    } catch (error) {
        console.error("Error fetching info for edit:", error);
    }
};

let currentDeleteId = null;

const handleDelete = (id) => {
    currentDeleteId = id;
    const savedInfoDeleteModal = document.getElementById('savedInfoDeleteModal');
    if (savedInfoDeleteModal) {
        savedInfoDeleteModal.classList.remove('hidden');
    }
};


const handleDeleteConfirmed = async () => {
    if (!currentDeleteId) return;

    try {
        // Show loading state
        const confirmBtn = document.getElementById('confirm-saved-info-delete-btn');
        const originalText = confirmBtn.textContent;
        confirmBtn.textContent = 'Deleting...';
        confirmBtn.disabled = true;

        const response = await fetch('/delete-saved-info/' + currentDeleteId + '/', {
            method: "DELETE",
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        if (result.success) {
            const savedInfoDeleteModal = document.getElementById('savedInfoDeleteModal');
            if (savedInfoDeleteModal) {
                savedInfoDeleteModal.classList.add('hidden');
            }
            currentDeleteId = null;
            // Refresh the page to show updated data
            window.location.reload();
        } else {
            console.error("Error deleting info:", result.message);
            alert("Error: " + result.message);
        }
    } catch (error) {
        console.error("Error deleting info:", error);
        alert("Error deleting info. Please try again.");
    } finally {
        // Reset button state
        const confirmBtn = document.getElementById('confirm-saved-info-delete-btn');
        if (confirmBtn) {
            confirmBtn.textContent = 'Delete';
            confirmBtn.disabled = false;
        }
    }
}

saveinfoForm.addEventListener('submit', handleSaveInfo)
Display()




