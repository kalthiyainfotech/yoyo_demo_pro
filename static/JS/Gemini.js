// Theme management
function applyTheme(theme) {
    document.body.classList.remove('light', 'dark');

    if (theme === 'system') {
        theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    document.body.classList.add(theme);
    localStorage.setItem('theme', theme);

    // Update UI to show active theme
    document.querySelectorAll('.theme-options li').forEach(li => {
        li.textContent = li.textContent.replace(' ✔', '').trim();
        if (li.dataset.theme === theme) {
            li.textContent += ' ✔';
        }
    });
}

// Initialize theme
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'system';
    applyTheme(savedTheme);

    // Watch for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (localStorage.getItem('theme') === 'system') {
            applyTheme('system');
        }
    });
}

// Set up theme switcher
function setupThemeSwitcher() {
    document.querySelectorAll('.theme-options li').forEach(option => {
        option.addEventListener('click', function () {
            const theme = this.dataset.theme;
            applyTheme(theme);
        });
    });
}

// Option selector with check icon for model dropdown
function selectOption(clickedElement) {
    document.querySelectorAll('.option').forEach(option => {
        option.classList.remove('selected');
        const checkIcon = option.querySelector('.fa-circle-check');
        if (checkIcon) checkIcon.classList.add('hidden');
    });

    clickedElement.classList.add('selected');
    const clickedCheckIcon = clickedElement.querySelector('.fa-circle-check');
    if (clickedCheckIcon) clickedCheckIcon.classList.remove('hidden');
}

// Toggle settings dropdown
function toggleDropdown() {
    const menu = document.getElementById('dropdownMenu');
    const settingHelp = document.getElementById('setting-help');
    const mainContent = document.getElementById('main-content');

    if (menu && settingHelp && mainContent) {
        if (!mainContent.classList.contains('pinned')) {
            mainContent.classList.add('pinned');
        }

        const isVisible = menu.style.display === 'block';
        menu.style.display = isVisible ? 'none' : 'block';
        settingHelp.classList.toggle('setingbackgroundChange', !isVisible);
    }
}

// Close settings menu utility
function closeSettingsMenu() {
    const menu = document.getElementById('dropdownMenu');
    const settingHelp = document.getElementById('setting-help');

    if (menu && settingHelp) {
        menu.style.display = 'none';
        settingHelp.classList.remove('setingbackgroundChange');
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    // Initialize theme
    initTheme();
    setupThemeSwitcher();

    // Header model dropdown
    const modelToggle = document.getElementById('model-toggle');
    const modelDropdown = document.getElementById('model-dropdown');
    if (modelToggle && modelDropdown) {
        modelToggle.addEventListener('click', function (e) {
            e.stopPropagation();
            modelDropdown.classList.toggle('show');
        });

        document.addEventListener('click', function (e) {
            if (!modelDropdown.contains(e.target) && !modelToggle.contains(e.target)) {
                modelDropdown.classList.remove('show');
            }
        });

        modelDropdown.addEventListener('click', function (e) {
            e.stopPropagation();
        });
    }

    // Settings dropdown auto-close on document click
    document.addEventListener('click', function (e) {
        const dropdown = document.getElementById('dropdownMenu');
        const button = document.querySelector('.dropdown-toggle');
        const mainContent = document.getElementById('main-content');
        const settingHelp = document.getElementById('setting-help');

        if (dropdown && button && mainContent && settingHelp) {
            if (!dropdown.contains(e.target) && !button.contains(e.target)) {
                dropdown.style.display = 'none';
                settingHelp.classList.remove('setingbackgroundChange');
            }

            if (!mainContent.classList.contains('pinned')) {
                dropdown.style.display = 'none';
                settingHelp.classList.remove('setingbackgroundChange');
            }
        }
    });

    // Help Center functionality
    const help_Data = document.getElementById('help_Data');
    const help_close = document.getElementById('help_close');
    const open_help_center = document.getElementById('open_help_center');

    if (open_help_center && help_Data) {
        open_help_center.addEventListener('click', () =>
            help_Data.classList.remove('hidden')
        );
    }
    if (help_close && help_Data) {
        help_close.addEventListener('click', () =>
            help_Data.classList.add('hidden')
        );
    }

    // Feedback functionality
    const feedback_message = document.getElementById("feedback_message");
    const sendBtn = document.getElementById("sendBtn");
    const feedback_close = document.getElementById("feedback_close");
    const feedback_open = document.getElementById("feedback_open");
    const feedback_data = document.getElementById("feedback-data");

    if (feedback_open && feedback_data) {
        feedback_open.addEventListener('click', () =>
            feedback_data.classList.remove('hidden')
        );
    }
    if (feedback_close && feedback_data) {
        feedback_close.addEventListener('click', () =>
            feedback_data.classList.add('hidden')
        );
    }

    if (feedback_message && sendBtn) {
        feedback_message.addEventListener("input", function () {
            if (feedback_message.value.trim().length > 0) {
                sendBtn.disabled = false;
                sendBtn.classList.remove("bg-[#373737]", "text-white");
                sendBtn.classList.add("bg-[#7CACF8]", "text-[#062E6F]");
            } else {
                sendBtn.disabled = true;
                sendBtn.classList.remove("bg-[#7CACF8]", "text-[#062E6F]");
                sendBtn.classList.add("bg-[#373737]", "text-white");
            }
        });
    }

    // Plus button dropdown functionality
    const plusButton = document.getElementById('plus-button');
    const plusDropdown = document.getElementById('plus-dropdown');
    const triggerUpload = document.getElementById('trigger-upload');
    const fileInput = document.getElementById('upload-preview-input');

    if (plusButton && plusDropdown) {
        plusButton.addEventListener('click', function (e) {
            e.stopPropagation();
            plusDropdown.classList.toggle('hidden');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function (event) {
            if (!plusDropdown.contains(event.target) && !plusButton.contains(event.target)) {
                plusDropdown.classList.add('hidden');
            }
        });
    }

    // File upload functionality
    if (triggerUpload && fileInput) {
        triggerUpload.addEventListener('click', (e) => {
            e.preventDefault();
            if (plusDropdown) {
                plusDropdown.classList.add("hidden");
            }
            fileInput.value = '';
            fileInput.click();
        });

        fileInput.addEventListener('change', function () {
            if (this.files && this.files[0]) {
                console.log('File selected:', this.files[0].name);
                
                // Show image preview
                const file = this.files[0];
                const imagePreview = document.getElementById('image-preview');
                const imagePreviewContainer = document.getElementById('image-preview-container');
                
                if (file && file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        imagePreview.src = e.target.result;
                        imagePreviewContainer.classList.remove('hidden');
                    };
                    reader.readAsDataURL(file);
                }
            }
        });
    }

    // Remove image preview functionality
    const removePreviewBtn = document.getElementById('remove-preview');
    if (removePreviewBtn) {
        removePreviewBtn.addEventListener('click', function() {
            const imagePreviewContainer = document.getElementById('image-preview-container');
            const fileInput = document.getElementById('upload-preview-input');
            
            if (imagePreviewContainer) {
                imagePreviewContainer.classList.add('hidden');
            }
            if (fileInput) {
                fileInput.value = '';
            }
        });
    }
});


let backdrop


document.addEventListener('DOMContentLoaded', function () {
    mainContent = document.getElementById('main-content');
    backdrop = document.getElementById('backdrop');
})

function toggleDropdown() {
    const menu = document.getElementById('dropdownMenu');
    const settingHelp = document.getElementById('setting-help');
    const mainContent = document.getElementById('main-content');

    if (menu && settingHelp && mainContent) {
        if (!mainContent.classList.contains('pinned')) {
            mainContent.classList.add('pinned');
        }

        const isVisible = menu.style.display === 'block';
        menu.style.display = isVisible ? 'none' : 'block';
        settingHelp.classList.toggle('setingbackgroundChange', !isVisible);
    }
}

document.addEventListener('click', function (e) {
    const dropdown = document.getElementById('dropdownMenu');
    const button = document.querySelector('.dropdown-toggle');
    const mainContent = document.getElementById('main-content');
    const settingHelp = document.getElementById('setting-help');

    if (dropdown && button && mainContent && settingHelp) {
        if (!dropdown.contains(e.target) && !button.contains(e.target)) {
            dropdown.style.display = 'none';
            settingHelp.classList.remove('setingbackgroundChange');
        }

        if (!mainContent.classList.contains('pinned')) {
            dropdown.style.display = 'none';
            settingHelp.classList.remove('setingbackgroundChange');
        }
    }
});

document.getElementById('mobileMenuBtn').addEventListener('click', function () {
    const mainContent = document.getElementById('main-content');
    const backdrop = document.getElementById('backdrop');

    mainContent.classList.toggle('sidebar-open');
    mainContent.classList.toggle('pinned');
    backdrop.classList.toggle('active');
});

// Close sidebar when clicking backdrop
document.getElementById('backdrop').addEventListener('click', function () {
    document.getElementById('main-content').classList.remove('sidebar-open');
    document.getElementById('main-content').classList.remove('pinned');
    this.classList.remove('active');
});


if (openBtn) {
        openBtn.addEventListener('click', (e) => {
            e.stopPropagation();

            if (window.innerWidth <= 768) {
                mainContent.classList.toggle('sidebar-open');
                mainContent.classList.toggle('pinned');
                backdrop.classList.toggle('active');

                if (mainContent.classList.contains('sidebar-open')) {
                    mainContent.classList.remove('pinned');
                }
            } else {
                mainContent.classList.toggle('pinned');
            }
        });
    }

    if (backdrop) {
        backdrop.addEventListener('click', () => {
            mainContent.classList.remove('sidebar-open');
            backdrop.classList.remove('active');
            mainContent.classList.remove('pinned');
            closeSettingsMenu();
        });
    }

    // Single resize handler
window.addEventListener('resize', () => {
    if (window.innerWidth >= 768) {
        mainContent.classList.remove('sidebar-open');
        backdrop.classList.remove('active');
    } else {
        mainContent.classList.remove('pinned');
        mainContent.classList.remove('sidebar-open');
        backdrop.classList.remove('active');
        closeSettingsMenu();
    }
});
function autoResize(el) {
    el.style.height = "auto"; // Reset height
    el.style.height = el.scrollHeight + "px"; // Set to scroll height
  }

