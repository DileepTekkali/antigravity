/**
 * Invoice Pagination JavaScript
 * Handles automatic page breaks for A4 invoices
 */

class InvoicePaginator {
    constructor() {
        this.A4_HEIGHT_MM = 297;
        this.A4_WIDTH_MM = 210;
        this.MARGIN_MM = 20;
        this.USABLE_HEIGHT_MM = this.A4_HEIGHT_MM - (2 * this.MARGIN_MM); // 257mm

        // Percentage allocations
        this.HEADER_PERCENT = 0.20;
        this.CUSTOMER_PERCENT = 0.10;
        this.ITEMS_PERCENT = 0.50;
        this.TOTALS_PERCENT = 0.10;
        this.SIGNATURE_PERCENT = 0.10;

        // Calculate heights in mm
        this.HEADER_HEIGHT = this.USABLE_HEIGHT_MM * this.HEADER_PERCENT; // ~51mm
        this.CUSTOMER_HEIGHT = this.USABLE_HEIGHT_MM * this.CUSTOMER_PERCENT; // ~26mm
        this.ITEMS_HEIGHT = this.USABLE_HEIGHT_MM * this.ITEMS_PERCENT; // ~128mm
        this.TOTALS_HEIGHT = this.USABLE_HEIGHT_MM * this.TOTALS_PERCENT; // ~26mm
        this.SIGNATURE_HEIGHT = this.USABLE_HEIGHT_MM * this.SIGNATURE_PERCENT; // ~26mm

        this.FIXED_SECTIONS_HEIGHT = this.HEADER_HEIGHT + this.CUSTOMER_HEIGHT +
            this.TOTALS_HEIGHT + this.SIGNATURE_HEIGHT; // ~129mm
        this.AVAILABLE_ITEMS_HEIGHT = this.USABLE_HEIGHT_MM - this.FIXED_SECTIONS_HEIGHT; // ~128mm
    }

    mmToPx(mm) {
        // Approximate conversion: 1mm ≈ 3.78px at 96 DPI
        return mm * 3.78;
    }

    pxToMm(px) {
        return px / 3.78;
    }

    checkPagination() {
        const itemsTable = document.querySelector('.items-section table tbody');
        if (!itemsTable) return;

        const rows = Array.from(itemsTable.querySelectorAll('tr'));
        if (rows.length === 0) return;

        // Calculate total height of items
        let totalItemsHeight = 0;
        rows.forEach(row => {
            totalItemsHeight += row.offsetHeight;
        });

        const totalItemsHeightMm = this.pxToMm(totalItemsHeight);

        // Check if items exceed available space
        if (totalItemsHeightMm > this.AVAILABLE_ITEMS_HEIGHT) {
            console.log(`Items overflow detected: ${totalItemsHeightMm.toFixed(2)}mm > ${this.AVAILABLE_ITEMS_HEIGHT.toFixed(2)}mm`);
            this.splitIntoPages(rows);
        } else {
            console.log(`Items fit on one page: ${totalItemsHeightMm.toFixed(2)}mm <= ${this.AVAILABLE_ITEMS_HEIGHT.toFixed(2)}mm`);
        }
    }

    splitIntoPages(rows) {
        // This would split items across multiple pages
        // For now, we'll just add a warning
        console.warn('Multi-page invoice detected. Items may overflow.');

        // Add a visual indicator
        const itemsSection = document.querySelector('.items-section');
        if (itemsSection && !document.querySelector('.pagination-warning')) {
            const warning = document.createElement('div');
            warning.className = 'pagination-warning';
            warning.style.cssText = `
                background: #fef3c7;
                border: 1px solid #f59e0b;
                color: #92400e;
                padding: 12px;
                border-radius: 6px;
                margin-bottom: 16px;
                font-size: 14px;
            `;
            warning.innerHTML = `
                <strong>⚠️ Multi-page invoice:</strong> This invoice has many items. 
                When printing, ensure your printer settings are set to A4 and page breaks are enabled.
            `;
            itemsSection.insertBefore(warning, itemsSection.firstChild);
        }
    }

    ensureSignatureOnLastPage() {
        // Ensure signature section has page-break-inside: avoid
        const signatureSection = document.querySelector('.signature-section');
        if (signatureSection) {
            signatureSection.style.pageBreakInside = 'avoid';
            signatureSection.style.breakInside = 'avoid';
        }

        // Ensure totals and signature stay together
        const totalsSection = document.querySelector('.totals-section');
        if (totalsSection) {
            totalsSection.style.pageBreakInside = 'avoid';
            totalsSection.style.breakInside = 'avoid';
        }
    }
}

// Initialize pagination checker when page loads
document.addEventListener('DOMContentLoaded', function () {
    const paginator = new InvoicePaginator();
    paginator.checkPagination();
    paginator.ensureSignatureOnLastPage();

    // Re-check on window resize
    let resizeTimeout;
    window.addEventListener('resize', function () {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            paginator.checkPagination();
        }, 250);
    });
});

// Export for use in other scripts
window.InvoicePaginator = InvoicePaginator;
