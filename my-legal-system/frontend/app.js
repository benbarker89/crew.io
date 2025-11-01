// Legal Case Management System - Frontend JavaScript

const API_BASE = 'http://localhost:8000/api';
let currentCaseId = null;

// ============ UTILITY FUNCTIONS ============

function formatDate(dateString) {
    if (!dateString) return 'Not set';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });
}

function formatDateTime(dateString) {
    if (!dateString) return 'Not set';
    const date = new Date(dateString);
    return date.toLocaleString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getDaysUntil(dateString) {
    if (!dateString) return null;
    const target = new Date(dateString);
    const now = new Date();
    const diffTime = target - now;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
}

function showError(message) {
    alert('Error: ' + message);
    console.error(message);
}

function showSuccess(message) {
    alert(message);
}

// ============ DASHBOARD FUNCTIONS ============

async function loadDashboard() {
    try {
        // Load next steps
        await loadNextSteps();

        // Load active cases
        await loadActiveCases();

        // Load statistics
        await loadStatistics();
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showError('Failed to load dashboard');
    }
}

async function loadNextSteps() {
    try {
        const response = await fetch(`${API_BASE}/next-steps?limit=10`);
        const data = await response.json();

        const container = document.getElementById('nextStepsContainer');
        if (!container) return;

        if (data.next_steps && data.next_steps.length > 0) {
            container.innerHTML = data.next_steps.map(step => `
                <div class="next-step-card ${step.urgency.toLowerCase().replace(' ', '-')}">
                    <div class="next-step-header">
                        <span class="urgency-badge">${step.urgency_icon}</span>
                        <span class="urgency-label">${step.urgency}</span>
                    </div>
                    <div class="next-step-title">${step.title}</div>
                    <div class="next-step-action">${step.action}</div>
                    <div class="next-step-meta">
                        ${step.estimated_time ? `<span>⏱️ ${step.estimated_time} hours</span>` : ''}
                        ${step.due_date ? `<span>📅 Due: ${formatDateTime(step.due_date)}</span>` : ''}
                        ${step.days_until !== undefined ? `<span>📆 ${step.days_until} days</span>` : ''}
                        ${step.days_overdue !== undefined ? `<span>⚠️ ${step.days_overdue} days overdue</span>` : ''}
                    </div>
                    ${step.context ? `<div class="next-step-context">${step.context}</div>` : ''}
                    ${step.case_number ? `<div style="margin-top: 10px; font-size: 0.9em; color: #7f8c8d;">Case: ${step.case_number}</div>` : ''}
                </div>
            `).join('');
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <p>🎉 No urgent tasks! You're all caught up.</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading next steps:', error);
        document.getElementById('nextStepsContainer').innerHTML =
            '<p class="loading">Failed to load next steps</p>';
    }
}

async function loadActiveCases() {
    try {
        const response = await fetch(`${API_BASE}/cases`);
        const data = await response.json();

        const container = document.getElementById('casesContainer');
        if (!container) return;

        if (data.cases && data.cases.length > 0) {
            // Load progress for each case
            const casesWithProgress = await Promise.all(
                data.cases.map(async (caseItem) => {
                    const progressResponse = await fetch(`${API_BASE}/cases/${caseItem.id}/progress`);
                    const progressData = await progressResponse.json();
                    return { ...caseItem, progress: progressData };
                })
            );

            container.innerHTML = casesWithProgress.map(caseItem => `
                <div class="case-card priority-${caseItem.priority.toLowerCase()}">
                    <div class="case-header">
                        <span class="case-number">${caseItem.case_number}</span>
                        <span class="priority-badge priority-${caseItem.priority.toLowerCase()}">${caseItem.priority}</span>
                    </div>
                    <h3 class="case-title">${caseItem.title}</h3>
                    <p class="case-type">${caseItem.case_type} • ${caseItem.status}</p>

                    <div class="progress-section">
                        <div class="progress-label">
                            <span>Mission Progress</span>
                            <span>${caseItem.progress.overall_progress}%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${caseItem.progress.overall_progress}%"></div>
                        </div>
                        <div class="progress-label" style="margin-top: 5px;">
                            <span>${caseItem.progress.milestones_completed} of ${caseItem.progress.milestones_total} milestones</span>
                        </div>
                    </div>

                    <div class="case-actions">
                        <a href="case_view.html?id=${caseItem.id}" class="btn btn-primary btn-small">View Details</a>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <p>No active cases found</p>
                    <button class="btn btn-primary" onclick="showNewCaseModal()">Create Your First Case</button>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading cases:', error);
        document.getElementById('casesContainer').innerHTML =
            '<p class="loading">Failed to load cases</p>';
    }
}

async function loadStatistics() {
    try {
        const casesResponse = await fetch(`${API_BASE}/cases`);
        const casesData = await casesResponse.json();

        const nextStepsResponse = await fetch(`${API_BASE}/next-steps`);
        const nextStepsData = await nextStepsResponse.json();

        // Count urgent tasks
        const urgentCount = nextStepsData.next_steps.filter(
            s => s.urgency === 'URGENT' || s.urgency === 'CRITICAL'
        ).length;

        // Count upcoming deadlines (within 7 days)
        const upcomingDeadlines = nextStepsData.next_steps.filter(
            s => s.days_until !== undefined && s.days_until <= 7 && s.days_until >= 0
        ).length;

        // Update statistics
        const totalCasesEl = document.getElementById('totalCases');
        const urgentTasksEl = document.getElementById('urgentTasks');
        const upcomingDeadlinesEl = document.getElementById('upcomingDeadlines');

        if (totalCasesEl) totalCasesEl.textContent = casesData.cases.filter(c => c.status !== 'Closed').length;
        if (urgentTasksEl) urgentTasksEl.textContent = urgentCount;
        if (upcomingDeadlinesEl) upcomingDeadlinesEl.textContent = upcomingDeadlines;

    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// ============ CASE MANAGEMENT ============

function showNewCaseModal() {
    document.getElementById('newCaseModal').classList.add('show');
}

function hideNewCaseModal() {
    document.getElementById('newCaseModal').classList.remove('show');
    document.getElementById('newCaseForm').reset();
}

async function createCase(event) {
    event.preventDefault();

    const caseData = {
        case_number: document.getElementById('caseNumber').value,
        title: document.getElementById('caseTitle').value,
        case_type: document.getElementById('caseType').value,
        priority: document.getElementById('priority').value,
        mission_statement: document.getElementById('missionStatement').value
    };

    try {
        const response = await fetch(`${API_BASE}/cases`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(caseData)
        });

        const result = await response.json();

        if (result.success) {
            showSuccess('Case created successfully!');
            hideNewCaseModal();
            loadDashboard();
            window.location.href = `case_view.html?id=${result.case_id}`;
        } else {
            showError('Failed to create case');
        }
    } catch (error) {
        console.error('Error creating case:', error);
        showError('Failed to create case');
    }
}

// ============ CASE DETAILS PAGE ============

async function loadCasesList() {
    try {
        const response = await fetch(`${API_BASE}/cases`);
        const data = await response.json();

        const select = document.getElementById('caseSelect');
        if (!select) return;

        if (data.cases && data.cases.length > 0) {
            select.innerHTML = '<option value="">Select a case...</option>' +
                data.cases.map(c =>
                    `<option value="${c.id}">${c.case_number} - ${c.title}</option>`
                ).join('');

            // Check if case ID in URL
            const urlParams = new URLSearchParams(window.location.search);
            const caseId = urlParams.get('id');
            if (caseId) {
                select.value = caseId;
                loadCaseDetails();
            }
        } else {
            select.innerHTML = '<option value="">No cases found</option>';
        }
    } catch (error) {
        console.error('Error loading cases list:', error);
    }
}

async function loadCaseDetails() {
    const select = document.getElementById('caseSelect');
    const caseId = select.value;

    if (!caseId) {
        document.getElementById('caseDetailsContainer').innerHTML =
            '<p class="loading">Select a case to view details</p>';
        return;
    }

    currentCaseId = caseId;

    try {
        // Load case data
        const caseResponse = await fetch(`${API_BASE}/cases/${caseId}`);
        const caseData = await caseResponse.json();

        // Load progress
        const progressResponse = await fetch(`${API_BASE}/cases/${caseId}/progress`);
        const progressData = await progressResponse.json();

        // Render case details
        renderCaseDetails(caseData, progressData);

        // Load initial tab content
        loadMilestones(caseId);

    } catch (error) {
        console.error('Error loading case details:', error);
        showError('Failed to load case details');
    }
}

function renderCaseDetails(caseData, progressData) {
    const container = document.getElementById('caseDetailsContainer');

    container.innerHTML = `
        <div class="case-detail-header">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <div class="case-number">${caseData.case_number}</div>
                    <h2 class="case-title">${caseData.title}</h2>
                    <p class="case-type">${caseData.case_type} • ${caseData.status}</p>
                </div>
                <span class="priority-badge priority-${caseData.priority.toLowerCase()}">${caseData.priority}</span>
            </div>

            ${caseData.mission_statement ? `
                <div class="mission-statement">
                    <strong>Mission:</strong> ${caseData.mission_statement}
                </div>
            ` : ''}

            <div class="progress-section" style="margin-top: 20px;">
                <div class="progress-label">
                    <span><strong>Mission Progress</strong></span>
                    <span>${progressData.overall_progress}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${progressData.overall_progress}%"></div>
                </div>
                <div class="progress-label" style="margin-top: 5px;">
                    <span>${progressData.milestones_completed} of ${progressData.milestones_total} milestones completed</span>
                </div>
            </div>
        </div>

        <div class="tabs">
            <div class="tab active" onclick="switchTab('milestones')">Milestones</div>
            <div class="tab" onclick="switchTab('tasks')">Tasks</div>
            <div class="tab" onclick="switchTab('documents')">Documents</div>
            <div class="tab" onclick="switchTab('timeline')">Timeline</div>
            <div class="tab" onclick="switchTab('notes')">Notes</div>
        </div>

        <div id="milestones" class="tab-content active"></div>
        <div id="tasks" class="tab-content"></div>
        <div id="documents" class="tab-content"></div>
        <div id="timeline" class="tab-content"></div>
        <div id="notes" class="tab-content"></div>
    `;
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.getElementById(tabName).classList.add('active');

    // Load content based on tab
    switch(tabName) {
        case 'milestones':
            loadMilestones(currentCaseId);
            break;
        case 'tasks':
            loadTasks(currentCaseId);
            break;
        case 'documents':
            loadDocuments(currentCaseId);
            break;
        case 'timeline':
            loadTimeline(currentCaseId);
            break;
        case 'notes':
            loadNotes(currentCaseId);
            break;
    }
}

// ============ MILESTONES ============

async function loadMilestones(caseId) {
    try {
        const response = await fetch(`${API_BASE}/cases/${caseId}/milestones`);
        const data = await response.json();

        const container = document.getElementById('milestones');

        let html = `
            <div class="section-card">
                <div class="section-header">
                    <h3>Mission Milestones</h3>
                    <button class="btn btn-primary btn-small" onclick="showMilestoneModal()">+ Add Milestone</button>
                </div>
        `;

        if (data.milestones && data.milestones.length > 0) {
            html += '<div class="milestone-list">';
            data.milestones.forEach(milestone => {
                const icon = milestone.is_completed ? '✓' : (milestone.completion_percentage > 0 ? '▶' : '□');
                html += `
                    <div class="milestone-item">
                        <div class="milestone-icon">${icon}</div>
                        <div class="milestone-details">
                            <div class="milestone-title">${milestone.title}</div>
                            <div class="milestone-meta">
                                ${milestone.milestone_type}
                                ${milestone.target_date ? `• Target: ${formatDate(milestone.target_date)}` : ''}
                                ${milestone.is_completed ? `• Completed: ${formatDate(milestone.completed_date)}` : ''}
                            </div>
                        </div>
                        <div class="milestone-progress">
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${milestone.completion_percentage}%"></div>
                            </div>
                            <div style="text-align: center; margin-top: 5px; font-size: 0.9em;">
                                ${milestone.completion_percentage}%
                            </div>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
        } else {
            html += '<div class="empty-state"><p>No milestones yet. Add your first milestone!</p></div>';
        }

        html += '</div>';
        container.innerHTML = html;

    } catch (error) {
        console.error('Error loading milestones:', error);
    }
}

function showMilestoneModal() {
    document.getElementById('milestoneCaseId').value = currentCaseId;
    document.getElementById('milestoneModal').classList.add('show');
}

function hideMilestoneModal() {
    document.getElementById('milestoneModal').classList.remove('show');
    document.getElementById('newMilestoneForm').reset();
}

async function createMilestone(event) {
    event.preventDefault();

    const milestoneData = {
        case_id: parseInt(document.getElementById('milestoneCaseId').value),
        title: document.getElementById('milestoneTitle').value,
        milestone_type: document.getElementById('milestoneType').value,
        description: document.getElementById('milestoneDescription').value,
        target_date: document.getElementById('milestoneTargetDate').value || null
    };

    try {
        const response = await fetch(`${API_BASE}/milestones`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(milestoneData)
        });

        const result = await response.json();

        if (result.success) {
            showSuccess('Milestone created successfully!');
            hideMilestoneModal();
            loadMilestones(currentCaseId);
        } else {
            showError('Failed to create milestone');
        }
    } catch (error) {
        console.error('Error creating milestone:', error);
        showError('Failed to create milestone');
    }
}

// ============ TASKS ============

async function loadTasks(caseId) {
    try {
        const response = await fetch(`${API_BASE}/cases/${caseId}/tasks`);
        const data = await response.json();

        const container = document.getElementById('tasks');

        let html = `
            <div class="section-card">
                <div class="section-header">
                    <h3>Tasks & Deadlines</h3>
                    <button class="btn btn-primary btn-small" onclick="showTaskModal()">+ Add Task</button>
                </div>
        `;

        if (data.tasks && data.tasks.length > 0) {
            html += '<div class="task-list">';
            data.tasks.forEach(task => {
                const daysUntil = getDaysUntil(task.due_date);
                html += `
                    <div class="task-item priority-${task.priority.toLowerCase()}">
                        <div class="task-header">
                            <div class="task-title">${task.title}</div>
                            <span class="priority-badge priority-${task.priority.toLowerCase()}">${task.priority}</span>
                        </div>
                        ${task.description ? `<p style="margin: 8px 0; color: #7f8c8d;">${task.description}</p>` : ''}
                        <div class="task-meta">
                            <span>Status: ${task.status}</span>
                            ${task.due_date ? `<span>Due: ${formatDateTime(task.due_date)}</span>` : ''}
                            ${daysUntil !== null ? `<span>${daysUntil >= 0 ? `${daysUntil} days remaining` : `${Math.abs(daysUntil)} days overdue`}</span>` : ''}
                            ${task.estimated_hours ? `<span>${task.estimated_hours} hours</span>` : ''}
                        </div>
                    </div>
                `;
            });
            html += '</div>';
        } else {
            html += '<div class="empty-state"><p>No tasks yet. Add your first task!</p></div>';
        }

        html += '</div>';
        container.innerHTML = html;

    } catch (error) {
        console.error('Error loading tasks:', error);
    }
}

function showTaskModal() {
    document.getElementById('taskCaseId').value = currentCaseId;
    document.getElementById('taskModal').classList.add('show');
}

function hideTaskModal() {
    document.getElementById('taskModal').classList.remove('show');
    document.getElementById('newTaskForm').reset();
}

async function createTask(event) {
    event.preventDefault();

    const taskData = {
        case_id: parseInt(document.getElementById('taskCaseId').value),
        title: document.getElementById('taskTitle').value,
        description: document.getElementById('taskDescription').value,
        priority: document.getElementById('taskPriority').value,
        due_date: document.getElementById('taskDueDate').value || null,
        estimated_hours: parseFloat(document.getElementById('taskEstimatedHours').value) || null
    };

    try {
        const response = await fetch(`${API_BASE}/tasks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(taskData)
        });

        const result = await response.json();

        if (result.success) {
            showSuccess('Task created successfully!');
            hideTaskModal();
            loadTasks(currentCaseId);
            loadNextSteps(); // Refresh next steps
        } else {
            showError('Failed to create task');
        }
    } catch (error) {
        console.error('Error creating task:', error);
        showError('Failed to create task');
    }
}

// ============ DOCUMENTS ============

async function loadDocuments(caseId) {
    try {
        const response = await fetch(`${API_BASE}/cases/${caseId}/documents`);
        const data = await response.json();

        const container = document.getElementById('documents');

        let html = `
            <div class="section-card">
                <div class="section-header">
                    <h3>Documents</h3>
                    <button class="btn btn-primary btn-small" onclick="showDocumentModal()">+ Upload Document</button>
                </div>
        `;

        if (data.documents && data.documents.length > 0) {
            html += '<div class="document-list">';
            data.documents.forEach(doc => {
                html += `
                    <div class="document-item">
                        <div class="document-icon">📄</div>
                        <div class="document-name">${doc.filename}</div>
                        <div class="document-meta">
                            ${doc.category} • ${(doc.file_size / 1024).toFixed(1)} KB<br>
                            Uploaded: ${formatDate(doc.upload_date)}
                        </div>
                    </div>
                `;
            });
            html += '</div>';
        } else {
            html += '<div class="empty-state"><p>No documents yet. Upload your first document!</p></div>';
        }

        html += '</div>';
        container.innerHTML = html;

    } catch (error) {
        console.error('Error loading documents:', error);
    }
}

function showDocumentModal() {
    document.getElementById('documentCaseId').value = currentCaseId;
    document.getElementById('documentModal').classList.add('show');
}

function hideDocumentModal() {
    document.getElementById('documentModal').classList.remove('show');
    document.getElementById('uploadDocumentForm').reset();
}

async function uploadDocument(event) {
    event.preventDefault();

    const caseId = document.getElementById('documentCaseId').value;
    const category = document.getElementById('documentCategory').value;
    const file = document.getElementById('documentFile').files[0];

    if (!file) {
        showError('Please select a file');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/documents/upload?case_id=${caseId}&category=${category}`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            showSuccess('Document uploaded successfully!');
            hideDocumentModal();
            loadDocuments(currentCaseId);
        } else {
            showError('Failed to upload document');
        }
    } catch (error) {
        console.error('Error uploading document:', error);
        showError('Failed to upload document');
    }
}

// ============ TIMELINE ============

async function loadTimeline(caseId) {
    try {
        const response = await fetch(`${API_BASE}/cases/${caseId}/timeline`);
        const data = await response.json();

        const container = document.getElementById('timeline');

        let html = `
            <div class="section-card">
                <div class="section-header">
                    <h3>Case Timeline</h3>
                </div>
        `;

        if (data.events && data.events.length > 0) {
            html += '<div class="task-list">';
            data.events.forEach(event => {
                html += `
                    <div class="task-item">
                        <div class="task-header">
                            <div class="task-title">${event.is_key_event ? '⭐ ' : ''}${event.title}</div>
                            <span style="font-size: 0.9em; color: #7f8c8d;">${event.event_type}</span>
                        </div>
                        ${event.description ? `<p style="margin: 8px 0; color: #7f8c8d;">${event.description}</p>` : ''}
                        <div class="task-meta">
                            <span>${formatDateTime(event.event_date)}</span>
                            ${event.party_involved ? `<span>Party: ${event.party_involved}</span>` : ''}
                        </div>
                    </div>
                `;
            });
            html += '</div>';
        } else {
            html += '<div class="empty-state"><p>No timeline events yet.</p></div>';
        }

        html += '</div>';
        container.innerHTML = html;

    } catch (error) {
        console.error('Error loading timeline:', error);
    }
}

// ============ NOTES ============

async function loadNotes(caseId) {
    try {
        const response = await fetch(`${API_BASE}/cases/${caseId}/notes`);
        const data = await response.json();

        const container = document.getElementById('notes');

        let html = `
            <div class="section-card">
                <div class="section-header">
                    <h3>Case Notes & Journal</h3>
                    <button class="btn btn-primary btn-small" onclick="showNoteModal()">+ Add Note</button>
                </div>
        `;

        if (data.notes && data.notes.length > 0) {
            html += '<div class="note-list">';
            data.notes.forEach(note => {
                html += `
                    <div class="note-item">
                        <div class="note-header">
                            <div class="note-title">${note.title || note.note_type}</div>
                            <div class="note-date">${formatDateTime(note.created_date)}</div>
                        </div>
                        <div class="note-content">${note.content}</div>
                        ${note.tags ? `
                            <div class="note-tags">
                                ${note.tags.split(',').map(tag => `<span class="tag">${tag.trim()}</span>`).join('')}
                            </div>
                        ` : ''}
                    </div>
                `;
            });
            html += '</div>';
        } else {
            html += '<div class="empty-state"><p>No notes yet. Add your first note!</p></div>';
        }

        html += '</div>';
        container.innerHTML = html;

    } catch (error) {
        console.error('Error loading notes:', error);
    }
}

function showNoteModal() {
    document.getElementById('noteCaseId').value = currentCaseId;
    document.getElementById('noteModal').classList.add('show');
}

function hideNoteModal() {
    document.getElementById('noteModal').classList.remove('show');
    document.getElementById('newNoteForm').reset();
}

async function createNote(event) {
    event.preventDefault();

    const noteData = {
        case_id: parseInt(document.getElementById('noteCaseId').value),
        title: document.getElementById('noteTitle').value,
        note_type: document.getElementById('noteType').value,
        content: document.getElementById('noteContent').value,
        tags: document.getElementById('noteTags').value
    };

    try {
        const response = await fetch(`${API_BASE}/notes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(noteData)
        });

        const result = await response.json();

        if (result.success) {
            showSuccess('Note created successfully!');
            hideNoteModal();
            loadNotes(currentCaseId);
        } else {
            showError('Failed to create note');
        }
    } catch (error) {
        console.error('Error creating note:', error);
        showError('Failed to create note');
    }
}

// ============ PAGE INITIALIZATION ============

document.addEventListener('DOMContentLoaded', function() {
    // Check which page we're on
    if (window.location.pathname.endsWith('index.html') || window.location.pathname.endsWith('/')) {
        loadDashboard();
    } else if (window.location.pathname.endsWith('case_view.html')) {
        loadCasesList();
    }
});
