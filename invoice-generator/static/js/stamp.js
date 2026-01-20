// Stamp Generator JavaScript

function initStampGenerator() {
    const autoGenerateToggle = document.getElementById('autoGenerateStamp');
    const stampOptions = document.getElementById('stampOptions');
    const businessNameInput = document.getElementById('business_name');
    const stampTypeInputs = document.querySelectorAll('input[name="stamp_type"]');
    const stampDataInput = document.getElementById('stampData');
    const canvas = document.getElementById('stampCanvas');

    if (!autoGenerateToggle || !canvas) return;

    const ctx = canvas.getContext('2d');

    // Toggle stamp options visibility
    autoGenerateToggle.addEventListener('change', function () {
        stampOptions.style.display = this.checked ? 'block' : 'none';
        if (this.checked) {
            generateStamp();
        } else {
            stampDataInput.value = '';
            clearCanvas();
        }
    });

    // Regenerate stamp when name changes
    if (businessNameInput) {
        businessNameInput.addEventListener('input', debounce(generateStamp, 300));
    }

    // Regenerate stamp when type changes
    stampTypeInputs.forEach(input => {
        input.addEventListener('change', generateStamp);
    });

    // Initial generation if toggle is checked
    if (autoGenerateToggle.checked) {
        generateStamp();
    }

    function clearCanvas() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }

    function generateStamp() {
        if (!autoGenerateToggle.checked) return;

        const businessName = businessNameInput?.value || 'BUSINESS';
        const stampType = document.querySelector('input[name="stamp_type"]:checked')?.value || 'rectangle';

        clearCanvas();

        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const stampColor = '#1e40af'; // Blue color for official look

        ctx.strokeStyle = stampColor;
        ctx.fillStyle = stampColor;
        ctx.lineWidth = 3;
        ctx.font = 'bold 14px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        if (stampType === 'circle') {
            drawCircleStamp(ctx, centerX, centerY, businessName, stampColor);
        } else {
            drawRectangleStamp(ctx, centerX, centerY, businessName, stampColor);
        }

        // Save stamp data as base64
        stampDataInput.value = canvas.toDataURL('image/png');
    }

    function drawCircleStamp(ctx, centerX, centerY, businessName, color) {
        const radius = 80;

        // Outer circle
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        ctx.stroke();

        // Inner circle
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius - 8, 0, Math.PI * 2);
        ctx.stroke();

        // Business name curved at top
        ctx.save();
        ctx.translate(centerX, centerY);

        const text = businessName.toUpperCase();
        const anglePerChar = 0.12;
        const startAngle = -Math.PI / 2 - (text.length * anglePerChar) / 2;

        ctx.font = 'bold 12px Inter, sans-serif';
        for (let i = 0; i < text.length; i++) {
            const angle = startAngle + i * anglePerChar;
            ctx.save();
            ctx.rotate(angle + Math.PI / 2);
            ctx.translate(0, -radius + 20);
            ctx.rotate(-Math.PI / 2);
            ctx.fillText(text[i], 0, 0);
            ctx.restore();
        }

        ctx.restore();

        // Center star or symbol
        ctx.font = 'bold 24px Inter, sans-serif';
        ctx.fillText('★', centerX, centerY - 10);

        // "AUTHORIZED" text at bottom
        ctx.font = 'bold 10px Inter, sans-serif';
        ctx.fillText('AUTHORIZED', centerX, centerY + 15);

        // Date at very bottom
        const date = new Date().getFullYear();
        ctx.font = '10px Inter, sans-serif';
        ctx.fillText(date.toString(), centerX, centerY + 35);
    }

    function drawRectangleStamp(ctx, centerX, centerY, businessName, color) {
        const width = 160;
        const height = 80;
        const x = centerX - width / 2;
        const y = centerY - height / 2;
        const cornerRadius = 5;

        // Outer rectangle
        ctx.beginPath();
        roundRect(ctx, x, y, width, height, cornerRadius);
        ctx.stroke();

        // Inner rectangle
        ctx.beginPath();
        roundRect(ctx, x + 4, y + 4, width - 8, height - 8, cornerRadius - 2);
        ctx.stroke();

        // Business name
        ctx.font = 'bold 14px Inter, sans-serif';
        ctx.fillText(businessName.toUpperCase(), centerX, centerY - 12);

        // Separator line
        ctx.beginPath();
        ctx.moveTo(x + 20, centerY + 2);
        ctx.lineTo(x + width - 20, centerY + 2);
        ctx.stroke();

        // "AUTHORIZED SIGNATORY" text
        ctx.font = 'bold 9px Inter, sans-serif';
        ctx.fillText('AUTHORIZED SIGNATORY', centerX, centerY + 18);
    }

    function roundRect(ctx, x, y, width, height, radius) {
        ctx.moveTo(x + radius, y);
        ctx.lineTo(x + width - radius, y);
        ctx.arcTo(x + width, y, x + width, y + radius, radius);
        ctx.lineTo(x + width, y + height - radius);
        ctx.arcTo(x + width, y + height, x + width - radius, y + height, radius);
        ctx.lineTo(x + radius, y + height);
        ctx.arcTo(x, y + height, x, y + height - radius, radius);
        ctx.lineTo(x, y + radius);
        ctx.arcTo(x, y, x + radius, y, radius);
    }
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
