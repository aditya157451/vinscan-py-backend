/* ============================================
   AI Business Interview & Reporting System- Report Module
   ============================================ */

let reportData = null;
let clientId = null;
let pollInterval = null;

/**
 * Initialize report page
 */
async function initReport() {
    clientId = getClientId();
    
    if (!clientId) {
        showToast('Client ID not found. Please login again.', 'error');
        setTimeout(() => window.location.href = '/', 2000);
        return;
    }

    await loadReport();
}

/**
 * Load report data
 */
async function loadReport() {
    try {
        const response = await api.getReport(clientId);
        
        if (response.error && response.status === 'not_started') {
            showNoReportState();
            return;
        }

        if (response.report) {
            reportData = response.report;
            displayReport(reportData);
            
            // Stop polling if report is completed
            if (reportData.status === 'completed') {
                stopPolling();
            } else if (reportData.status === 'generating') {
                startPolling();
            }
        }
    } catch (error) {
        console.error('Error loading report:', error);
        
        // Check if it's a 404 or "not found" error
        if (error.message.includes('not found') || error.message.includes('404')) {
            showNoReportState();
        } else {
            showToast('Failed to load report', 'error');
        }
    }
}

/**
 * Display report content
 */
function displayReport(report) {
    const container = document.getElementById('report-content');
    if (!container) return;

    // Show loading state if generating
    if (report.status === 'generating') {
        container.innerHTML = `
            <div style="text-align: center; padding: var(--spacing-2xl);">
                <div class="spinner" style="margin: 0 auto var(--spacing-lg);"></div>
                <h2>Generating Your Report</h2>
                <p style="color: var(--gray-600);">This may take a few minutes. Please wait...</p>
            </div>
        `;
        return;
    }

    // Show error state if failed
    if (report.status === 'failed') {
        container.innerHTML = `
            <div class="alert alert-error">
                <strong>Report Generation Failed</strong>
                <p>There was an error generating your report. Please try again or contact support.</p>
                <button class="btn btn-primary" onclick="generateReport()">Retry Generation</button>
            </div>
        `;
        return;
    }

    // Display completed report
    let html = '';

    // Executive Summary
    if (report.summary) {
        html += `
            <section class="report-section">
                <h2>Executive Summary</h2>
                <div class="report-content-text">
                    ${formatReportText(report.summary)}
                </div>
            </section>
        `;
    }

    // Report Sections
    if (report.sections && report.sections.length > 0) {
        report.sections.forEach((section, index) => {
            html += `
                <section class="report-section" id="section-${index}">
                    <h2>${escapeHtml(section.title)}</h2>
                    <div class="report-content-text">
                        ${formatReportText(section.content)}
                    </div>
                </section>
            `;
        });
    }

    // Report metadata
    if (report.created_at) {
        html += `
            <div class="report-meta">
                <p><strong>Generated:</strong> ${formatDate(report.created_at, true)}</p>
            </div>
        `;
    }

    container.innerHTML = html;

    // Update navigation
    updateReportNavigation(report);
}

/**
 * Format report text (convert markdown-like formatting to HTML)
 */
function formatReportText(text) {
    if (!text) return '';
    
    // Escape HTML first
    let formatted = escapeHtml(text);
    
    // Convert line breaks
    formatted = formatted.replace(/\n\n/g, '</p><p>');
    formatted = formatted.replace(/\n/g, '<br>');
    
    // Wrap in paragraph tags
    formatted = `<p>${formatted}</p>`;
    
    // Convert numbered lists (1. item)
    formatted = formatted.replace(/(\d+\.\s+[^\n]+(?:\n(?!\d+\.)[^\n]+)*)/g, (match) => {
        const items = match.split(/\n(?=\d+\.)/);
        return '<ol>' + items.map(item => {
            const content = item.replace(/^\d+\.\s+/, '');
            return `<li>${content}</li>`;
        }).join('') + '</ol>';
    });
    
    // Convert bullet points (- item or * item)
    formatted = formatted.replace(/([-*]\s+[^\n]+(?:\n(?![-*])[^\n]+)*)/g, (match) => {
        const items = match.split(/\n(?=[-*])/);
        return '<ul>' + items.map(item => {
            const content = item.replace(/^[-*]\s+/, '');
            return `<li>${content}</li>`;
        }).join('') + '</ul>';
    });
    
    // Convert bold (**text** or __text__)
    formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/__([^_]+)__/g, '<strong>$1</strong>');
    
    // Convert italic (*text* or _text_)
    formatted = formatted.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>');
    formatted = formatted.replace(/(?<!_)_([^_]+)_(?!_)/g, '<em>$1</em>');
    
    return formatted;
}

/**
 * Update report navigation
 */
function updateReportNavigation(report) {
    const nav = document.getElementById('report-nav');
    if (!nav) return;

    let navHtml = '<h3>Report Sections</h3><ul>';

    // Add summary link
    if (report.summary) {
        navHtml += '<li><a href="#summary">Executive Summary</a></li>';
    }

    // Add section links
    if (report.sections) {
        report.sections.forEach((section, index) => {
            navHtml += `<li><a href="#section-${index}">${escapeHtml(section.title)}</a></li>`;
        });
    }

    navHtml += '</ul>';
    nav.innerHTML = navHtml;
}

/**
 * Show "no report" state
 */
function showNoReportState() {
    const container = document.getElementById('report-content');
    if (!container) return;

    container.innerHTML = `
        <div style="text-align: center; padding: var(--spacing-2xl);">
            <div style="font-size: 4rem; margin-bottom: var(--spacing-lg);">📄</div>
            <h2>No Report Available</h2>
            <p style="color: var(--gray-600); margin-bottom: var(--spacing-xl);">
                You haven't generated a report yet. Complete the stakeholder interviews to generate your business intelligence report.
            </p>
            <div style="display: flex; gap: var(--spacing-md); justify-content: center; flex-wrap: wrap;">
                <a href="/chat" class="btn btn-primary">Start Interview</a>
                <button class="btn btn-outline" onclick="generateReport()">Generate Report</button>
            </div>
        </div>
    `;
}

/**
 * Generate report
 */
async function generateReport() {
    if (!clientId) {
        showToast('Client ID not found', 'error');
        return;
    }

    const button = event?.target || document.querySelector('#generate-report-btn');
    if (button) {
        setLoading(button, true);
    }

    try {
        await api.generateReport(clientId);
        showToast('Report generation started! This may take a few minutes.', 'success');
        
        // Start polling for updates
        startPolling();
        
        // Show loading state
        const container = document.getElementById('report-content');
        if (container) {
            container.innerHTML = `
                <div style="text-align: center; padding: var(--spacing-2xl);">
                    <div class="spinner" style="margin: 0 auto var(--spacing-lg);"></div>
                    <h2>Generating Your Report</h2>
                    <p style="color: var(--gray-600);">This may take a few minutes. Please wait...</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error generating report:', error);
        showToast(error.message || 'Failed to start report generation', 'error');
    } finally {
        if (button) {
            setLoading(button, false);
        }
    }
}

/**
 * Start polling for report updates
 */
function startPolling() {
    // Clear any existing interval
    stopPolling();
    
    // Poll every 5 seconds
    pollInterval = setInterval(async () => {
        try {
            const response = await api.getReport(clientId);
            if (response.report) {
                reportData = response.report;
                
                if (reportData.status === 'completed') {
                    displayReport(reportData);
                    stopPolling();
                    showToast('Report generation completed!', 'success');
                } else if (reportData.status === 'failed') {
                    displayReport(reportData);
                    stopPolling();
                    showToast('Report generation failed', 'error');
                }
            }
        } catch (error) {
            console.error('Error polling report:', error);
        }
    }, 5000);
}

/**
 * Stop polling
 */
function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

/**
 * Print report
 */
function printReport() {
    window.print();
}

/**
 * Export report (download as text)
 */
function exportReport() {
    if (!reportData) {
        showToast('No report to export', 'error');
        return;
    }

    let text = 'AI Business Interview & Reporting System\n';
    text += '='.repeat(50) + '\n\n';

    if (reportData.summary) {
        text += 'EXECUTIVE SUMMARY\n';
        text += '-'.repeat(50) + '\n';
        text += reportData.summary + '\n\n';
    }

    if (reportData.sections) {
        reportData.sections.forEach(section => {
            text += section.title.toUpperCase() + '\n';
            text += '-'.repeat(50) + '\n';
            text += section.content + '\n\n';
        });
    }

    if (reportData.created_at) {
        text += '\nGenerated: ' + formatDate(reportData.created_at, true) + '\n';
    }

    // Create blob and download
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vinscan-report-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast('Report exported successfully', 'success');
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initReport);
} else {
    initReport();
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    stopPolling();
});

