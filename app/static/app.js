// API Configuration
const API_BASE = window.location.origin.includes(':8000') ? '' : 'http://localhost:8000';

// UI Elements & State
let activePostId = null;
let activeAssistPostId = null;
let carouselSlides = [];
let activeSlideIndex = 0;
let allPosts = [];
let calendarDate = new Date();
let selectedCalendarKey = null;
let supabaseClient = null;

const el = {
    // Form & Inputs
    generatorForm: document.getElementById('generator-form'),
    postTitle: document.getElementById('post-title'),
    postType: document.getElementById('post-type'),
    slidesCountGroup: document.getElementById('slides-count-group'),
    slidesCount: document.getElementById('slides-count'),
    urlContainer: document.getElementById('url-container'),
    addUrlBtn: document.getElementById('add-url-btn'),
    autoSearchToggle: document.getElementById('auto-search-toggle'),
    autoSearchCountGroup: document.getElementById('auto-search-count-group'),
    autoSearchCount: document.getElementById('auto-search-count'),
    roughDraft: document.getElementById('rough-draft'),
    additionalContext: document.getElementById('additional-context'),
    styleSelect: document.getElementById('style-select'),
    scheduleTime: document.getElementById('schedule-time'),
    generateBtn: document.getElementById('generate-btn'),
    generateSpinner: document.getElementById('generate-spinner'),

    // Preview
    previewPlaceholder: document.getElementById('preview-placeholder'),
    postPreview: document.getElementById('post-preview'),
    postContentBody: document.getElementById('post-content-body'),
    carouselPreview: document.getElementById('carousel-preview'),
    slideCard: document.getElementById('slide-card'),
    slideNum: document.getElementById('slide-num'),
    slideTitle: document.getElementById('slide-title'),
    slideContent: document.getElementById('slide-content'),
    prevSlideBtn: document.getElementById('prev-slide-btn'),
    nextSlideBtn: document.getElementById('next-slide-btn'),
    slideIndicator: document.getElementById('slide-indicator'),
    copyBtn: document.getElementById('copy-btn'),
    regenerateBtn: document.getElementById('regenerate-btn'),
    downloadPdfBtn: document.getElementById('download-pdf-btn'),
    sourcesSection: document.getElementById('sources-section'),
    sourcesList: document.getElementById('sources-list'),

    // Refinement
    refinementSection: document.getElementById('refinement-section'),
    refinementForm: document.getElementById('refinement-form'),
    refinementInstruction: document.getElementById('refinement-instruction'),
    refineBtn: document.getElementById('refine-btn'),
    refineSpinner: document.getElementById('refine-spinner'),

    // History
    historyList: document.getElementById('history-list'),

    // Calendar Modal
    openCalendarBtn: document.getElementById('open-calendar-btn'),
    calendarModal: document.getElementById('calendar-modal'),
    closeCalendarBtn: document.getElementById('close-calendar-btn'),
    calPrevBtn: document.getElementById('cal-prev-btn'),
    calNextBtn: document.getElementById('cal-next-btn'),
    calTodayBtn: document.getElementById('cal-today-btn'),
    calMonthLabel: document.getElementById('cal-month-label'),
    calendarGrid: document.getElementById('calendar-grid'),
    calendarDayDetail: document.getElementById('calendar-day-detail'),
    calDetailDate: document.getElementById('cal-detail-date'),
    calDetailPosts: document.getElementById('cal-detail-posts'),

    // Style Templates Modal
    manageStylesBtn: document.getElementById('manage-styles-btn'),
    stylesModal: document.getElementById('styles-modal'),
    closeModalBtn: document.getElementById('close-modal-btn'),
    templateForm: document.getElementById('template-form'),
    templateName: document.getElementById('template-name'),
    templateContent: document.getElementById('template-content'),
    templatesList: document.getElementById('templates-list'),

    // Tab Navigation
    tabBar: document.getElementById('tab-bar'),

    // Assist View
    assistForm: document.getElementById('assist-form'),
    assistTitle: document.getElementById('assist-title'),
    assistDraft: document.getElementById('assist-draft'),
    assistAdditionalContext: document.getElementById('assist-additional-context'),
    assistUrlContainer: document.getElementById('assist-url-container'),
    assistAddUrlBtn: document.getElementById('assist-add-url-btn'),
    assistAutoSearchToggle: document.getElementById('assist-auto-search-toggle'),
    assistAutoSearchCountGroup: document.getElementById('assist-auto-search-count-group'),
    assistAutoSearchCount: document.getElementById('assist-auto-search-count'),
    assistStyleSelect: document.getElementById('assist-style-select'),
    assistManageStylesBtn: document.getElementById('assist-manage-styles-btn'),
    assistNewBtn: document.getElementById('assist-new-btn'),
    assistSaveBtn: document.getElementById('assist-save-btn'),
    assistRunBtn: document.getElementById('assist-run-btn'),
    assistSpinner: document.getElementById('assist-spinner'),
    assistPlaceholder: document.getElementById('assist-placeholder'),
    assistResults: document.getElementById('assist-results'),
    assistFactCheckList: document.getElementById('assist-fact-check-list'),
    assistStructuredDraft: document.getElementById('assist-structured-draft'),
    assistSuggestionsList: document.getElementById('assist-suggestions-list'),
    assistTemplate: document.getElementById('assist-template'),

    // Toast
    toast: document.getElementById('toast'),

    // Auth / Login Gate
    loginView: document.getElementById('login-view'),
    appShell: document.getElementById('app-shell'),
    loginSigninStep: document.getElementById('login-signin-step'),
    loginPassphraseStep: document.getElementById('login-passphrase-step'),
    googleSigninBtn: document.getElementById('google-signin-btn'),
    passphraseForm: document.getElementById('passphrase-form'),
    passphraseInput: document.getElementById('passphrase-input'),
    passphraseSpinner: document.getElementById('passphrase-spinner'),
    logoutBtn: document.getElementById('logout-btn')
};

// --- Helper Functions ---

function showToast(message, type = 'info') {
    el.toast.textContent = message;
    el.toast.className = `toast-web show ${type}`;
    setTimeout(() => {
        el.toast.classList.remove('show');
    }, 4000);
}

// --- Auth-aware fetch ---

async function getAccessToken() {
    if (!supabaseClient) return null;
    const { data } = await supabaseClient.auth.getSession();
    return data?.session?.access_token || null;
}

// Wraps fetch() with the current Supabase access token attached, since every
// /api/* route (other than /api/config) now requires authentication.
async function apiFetch(path, options = {}) {
    const token = await getAccessToken();
    const headers = { ...(options.headers || {}) };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return fetch(`${API_BASE}${path}`, { ...options, headers });
}

function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

// --- Tab Navigation ---

function switchView(viewName) {
    document.querySelectorAll('.app-view').forEach(v => v.classList.remove('active'));
    const target = document.getElementById(`view-${viewName}`);
    if (target) target.classList.add('active');
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.view === viewName));
}

el.tabBar.addEventListener('click', (e) => {
    const btn = e.target.closest('.tab-btn');
    if (btn) switchView(btn.dataset.view);
});

function formatMarkdown(text) {
    if (!text) return "";
    let formatted = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    
    // Bold matches
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    return formatted;
}

// Convert date string to readable local string
function formatDisplayDate(dateStr) {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    return date.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

// Check backend connectivity
async function checkSystemStatus() {
    const apiStatus = document.getElementById('api-status');
    try {
        const res = await apiFetch(`/api/style-templates`);
        if (res.ok) {
            apiStatus.innerHTML = '<i class="fa-solid fa-circle-check"></i> System Online';
            apiStatus.className = 'status-badge connected';
        } else {
            throw new Error();
        }
    } catch {
        apiStatus.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Offline';
        apiStatus.className = 'status-badge disconnected';
        showToast("Cannot connect to backend server. Make sure FastAPI is running.", "error");
    }
}

// --- Dynamic Form URLs ---

function addUrlRow(container) {
    const row = document.createElement('div');
    row.className = 'url-input-row';
    row.innerHTML = `
        <input type="url" class="source-url" placeholder="https://example.com/article">
        <button type="button" class="btn-icon remove-url"><i class="fa-solid fa-trash"></i></button>
    `;
    container.appendChild(row);

    // Bind remove button
    row.querySelector('.remove-url').addEventListener('click', () => {
        row.remove();
    });
}

el.addUrlBtn.addEventListener('click', () => addUrlRow(el.urlContainer));
el.assistAddUrlBtn.addEventListener('click', () => addUrlRow(el.assistUrlContainer));

// Show/hide auto-search source count based on checkbox
el.autoSearchToggle.addEventListener('change', (e) => {
    el.autoSearchCountGroup.style.display = e.target.checked ? 'block' : 'none';
});
el.assistAutoSearchToggle.addEventListener('change', (e) => {
    el.assistAutoSearchCountGroup.style.display = e.target.checked ? 'block' : 'none';
});

// Show/hide slides input based on post type select
el.postType.addEventListener('change', (e) => {
    if (e.target.value === 'carousel') {
        el.slidesCountGroup.style.display = 'block';
    } else {
        el.slidesCountGroup.style.display = 'none';
    }
});

// --- API Integrations: Style Templates ---

async function fetchStyles() {
    try {
        const res = await apiFetch(`/api/style-templates`);
        const templates = await res.json();
        
        // Populate dropdowns (Create + Assist both offer the same style templates)
        el.styleSelect.innerHTML = '<option value="">No template (Standard LinkedIn Copywriter)</option>';
        el.assistStyleSelect.innerHTML = '<option value="">No template</option>';
        templates.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.id;
            opt.textContent = t.name;
            el.styleSelect.appendChild(opt);
            el.assistStyleSelect.appendChild(opt.cloneNode(true));
        });

        // Populate modal list
        el.templatesList.innerHTML = '';
        if (templates.length === 0) {
            el.templatesList.innerHTML = '<p class="text-muted">No custom style templates created yet.</p>';
        } else {
            templates.forEach(t => {
                const item = document.createElement('div');
                item.className = 'template-item';
                item.innerHTML = `
                    <div class="template-info">
                        <h4>${t.name}</h4>
                        <p>${t.content}</p>
                    </div>
                    <button type="button" class="btn-icon delete-template" data-id="${t.id}"><i class="fa-solid fa-trash"></i></button>
                `;
                el.templatesList.appendChild(item);

                // Add delete action
                item.querySelector('.delete-template').addEventListener('click', async () => {
                    if (confirm(`Delete style template "${t.name}"?`)) {
                        await deleteStyleTemplate(t.id);
                    }
                });
            });
        }
    } catch (err) {
        showToast("Error loading style templates", "error");
    }
}

async function createStyleTemplate(name, content) {
    try {
        const res = await apiFetch(`/api/style-templates`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, content })
        });
        if (res.ok) {
            showToast("Style template saved successfully!", "success");
            el.templateName.value = '';
            el.templateContent.value = '';
            await fetchStyles();
        } else {
            const data = await res.json();
            showToast(data.detail || "Failed to create style template", "error");
        }
    } catch (err) {
        showToast("Error creating style template", "error");
    }
}

async function deleteStyleTemplate(id) {
    try {
        const res = await apiFetch(`/api/style-templates/${id}`, { method: 'DELETE' });
        if (res.ok) {
            showToast("Template deleted", "success");
            await fetchStyles();
        } else {
            showToast("Failed to delete template", "error");
        }
    } catch (err) {
        showToast("Error deleting style template", "error");
    }
}

// Modal controls
el.manageStylesBtn.addEventListener('click', () => el.stylesModal.classList.add('active'));
el.assistManageStylesBtn.addEventListener('click', () => el.stylesModal.classList.add('active'));
el.closeModalBtn.addEventListener('click', () => el.stylesModal.classList.remove('active'));
el.stylesModal.addEventListener('click', (e) => {
    if (e.target === el.stylesModal) el.stylesModal.classList.remove('active');
});

el.templateForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await createStyleTemplate(el.templateName.value, el.templateContent.value);
});

// --- API Integrations: Posts & Generation ---

async function fetchHistory() {
    try {
        const res = await apiFetch(`/api/posts`);
        const posts = await res.json();
        allPosts = posts;

        el.historyList.innerHTML = '';
        if (posts.length === 0) {
            el.historyList.innerHTML = '<p class="no-history">No posts generated yet.</p>';
            return;
        }

        posts.forEach(p => {
            const item = document.createElement('div');
            item.className = 'history-item';
            
            let badgeClass = p.status.toLowerCase();
            let detailsText = p.type === 'carousel' ? 'Visual Carousel' : 'Post';
            if (p.scheduled_time) {
                detailsText += ` • Scheduled ${formatDisplayDate(p.scheduled_time)}`;
            } else {
                detailsText += ` • Created ${formatDisplayDate(p.created_at)}`;
            }

            item.innerHTML = `
                <div class="history-meta" style="cursor: pointer;">
                    <div class="history-title">${p.title || 'Untitled Generation'}</div>
                    <div class="history-details">
                        <span class="badge-status ${badgeClass}">${p.status}</span>
                        <span>${detailsText}</span>
                    </div>
                </div>
                <div class="history-actions">
                    <button class="btn-icon delete-post" data-id="${p.id}"><i class="fa-solid fa-trash"></i></button>
                </div>
            `;

            // Click metadata to load
            item.querySelector('.history-meta').addEventListener('click', () => {
                openPostFromHistory(p);
            });

            // Click delete
            item.querySelector('.delete-post').addEventListener('click', async (e) => {
                e.stopPropagation();
                if (confirm(`Delete post "${p.title || 'Untitled'}"?`)) {
                    await deletePost(p.id);
                }
            });

            el.historyList.appendChild(item);
        });
    } catch (err) {
        showToast("Error loading history list", "error");
    }
}

async function deletePost(id) {
    try {
        const res = await apiFetch(`/api/posts/${id}`, { method: 'DELETE' });
        if (res.ok) {
            showToast("Post deleted successfully", "success");
            if (activePostId === id) {
                resetPreview();
            }
            await fetchHistory();
        } else {
            showToast("Failed to delete post", "error");
        }
    } catch (err) {
        showToast("Error deleting post", "error");
    }
}

// --- Content Calendar ---

function dateKey(d) {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

// A post's "calendar date" is when it's scheduled to publish, or when it was created if never scheduled.
function postEffectiveDate(p) {
    return new Date(p.scheduled_time || p.created_at);
}

function openCalendarModal() {
    calendarDate = new Date();
    selectedCalendarKey = null;
    el.calendarDayDetail.style.display = 'none';
    renderCalendar();
    el.calendarModal.classList.add('active');
}

function renderCalendar() {
    const year = calendarDate.getFullYear();
    const month = calendarDate.getMonth();

    el.calMonthLabel.textContent = calendarDate.toLocaleString([], { month: 'long', year: 'numeric' });

    // Group posts by their local calendar day
    const postsByDate = {};
    allPosts.forEach(p => {
        const key = dateKey(postEffectiveDate(p));
        if (!postsByDate[key]) postsByDate[key] = [];
        postsByDate[key].push(p);
    });

    const firstOfMonth = new Date(year, month, 1);
    const startOffset = firstOfMonth.getDay(); // 0 = Sunday
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const totalCells = Math.ceil((startOffset + daysInMonth) / 7) * 7;

    const todayKey = dateKey(new Date());

    el.calendarGrid.innerHTML = '';
    for (let i = 0; i < totalCells; i++) {
        const cellDate = new Date(year, month, i - startOffset + 1);
        const key = dateKey(cellDate);
        const isOtherMonth = cellDate.getMonth() !== month;
        const dayPosts = postsByDate[key] || [];

        const cell = document.createElement('div');
        cell.className = 'calendar-day';
        if (isOtherMonth) cell.classList.add('other-month');
        if (key === todayKey) cell.classList.add('today');
        if (key === selectedCalendarKey) cell.classList.add('selected');

        let dotsHtml = '';
        const visibleDots = dayPosts.slice(0, 4);
        visibleDots.forEach(p => {
            dotsHtml += `<span class="calendar-dot ${p.status.toLowerCase()}"></span>`;
        });
        if (dayPosts.length > 4) {
            dotsHtml += `<span class="calendar-dot-overflow">+${dayPosts.length - 4}</span>`;
        }

        cell.innerHTML = `
            <span class="calendar-day-num">${cellDate.getDate()}</span>
            <div class="calendar-day-dots">${dotsHtml}</div>
        `;

        cell.addEventListener('click', () => selectCalendarDay(key, cellDate, dayPosts));
        el.calendarGrid.appendChild(cell);
    }
}

function selectCalendarDay(key, dateObj, dayPosts) {
    selectedCalendarKey = key;
    renderCalendar();

    el.calendarDayDetail.style.display = 'block';
    el.calDetailDate.textContent = dateObj.toLocaleString([], { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });

    if (dayPosts.length === 0) {
        el.calDetailPosts.innerHTML = '<p class="calendar-detail-empty">No content scheduled or created on this day.</p>';
        return;
    }

    el.calDetailPosts.innerHTML = '';
    dayPosts.forEach(p => {
        const item = document.createElement('div');
        item.className = 'history-item';
        const timeLabel = p.scheduled_time ? `Scheduled ${formatDisplayDate(p.scheduled_time)}` : `Created ${formatDisplayDate(p.created_at)}`;
        item.innerHTML = `
            <div class="history-meta" style="cursor: pointer;">
                <div class="history-title">${p.title || 'Untitled Generation'}</div>
                <div class="history-details">
                    <span class="badge-status ${p.status.toLowerCase()}">${p.status}</span>
                    <span>${timeLabel}</span>
                </div>
            </div>
        `;
        item.querySelector('.history-meta').addEventListener('click', () => {
            openPostFromHistory(p);
            el.calendarModal.classList.remove('active');
        });
        el.calDetailPosts.appendChild(item);
    });
}

el.openCalendarBtn.addEventListener('click', openCalendarModal);
el.closeCalendarBtn.addEventListener('click', () => el.calendarModal.classList.remove('active'));
el.calendarModal.addEventListener('click', (e) => {
    if (e.target === el.calendarModal) el.calendarModal.classList.remove('active');
});
el.calPrevBtn.addEventListener('click', () => {
    calendarDate = new Date(calendarDate.getFullYear(), calendarDate.getMonth() - 1, 1);
    renderCalendar();
});
el.calNextBtn.addEventListener('click', () => {
    calendarDate = new Date(calendarDate.getFullYear(), calendarDate.getMonth() + 1, 1);
    renderCalendar();
});
el.calTodayBtn.addEventListener('click', () => {
    calendarDate = new Date();
    selectedCalendarKey = null;
    el.calendarDayDetail.style.display = 'none';
    renderCalendar();
});

// Render selected post in the preview pane
function loadPostToPreview(post) {
    activePostId = post.id;
    
    // Toggle previews
    el.previewPlaceholder.style.display = 'none';
    el.refinementSection.style.display = 'block';
    el.copyBtn.removeAttribute('disabled');
    
    if (post.type === 'carousel') {
        el.postPreview.style.display = 'none';
        el.carouselPreview.style.display = 'flex';
        el.downloadPdfBtn.style.display = 'inline-flex';

        try {
            carouselSlides = JSON.parse(post.content || "[]");
        } catch {
            carouselSlides = [{ slide: 1, title: "Error", content: "Could not parse carousel slides JSON" }];
        }

        activeSlideIndex = 0;
        renderSlide();
    } else {
        el.carouselPreview.style.display = 'none';
        el.postPreview.style.display = 'block';
        el.downloadPdfBtn.style.display = 'none';
        el.postContentBody.innerHTML = formatMarkdown(post.content || "");
    }

    // Render the list of web sources used for this generation, if any
    if (Array.isArray(post.web_sources) && post.web_sources.length > 0) {
        el.sourcesList.innerHTML = post.web_sources.map(url => `
            <li><a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(url)}</a></li>
        `).join('');
        el.sourcesSection.style.display = 'block';
    } else {
        el.sourcesList.innerHTML = '';
        el.sourcesSection.style.display = 'none';
    }

    // Scroll to preview on mobile/smaller screens
    el.postPreview.scrollIntoView({ behavior: 'smooth' });
}

function renderSlide() {
    if (carouselSlides.length === 0) return;
    
    const slide = carouselSlides[activeSlideIndex];
    el.slideNum.textContent = `${slide.slide} / ${carouselSlides.length}`;
    el.slideTitle.textContent = slide.title || "";
    
    // Formats body bullet points/text inside the slide
    let bodyHtml = "";
    if (Array.isArray(slide.content)) {
        bodyHtml = slide.content.map(p => `<p>${p}</p>`).join("");
    } else {
        // split on newlines or bullet symbols for pretty presentation
        const points = slide.content.split('\n');
        bodyHtml = points.map(p => `<p>${p}</p>`).join("");
    }
    el.slideContent.innerHTML = bodyHtml;
    el.slideIndicator.textContent = `Slide ${slide.slide} of ${carouselSlides.length}`;

    // Manage buttons disabling
    el.prevSlideBtn.disabled = activeSlideIndex === 0;
    el.nextSlideBtn.disabled = activeSlideIndex === carouselSlides.length - 1;

    // Apply micro-animation class triggers
    el.slideCard.style.transform = 'scale(0.98)';
    setTimeout(() => {
        el.slideCard.style.transform = 'scale(1)';
    }, 150);
}

// Carousel Controls
el.prevSlideBtn.addEventListener('click', () => {
    if (activeSlideIndex > 0) {
        activeSlideIndex--;
        renderSlide();
    }
});
el.nextSlideBtn.addEventListener('click', () => {
    if (activeSlideIndex < carouselSlides.length - 1) {
        activeSlideIndex++;
        renderSlide();
    }
});

function resetPreview() {
    activePostId = null;
    carouselSlides = [];
    activeSlideIndex = 0;
    el.previewPlaceholder.style.display = 'block';
    el.postPreview.style.display = 'none';
    el.carouselPreview.style.display = 'none';
    el.refinementSection.style.display = 'none';
    el.copyBtn.setAttribute('disabled', 'true');
    el.downloadPdfBtn.style.display = 'none';
    el.sourcesSection.style.display = 'none';
    el.sourcesList.innerHTML = '';
}

// Dispatches a history item to whichever tab can display it, since Assist-mode
// drafts (advisory, non-destructive) and Generate-mode posts render completely differently.
function openPostFromHistory(p) {
    if (p.mode === 'assist') {
        loadAssistPost(p);
        switchView('assist');
    } else {
        loadPostToPreview(p);
        switchView('create');
    }
}

// --- Assist Mode (non-destructive editorial assistance) ---

function resetAssistView() {
    activeAssistPostId = null;
    el.assistTitle.value = '';
    el.assistDraft.value = '';
    el.assistAdditionalContext.value = '';
    el.assistUrlContainer.innerHTML = `
        <div class="url-input-row">
            <input type="url" class="source-url" placeholder="https://example.com/article">
            <button type="button" class="btn-icon remove-url" style="display:none;"><i class="fa-solid fa-trash"></i></button>
        </div>
    `;
    el.assistAutoSearchToggle.checked = false;
    el.assistAutoSearchCountGroup.style.display = 'none';
    el.assistStyleSelect.value = '';
    el.assistPlaceholder.style.display = 'block';
    el.assistResults.style.display = 'none';
}

function loadAssistPost(post) {
    activeAssistPostId = post.id;
    el.assistTitle.value = post.title || '';
    el.assistDraft.value = post.rough_draft || '';
    el.assistAdditionalContext.value = post.additional_context || '';
    el.assistStyleSelect.value = post.style_template_id || '';
    el.assistAutoSearchToggle.checked = !!post.auto_search_count;
    el.assistAutoSearchCountGroup.style.display = post.auto_search_count ? 'block' : 'none';
    if (post.auto_search_count) el.assistAutoSearchCount.value = post.auto_search_count;

    const urls = post.web_sources || [];
    el.assistUrlContainer.innerHTML = '';
    if (urls.length === 0) {
        addUrlRow(el.assistUrlContainer);
    } else {
        urls.forEach(url => {
            addUrlRow(el.assistUrlContainer);
            el.assistUrlContainer.lastElementChild.querySelector('.source-url').value = url;
        });
    }

    if (post.assist_result) {
        renderAssistResult(post.assist_result);
    } else {
        el.assistPlaceholder.style.display = 'block';
        el.assistResults.style.display = 'none';
    }
}

function renderAssistResult(result) {
    el.assistPlaceholder.style.display = 'none';
    el.assistResults.style.display = 'block';

    const verdictIcon = {
        supported: 'fa-circle-check',
        unsupported: 'fa-circle-xmark',
        conflicting: 'fa-triangle-exclamation',
        unverified: 'fa-circle-question'
    };
    el.assistFactCheckList.innerHTML = (result.fact_check || []).map(fc => `
        <li class="fact-check-item verdict-${fc.verdict}">
            <i class="fa-solid ${verdictIcon[fc.verdict] || 'fa-circle-question'}"></i>
            <div>
                <p class="fact-check-claim">${escapeHtml(fc.claim)}</p>
                <p class="fact-check-note">${escapeHtml(fc.note)}</p>
                ${fc.source ? (/^https?:\/\//i.test(fc.source)
                    ? `<a href="${escapeHtml(fc.source)}" target="_blank" rel="noopener noreferrer">${escapeHtml(fc.source)}</a>`
                    : `<span class="fact-check-source-label">${escapeHtml(fc.source)}</span>`) : ''}
            </div>
        </li>
    `).join('') || '<li class="no-history">No factual claims identified.</li>';

    el.assistStructuredDraft.innerHTML = formatMarkdown(result.structured_draft || '');

    el.assistSuggestionsList.innerHTML = (result.suggestions || []).map(s => `
        <li class="suggestion-item suggestion-${s.type}"><span class="suggestion-type">${escapeHtml(s.type)}</span> ${escapeHtml(s.detail)}</li>
    `).join('') || '<li class="no-history">No suggestions.</li>';

    el.assistTemplate.textContent = result.template || '';
}

function collectAssistPayload() {
    const urls = Array.from(el.assistUrlContainer.querySelectorAll('.source-url'))
        .map(input => input.value.trim())
        .filter(url => url !== "");

    return {
        title: el.assistTitle.value.trim() || null,
        rough_draft: el.assistDraft.value.trim() || null,
        additional_context: el.assistAdditionalContext.value.trim() || null,
        web_sources: urls.length > 0 ? urls : null,
        auto_search_count: el.assistAutoSearchToggle.checked ? parseInt(el.assistAutoSearchCount.value) : null,
        style_template_id: el.assistStyleSelect.value ? parseInt(el.assistStyleSelect.value) : null
    };
}

// Creates the assist-mode draft on first save, then patches it in place afterward.
async function saveAssistDraft() {
    const payload = collectAssistPayload();
    try {
        let res;
        if (activeAssistPostId) {
            res = await apiFetch(`/api/posts/${activeAssistPostId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } else {
            res = await apiFetch(`/api/posts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...payload, type: 'post', mode: 'assist' })
            });
        }
        if (res.ok) {
            const post = await res.json();
            activeAssistPostId = post.id;
            await fetchHistory();
            return post;
        }
        const errData = await res.json();
        showToast(errData.detail || "Failed to save draft", "error");
    } catch (err) {
        showToast("Error communicating with backend server", "error");
    }
    return null;
}

el.assistNewBtn.addEventListener('click', () => {
    resetAssistView();
    showToast("Started a new draft", "info");
});

el.assistSaveBtn.addEventListener('click', async () => {
    const post = await saveAssistDraft();
    if (post) showToast("Draft saved", "success");
});

el.assistRunBtn.addEventListener('click', async () => {
    if (!el.assistDraft.value.trim()) {
        showToast("Write a draft first", "error");
        return;
    }

    el.assistRunBtn.disabled = true;
    el.assistSpinner.style.display = 'inline-block';
    el.assistRunBtn.querySelector('.btn-text-content').style.opacity = '0.5';

    try {
        const saved = await saveAssistDraft();
        if (!saved) return;

        const res = await apiFetch(`/api/posts/${activeAssistPostId}/assist`, { method: 'POST' });
        if (res.ok) {
            const post = await res.json();
            renderAssistResult(post.assist_result);
            await fetchHistory();
            showToast("Editorial feedback ready", "success");
        } else {
            const errData = await res.json();
            showToast(errData.detail || "Failed to get AI assist", "error");
        }
    } catch (err) {
        showToast("Error communicating with backend server", "error");
    } finally {
        el.assistRunBtn.disabled = false;
        el.assistSpinner.style.display = 'none';
        el.assistRunBtn.querySelector('.btn-text-content').style.opacity = '1';
    }
});

// Generic copy-to-clipboard for any advisory section (Suggested Structure, Template)
document.addEventListener('click', (e) => {
    const btn = e.target.closest('.copy-section-btn');
    if (!btn) return;
    const target = document.getElementById(btn.dataset.target);
    if (!target) return;
    navigator.clipboard.writeText(target.innerText).then(() => {
        showToast("Copied to clipboard!", "success");
    }).catch(() => {
        showToast("Failed to copy", "error");
    });
});

// Form Submission (Create and Generate Post)
el.generatorForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Check configuration
    const title = el.postTitle.value.trim();
    const type = el.postType.value;
    const rough_draft = el.roughDraft.value.trim() || null;
    const additional_context = el.additionalContext.value.trim() || null;
    
    // Extract Web Sources list
    const urls = Array.from(el.urlContainer.querySelectorAll('.source-url'))
        .map(input => input.value.trim())
        .filter(url => url !== "");
    
    const style_template_id = el.styleSelect.value ? parseInt(el.styleSelect.value) : null;

    const auto_search_count = el.autoSearchToggle.checked ? parseInt(el.autoSearchCount.value) : null;

    // Scheduled time
    let scheduled_time = null;
    if (el.scheduleTime.value) {
        // Convert local datetime-local value to ISO UTC string
        scheduled_time = new Date(el.scheduleTime.value).toISOString();
    }

    // Set UI Loading State
    el.generateBtn.disabled = true;
    el.generateSpinner.style.display = 'inline-block';
    el.generateBtn.querySelector('.btn-text-content').style.opacity = '0.5';

    try {
        const payload = {
            title,
            type,
            rough_draft,
            additional_context,
            web_sources: urls.length > 0 ? urls : null,
            auto_search_count,
            style_template_id,
            scheduled_time
        };

        const res = await apiFetch(`/api/posts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            const post = await res.json();
            await fetchHistory();
            
            if (scheduled_time) {
                showToast(`Post scheduled successfully for ${formatDisplayDate(scheduled_time)}!`, "success");
                el.generatorForm.reset();
                // Clear any added dynamic URL rows
                el.urlContainer.innerHTML = `
                    <div class="url-input-row">
                        <input type="url" class="source-url" placeholder="https://example.com/article">
                        <button type="button" class="btn-icon remove-url" style="display:none;"><i class="fa-solid fa-trash"></i></button>
                    </div>
                `;
                el.autoSearchCountGroup.style.display = 'none';
                resetPreview();
            } else {
                showToast("Post generated successfully!", "success");
                loadPostToPreview(post);
            }
        } else {
            const errData = await res.json();
            showToast(errData.detail || "Failed to generate content", "error");
        }
    } catch (err) {
        showToast("Error communicating with backend server", "error");
    } finally {
        el.generateBtn.disabled = false;
        el.generateSpinner.style.display = 'none';
        el.generateBtn.querySelector('.btn-text-content').style.opacity = '1';
    }
});

// Refinement submission
el.refinementForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!activePostId) return;

    const instruction = el.refinementInstruction.value.trim();
    if (!instruction) return;

    el.refineBtn.disabled = true;
    el.refineSpinner.style.display = 'inline-block';
    el.refineBtn.querySelector('.btn-text-content').style.opacity = '0.5';

    try {
        const res = await apiFetch(`/api/posts/${activePostId}/refine`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ instruction })
        });

        if (res.ok) {
            const post = await res.json();
            showToast("Post refined successfully!", "success");
            el.refinementInstruction.value = '';
            loadPostToPreview(post);
            await fetchHistory();
        } else {
            const errData = await res.json();
            showToast(errData.detail || "Failed to refine post", "error");
        }
    } catch (err) {
        showToast("Error processing refinement request", "error");
    } finally {
        el.refineBtn.disabled = false;
        el.refineSpinner.style.display = 'none';
        el.refineBtn.querySelector('.btn-text-content').style.opacity = '1';
    }
});

// Copy to clipboard actions
el.copyBtn.addEventListener('click', () => {
    if (!activePostId) return;
    
    let copyText = "";
    if (el.postPreview.style.display === 'block') {
        copyText = el.postContentBody.innerText;
    } else if (el.carouselPreview.style.display === 'flex') {
        // Copy carousel formatted text
        copyText = carouselSlides.map(slide => {
            const bulletText = Array.isArray(slide.content) 
                ? slide.content.join('\n') 
                : slide.content;
            return `[Slide ${slide.slide}] ${slide.title}\n${bulletText}\n`;
        }).join('\n---\n\n');
    }

    navigator.clipboard.writeText(copyText).then(() => {
        showToast("Content copied to clipboard!", "success");
    }).catch(err => {
        showToast("Failed to copy content", "error");
    });
});

// Download rendered carousel slides as a LinkedIn-ready PDF.
// Can't use window.open() directly since the endpoint now requires an
// Authorization header a plain navigation can't carry - fetch the bytes
// ourselves and trigger the download from a blob URL instead.
el.downloadPdfBtn.addEventListener('click', async () => {
    if (!activePostId) return;
    const res = await apiFetch(`/api/posts/${activePostId}/carousel.pdf`);
    if (!res.ok) {
        showToast("Failed to download PDF", "error");
        return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `carousel_${activePostId}.pdf`;
    link.click();
    URL.revokeObjectURL(url);
});

// --- Theme Toggle Management ---
function initTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;

    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
        themeToggle.innerHTML = '<i class="fa-solid fa-moon"></i>';
    } else {
        document.body.classList.remove('light-theme');
        themeToggle.innerHTML = '<i class="fa-solid fa-sun"></i>';
    }

    themeToggle.addEventListener('click', () => {
        const isLight = document.body.classList.toggle('light-theme');
        if (isLight) {
            localStorage.setItem('theme', 'light');
            themeToggle.innerHTML = '<i class="fa-solid fa-moon"></i>';
            showToast("Switched to Light Mode", "info");
        } else {
            localStorage.setItem('theme', 'dark');
            themeToggle.innerHTML = '<i class="fa-solid fa-sun"></i>';
            showToast("Switched to Dark Mode", "info");
        }
    });
}

// --- Auth / Login Gate ---

async function initSupabase() {
    try {
        const res = await fetch(`${API_BASE}/api/config`);
        const config = await res.json();
        if (!config.supabase_url || !config.supabase_anon_key) {
            showToast("Supabase is not configured on the server yet", "error");
            return null;
        }
        return window.supabase.createClient(config.supabase_url, config.supabase_anon_key);
    } catch (err) {
        showToast("Error communicating with backend server", "error");
        return null;
    }
}

function showLoginView() {
    el.appShell.style.display = 'none';
    el.loginView.style.display = 'flex';
    el.loginSigninStep.style.display = 'block';
    el.loginPassphraseStep.style.display = 'none';
}

function showPassphraseStep() {
    el.loginView.style.display = 'flex';
    el.appShell.style.display = 'none';
    el.loginSigninStep.style.display = 'none';
    el.loginPassphraseStep.style.display = 'block';
}

// Loading posts/styles/history is idempotent but no need to repeat it if
// onAuthStateChange and the initial session check both resolve to a signed-in,
// approved user around the same time.
let appShellLoaded = false;
async function showAppShell() {
    el.loginView.style.display = 'none';
    el.appShell.style.display = 'block';
    if (appShellLoaded) return;
    appShellLoaded = true;
    await checkSystemStatus();
    await fetchStyles();
    await fetchHistory();
}

// Checks the signed-in user's invite-passphrase approval status and shows the right view.
async function handleAuthenticatedSession() {
    const res = await apiFetch('/api/auth/me');
    if (!res.ok) {
        let detail = `HTTP ${res.status}`;
        try {
            const errData = await res.json();
            if (errData.detail) detail = `${detail}: ${errData.detail}`;
        } catch (_) { /* non-JSON error body */ }
        console.error('/api/auth/me failed:', detail);
        showToast(`Sign-in failed (${detail})`, "error");
        showLoginView();
        return;
    }
    const profile = await res.json();
    if (profile.is_approved) {
        await showAppShell();
    } else {
        showPassphraseStep();
    }
}

el.googleSigninBtn.addEventListener('click', async () => {
    if (!supabaseClient) return;
    await supabaseClient.auth.signInWithOAuth({ provider: 'google' });
});

el.passphraseForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const passphrase = el.passphraseInput.value.trim();
    if (!passphrase) return;

    const submitBtn = el.passphraseForm.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    el.passphraseSpinner.style.display = 'inline-block';

    try {
        const res = await apiFetch('/api/auth/approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ passphrase })
        });
        if (res.ok) {
            showToast("Access granted!", "success");
            await showAppShell();
        } else {
            const errData = await res.json();
            showToast(errData.detail || "Incorrect passphrase", "error");
        }
    } catch (err) {
        showToast("Error communicating with backend server", "error");
    } finally {
        submitBtn.disabled = false;
        el.passphraseSpinner.style.display = 'none';
    }
});

el.logoutBtn.addEventListener('click', async () => {
    if (supabaseClient) await supabaseClient.auth.signOut();
    appShellLoaded = false;
    el.passphraseInput.value = '';
    showLoginView();
});

// --- Startup Initialization ---

window.addEventListener('DOMContentLoaded', async () => {
    initTheme();

    supabaseClient = await initSupabase();
    if (!supabaseClient) {
        showLoginView();
        return;
    }

    const { data: { session } } = await supabaseClient.auth.getSession();
    if (session) {
        await handleAuthenticatedSession();
    } else {
        showLoginView();
    }

    supabaseClient.auth.onAuthStateChange(async (event, newSession) => {
        if (event === 'SIGNED_IN' && newSession) {
            await handleAuthenticatedSession();
        } else if (event === 'SIGNED_OUT') {
            appShellLoaded = false;
            showLoginView();
        }
    });
});
