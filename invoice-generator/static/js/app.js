// Main App JavaScript

document.addEventListener('DOMContentLoaded', function () {
    // Mobile Navigation Toggle
    const navToggle = document.getElementById('navToggle');
    const sidebar = document.getElementById('sidebar');

    if (navToggle && sidebar) {
        navToggle.addEventListener('click', function () {
            sidebar.classList.toggle('open');
            document.body.style.overflow = sidebar.classList.contains('open') ? 'hidden' : '';
        });

        // Close sidebar when clicking outside
        document.addEventListener('click', function (e) {
            if (sidebar.classList.contains('open') &&
                !sidebar.contains(e.target) &&
                !navToggle.contains(e.target)) {
                sidebar.classList.remove('open');
                document.body.style.overflow = '';
            }
        });
    }

    // File Upload Preview
    const logoInput = document.getElementById('logo');
    const signatureInput = document.getElementById('signature');

    if (logoInput) {
        logoInput.addEventListener('change', function (e) {
            previewFile(e.target, 'logoUploadArea', 'logoPreview');
        });
    }

    if (signatureInput) {
        signatureInput.addEventListener('change', function (e) {
            previewFile(e.target, 'signatureUploadArea', 'signaturePreview');
        });
    }
});

// File Preview Function
function previewFile(input, areaId, previewId) {
    const area = document.getElementById(areaId);
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
            let preview = document.getElementById(previewId);
            if (!preview) {
                preview = document.createElement('img');
                preview.id = previewId;
                preview.className = 'preview-image';
                area.innerHTML = '';
                area.appendChild(preview);
            }
            preview.src = e.target.result;

            // Add filename
            let fileName = area.querySelector('.file-name');
            if (!fileName) {
                fileName = document.createElement('span');
                fileName.className = 'file-name';
                area.appendChild(fileName);
            }
            fileName.textContent = input.files[0].name;
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// Format Currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
    }).format(amount);
}

// Show Toast Notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#6366f1'};
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 500;
        z-index: 9999;
        animation: slideUp 0.3s ease;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideDown 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Add animation keyframes
const style = document.createElement('style');
style.textContent = `
    @keyframes slideUp {
        from { transform: translateX(-50%) translateY(100%); opacity: 0; }
        to { transform: translateX(-50%) translateY(0); opacity: 1; }
    }
    @keyframes slideDown {
        from { transform: translateX(-50%) translateY(0); opacity: 1; }
        to { transform: translateX(-50%) translateY(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);
