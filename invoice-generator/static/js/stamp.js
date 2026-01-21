// Stamp Generator JavaScript

function initStampGenerator() {
    const autoGenerateToggle = document.getElementById('autoGenerateStamp');
    const stampOptions = document.getElementById('stampOptions');
    const stampUploadSection = document.getElementById('stampUploadSection');

    const stampNameInput = document.getElementById('stamp_business_name');
    const stampPlaceInput = document.getElementById('stamp_place');
    const stampTypeInputs = document.querySelectorAll('input[name="stamp_type"]');
    const stampDataInput = document.getElementById('stampData');
    const canvas = document.getElementById('stampCanvas');

    if (!autoGenerateToggle || !canvas) return;

    const ctx = canvas.getContext('2d');

    autoGenerateToggle.addEventListener('change', function () {
        if (this.checked) {
            stampOptions.style.display = 'block';
            stampUploadSection.style.display = 'none';
            generateStamp();
        } else {
            stampOptions.style.display = 'none';
            stampUploadSection.style.display = 'block';
            stampDataInput.value = '';
        }
    });

    [stampNameInput, stampPlaceInput].forEach(input => {
        if (input) {
            input.addEventListener('input', debounce(generateStamp, 200));
            input.addEventListener('change', generateStamp);
        }
    });

    stampTypeInputs.forEach(input => {
        input.addEventListener('change', generateStamp);
    });

    const mainBusinessName = document.getElementById('business_name');
    const mainBusinessAddress = document.getElementById('business_address');

    if (mainBusinessName) {
        mainBusinessName.addEventListener('input', function () {
            if (autoGenerateToggle.checked && stampNameInput) {
                stampNameInput.value = this.value;
                generateStamp();
            }
        });
    }

    if (mainBusinessAddress) {
        mainBusinessAddress.addEventListener('input', function () {
            if (autoGenerateToggle.checked && stampPlaceInput) {
                const val = this.value;
                const city = val.includes(',') ? val.split(',').pop().trim() : val;
                stampPlaceInput.value = city;
                generateStamp();
            }
        });
    }

    if (autoGenerateToggle.checked) generateStamp();

    function generateStamp() {
        if (!autoGenerateToggle.checked) return;

        const name = (stampNameInput?.value || 'SEAL').toUpperCase();
        const place = (stampPlaceInput?.value || '').toUpperCase();
        const stampType = document.querySelector('input[name="stamp_type"]:checked')?.value || 'circle';

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const stampColor = '#1e3a8a';

        ctx.strokeStyle = stampColor;
        ctx.fillStyle = stampColor;

        if (stampType === 'circle') {
            drawCircleStamp(ctx, centerX, centerY, name, place, stampColor);
        } else {
            drawRectangleStamp(ctx, centerX, centerY, name, place, stampColor);
        }

        stampDataInput.value = canvas.toDataURL('image/png');
    }

    function drawCircleStamp(ctx, centerX, centerY, name, place, color) {
        const radius = 75;
        const innerRadius = 52;
        const textRadius = (radius + innerRadius) / 2;

        // Draw Circles
        ctx.lineWidth = 4;
        ctx.beginPath(); ctx.arc(centerX, centerY, radius, 0, Math.PI * 2); ctx.stroke();
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(centerX, centerY, innerRadius, 0, Math.PI * 2); ctx.stroke();

        let fontSize = 13;
        const kerningFactor = 1.15; // Fixed spacing factor for a "neat" look

        // Measurement loop to find the best font size that fits both texts with stars
        function calculateLayout(fSize) {
            ctx.font = `bold ${fSize}px Inter`;

            const spaceWidth = ctx.measureText(' ').width;
            const starWidth = ctx.measureText('★').width;

            const topAngle = (ctx.measureText(name).width / textRadius) * kerningFactor;
            const botAngle = place ? (ctx.measureText(place).width / textRadius) * kerningFactor : 0;

            const starBlockAngle = (starWidth + spaceWidth * 2) / textRadius; // Space Star Space

            // Required angle = Top + Bottom + 2 * StarBlock
            const totalRequired = topAngle + botAngle + (starBlockAngle * 2);
            return { topAngle, botAngle, totalRequired, starBlockAngle, fSize };
        }

        let layout = calculateLayout(fontSize);
        // If it doesn't fit, shrink font until it does (min 8px)
        while (layout.totalRequired > Math.PI * 1.95 && fontSize > 8) {
            fontSize -= 0.5;
            layout = calculateLayout(fontSize);
        }

        // Draw Text with the decided font size
        renderArcText(ctx, name, centerX, centerY, textRadius, color, `bold ${fontSize}px Inter`, false, layout.topAngle);
        if (place) {
            renderArcText(ctx, place, centerX, centerY, textRadius, color, `bold ${fontSize}px Inter`, true, layout.botAngle);
        }

        // Dynamic Stars - automatically centered in remaining gaps
        // Gap Midpoint Right (centered at 0)
        const rightStarAngle = (layout.topAngle - layout.botAngle) / 4;
        // Gap Midpoint Left (centered at PI)
        const leftStarAngle = Math.PI - (layout.topAngle - layout.botAngle) / 4;

        ctx.font = `bold ${fontSize + 1}px Inter`; // Star slightly bigger for visibility
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        [rightStarAngle, leftStarAngle].forEach(angle => {
            ctx.save();
            ctx.translate(centerX + Math.cos(angle) * textRadius, centerY + Math.sin(angle) * textRadius);
            ctx.fillText('★', 0, 0);
            ctx.restore();
        });
    }

    // New unified rendering function to ensure consistent spacing
    function renderArcText(ctx, str, cx, cy, radius, color, font, isBottom, totalAngle) {
        ctx.save();
        ctx.font = font;
        ctx.fillStyle = color;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        const anglePerChar = totalAngle / Math.max(str.length, 1);
        let startAngle;

        if (!isBottom) {
            // Top: centered north (-PI/2)
            startAngle = -Math.PI / 2 - (totalAngle / 2) + (anglePerChar / 2);
        } else {
            // Bottom: centered south (PI/2), reversing for readable LTR
            startAngle = Math.PI / 2 + (totalAngle / 2) - (anglePerChar / 2);
        }

        for (let i = 0; i < str.length; i++) {
            const charAngle = isBottom ? (startAngle - i * anglePerChar) : (startAngle + i * anglePerChar);
            ctx.save();
            ctx.translate(cx + Math.cos(charAngle) * radius, cy + Math.sin(charAngle) * radius);
            if (!isBottom) {
                ctx.rotate(charAngle + Math.PI / 2);
            } else {
                ctx.rotate(charAngle - Math.PI / 2);
            }
            ctx.fillText(str[i], 0, 0);
            ctx.restore();
        }
        ctx.restore();
    }

    function drawRectangleStamp(ctx, centerX, centerY, name, place, color) {
        const width = 180;
        const height = 90;
        const padding = 10;
        const maxWidth = width - padding * 2;

        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.strokeRect(centerX - width / 2, centerY - height / 2, width, height);

        ctx.fillStyle = color;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        // 1. Fit Business Name
        let nameFontSize = 18;
        ctx.font = `bold ${nameFontSize}px Inter`;
        while (ctx.measureText(name).width > maxWidth && nameFontSize > 10) {
            nameFontSize -= 1;
            ctx.font = `bold ${nameFontSize}px Inter`;
        }
        ctx.fillText(name, centerX, centerY - 15);

        // 2. Fit Place
        let placeFontSize = 12;
        ctx.font = `${placeFontSize}px Inter`;

        if (ctx.measureText(place).width > maxWidth) {
            // Try multi-line if too long
            const words = place.split(' ');
            const mid = Math.floor(words.length / 2);
            const line1 = words.slice(0, mid).join(' ');
            const line2 = words.slice(mid).join(' ');

            ctx.fillText(line1, centerX, centerY + 10);
            ctx.fillText(line2, centerX, centerY + 25);
        } else {
            ctx.fillText(place, centerX, centerY + 15);
        }
    }

    function debounce(func, wait) {
        let timeout;
        return function (...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func(...args), wait);
        };
    }
}
