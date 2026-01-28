// Export Functions - PDF, JPEG, Print, Share

// Download as PDF with proper A4 sizing
async function downloadPDF() {
    const { jsPDF } = window.jspdf;
    const element = document.getElementById('billPreview');

    if (!element) {
        showToast('Bill preview not found', 'error');
        return;
    }

    showToast('Generating PDF...', 'info');

    try {
        // Capture only the invoice content, not the wrapper
        const canvas = await html2canvas(element, {
            scale: 2,
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff',
            windowWidth: 794,  // A4 width in pixels at 96 DPI (210mm)
            windowHeight: 1123, // A4 height in pixels at 96 DPI (297mm)
            x: 0,
            y: 0,
            scrollY: -window.scrollY,
            scrollX: -window.scrollX
        });

        const pdf = new jsPDF({
            orientation: 'portrait',
            unit: 'mm',
            format: 'a4'
        });

        const pdfWidth = 210; // A4 width in mm
        const pdfHeight = 297; // A4 height in mm
        const margin = 0; // No margins for full bleed

        // Calculate dimensions to fit A4 perfectly
        const imgWidth = canvas.width;
        const imgHeight = canvas.height;

        // Convert pixels to mm (assuming 96 DPI)
        const imgWidthMM = (imgWidth * 25.4) / (96 * 2); // scale is 2
        const imgHeightMM = (imgHeight * 25.4) / (96 * 2);

        // Check if content fits on one page
        if (imgHeightMM <= pdfHeight) {
            // Single page - fit to width
            const ratio = pdfWidth / imgWidthMM;
            const scaledHeight = imgHeightMM * ratio;

            pdf.addImage(canvas.toDataURL('image/png'), 'PNG',
                margin, margin, pdfWidth, scaledHeight);
        } else {
            // Multi-page - split content
            const pageHeight = pdfHeight;
            const pageHeightPx = (pageHeight * 96 * 2) / 25.4; // Convert mm to pixels

            let yPosition = 0;
            let pageNumber = 0;

            while (yPosition < imgHeight) {
                if (pageNumber > 0) {
                    pdf.addPage();
                }

                // Create a canvas for this page
                const pageCanvas = document.createElement('canvas');
                pageCanvas.width = imgWidth;
                pageCanvas.height = Math.min(pageHeightPx, imgHeight - yPosition);

                const ctx = pageCanvas.getContext('2d');
                ctx.drawImage(canvas,
                    0, yPosition, imgWidth, pageCanvas.height,
                    0, 0, imgWidth, pageCanvas.height);

                const pageImgData = pageCanvas.toDataURL('image/png');
                const ratio = pdfWidth / imgWidthMM;
                const pageHeightMM = (pageCanvas.height * 25.4) / (96 * 2);

                pdf.addImage(pageImgData, 'PNG',
                    margin, margin, pdfWidth, pageHeightMM * ratio);

                yPosition += pageHeightPx;
                pageNumber++;
            }
        }

        const fileName = window.billNumber ? `${window.billNumber}.pdf` : 'invoice.pdf';
        pdf.save(fileName);

        showToast('PDF downloaded successfully!', 'success');
    } catch (error) {
        console.error('PDF generation error:', error);
        showToast('Failed to generate PDF', 'error');
    }
}

// Download as JPEG with proper A4 sizing
async function downloadJPEG() {
    const element = document.getElementById('billPreview');

    if (!element) {
        showToast('Bill preview not found', 'error');
        return;
    }

    showToast('Generating image...', 'info');

    try {
        // Capture with same settings as PDF for consistency
        const canvas = await html2canvas(element, {
            scale: 2,
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff',
            windowWidth: 794,  // A4 width in pixels
            windowHeight: 1123, // A4 height in pixels
            x: 0,
            y: 0,
            scrollY: -window.scrollY,
            scrollX: -window.scrollX
        });

        // For multi-page invoices, create separate images
        const a4HeightPx = 1123 * 2; // Account for scale

        if (canvas.height <= a4HeightPx) {
            // Single page
            const link = document.createElement('a');
            link.download = window.billNumber ? `${window.billNumber}.jpg` : 'invoice.jpg';
            link.href = canvas.toDataURL('image/jpeg', 0.95);
            link.click();
            showToast('Image downloaded successfully!', 'success');
        } else {
            // Multi-page - create separate images
            const pageCount = Math.ceil(canvas.height / a4HeightPx);

            for (let i = 0; i < pageCount; i++) {
                const pageCanvas = document.createElement('canvas');
                pageCanvas.width = canvas.width;
                pageCanvas.height = Math.min(a4HeightPx, canvas.height - (i * a4HeightPx));

                const ctx = pageCanvas.getContext('2d');
                ctx.drawImage(canvas,
                    0, i * a4HeightPx, canvas.width, pageCanvas.height,
                    0, 0, canvas.width, pageCanvas.height);

                const link = document.createElement('a');
                const fileName = window.billNumber ?
                    `${window.billNumber}_page${i + 1}.jpg` :
                    `invoice_page${i + 1}.jpg`;
                link.download = fileName;
                link.href = pageCanvas.toDataURL('image/jpeg', 0.95);
                link.click();

                // Small delay between downloads
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            showToast(`${pageCount} images downloaded successfully!`, 'success');
        }
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
