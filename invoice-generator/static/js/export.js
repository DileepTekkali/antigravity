// Export Functions - PDF, JPEG, Print, Share

// Download as PDF
async function downloadPDF() {
    const { jsPDF } = window.jspdf;
    const element = document.getElementById('billPreview');

    if (!element) {
        showToast('Bill preview not found', 'error');
        return;
    }

    showToast('Generating PDF...', 'info');

    try {
        const canvas = await html2canvas(element, {
            scale: 2,
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff'
        });

        const imgData = canvas.toDataURL('image/png');
        const pdf = new jsPDF({
            orientation: 'portrait',
            unit: 'mm',
            format: 'a4'
        });

        const pdfWidth = pdf.internal.pageSize.getWidth();
        const pdfHeight = pdf.internal.pageSize.getHeight();

        const imgWidth = canvas.width;
        const imgHeight = canvas.height;

        const ratio = Math.min(pdfWidth / imgWidth, pdfHeight / imgHeight);
        const imgX = (pdfWidth - imgWidth * ratio) / 2;
        const imgY = 10;

        pdf.addImage(imgData, 'PNG', imgX, imgY, imgWidth * ratio, imgHeight * ratio);

        const fileName = window.billNumber ? `${window.billNumber}.pdf` : 'invoice.pdf';
        pdf.save(fileName);

        showToast('PDF downloaded successfully!', 'success');
    } catch (error) {
        console.error('PDF generation error:', error);
        showToast('Failed to generate PDF', 'error');
    }
}

// Download as JPEG
async function downloadJPEG() {
    const element = document.getElementById('billPreview');

    if (!element) {
        showToast('Bill preview not found', 'error');
        return;
    }

    showToast('Generating image...', 'info');

    try {
        const canvas = await html2canvas(element, {
            scale: 2,
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff'
        });

        const link = document.createElement('a');
        link.download = window.billNumber ? `${window.billNumber}.jpg` : 'invoice.jpg';
        link.href = canvas.toDataURL('image/jpeg', 0.9);
        link.click();

        showToast('Image downloaded successfully!', 'success');
    } catch (error) {
        console.error('JPEG generation error:', error);
        showToast('Failed to generate image', 'error');
    }
}

// Print Bill
function printBill() {
    window.print();
}

// Share Bill (Web Share API)
async function shareBill() {
    const element = document.getElementById('billPreview');

    if (!navigator.share) {
        showToast('Share not supported on this device', 'error');
        return;
    }

    try {
        showToast('Preparing to share...', 'info');

        const canvas = await html2canvas(element, {
            scale: 2,
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff'
        });

        canvas.toBlob(async (blob) => {
            const fileName = window.billNumber ? `${window.billNumber}.png` : 'invoice.png';
            const file = new File([blob], fileName, { type: 'image/png' });

            try {
                await navigator.share({
                    title: `Invoice ${window.billNumber || ''}`,
                    text: 'Here is your invoice',
                    files: [file]
                });
                showToast('Shared successfully!', 'success');
            } catch (shareError) {
                if (shareError.name !== 'AbortError') {
                    // Fallback: try sharing without file
                    try {
                        await navigator.share({
                            title: `Invoice ${window.billNumber || ''}`,
                            text: 'Here is your invoice'
                        });
                    } catch (e) {
                        showToast('Share cancelled', 'info');
                    }
                }
            }
        }, 'image/png');
    } catch (error) {
        console.error('Share error:', error);
        showToast('Failed to share', 'error');
    }
}

// Toast notification function (if not already defined)
if (typeof showToast === 'undefined') {
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
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}
