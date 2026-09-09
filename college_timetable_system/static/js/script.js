let currentEntity = 'departments';
let globalData = {
    colleges: [],
    admin_users: [],
    admin_college_access: [],
    departments: [],
    sections: [],
    subjects: [],
    faculty: [],
    classrooms: [],
    periods: [],
    timetable: []
};

document.addEventListener('DOMContentLoaded', () => {
    fetchAllData();
});

const endpointMap = {
    admin_users: 'admin-users',
    admin_college_access: 'admin-college-access'
};

async function fetchAllData() {
    try {
        const endpoints = ['colleges', 'admin_users', 'admin_college_access', 'departments', 'sections', 'subjects', 'faculty', 'classrooms', 'periods', 'timetable'];
        const results = await Promise.all(endpoints.map(async (e) => {
            try {
                const route = endpointMap[e] || e;
                const res = await fetch(`/api/${route}`);
                if (!res.ok) return [];
                return await res.json();
            } catch (err) {
                return [];
            }
        }));
        
        endpoints.forEach((ep, idx) => {
            globalData[ep] = Array.isArray(results[idx]) ? results[idx] : [];
        });

        renderMasterTable();
        populateDropdowns();
        renderTimetableMatrix();
    } catch (err) {
        console.error("Failed to fetch database records:", err);
    }
}

function switchTab(tabId, event) {
    document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
    document.getElementById(`tab-${tabId}`).classList.add('active');
    if(event) event.currentTarget.classList.add('active');
}

function switchEntity(entity, event) {
    currentEntity = entity;
    document.querySelectorAll('.sub-tab').forEach(el => el.classList.remove('active'));
    if(event) event.currentTarget.classList.add('active');
    renderMasterTable();
}

function getVisibleEntityTabs() {
    const allowed = ['colleges', 'departments', 'sections', 'subjects', 'faculty', 'classrooms'];
    document.querySelectorAll('.sub-tab').forEach((el) => {
        const entity = el.textContent.trim();
        const isSuperOnly = el.textContent.includes('Admin Access') || el.textContent.includes('College Assignments');
        if (isSuperOnly) {
            el.style.display = 'none';
        } else {
            el.style.display = 'inline-flex';
        }
    });
}

// --- Master Entity Forms & Rendering ---
const entitySchemas = {
    colleges: [
        {name: 'name', label: 'College Name', type: 'text'},
        {name: 'short_name', label: 'Short Name', type: 'text'},
        {name: 'location', label: 'Location', type: 'text'},
        {name: 'logo_url', label: 'Logo URL', type: 'text'},
        {name: 'website', label: 'Website', type: 'text'},
        {name: 'is_active', label: 'Status', type: 'select', options: [{id: 1, name: 'Active'}, {id: 0, name: 'Inactive'}]}
    ],
    admin_users: [
        {name: 'username', label: 'Username', type: 'text'},
        {name: 'password', label: 'Password', type: 'password'},
        {name: 'full_name', label: 'Admin Name', type: 'text'},
        {name: 'is_super_admin', label: 'Super Admin?', type: 'select', options: [{id: 0, name: 'College Admin'}, {id: 1, name: 'Super Admin'}]},
        {name: 'college_id', label: 'Assigned College', type: 'select', ref: 'colleges'}
    ],
    admin_college_access: [
        {name: 'admin_user_id', label: 'Admin User', type: 'select', ref: 'admin_users'},
        {name: 'college_id', label: 'College', type: 'select', ref: 'colleges'}
    ],
    departments: [
        {name: 'name', label: 'Department Name', type: 'text'},
        {name: 'college_id', label: 'College', type: 'select', ref: 'colleges'}
    ],
    sections: [
        {name: 'name', label: 'Section Name', type: 'text'},
        {name: 'department_id', label: 'Department', type: 'select', ref: 'departments'},
        {name: 'college_id', label: 'College', type: 'select', ref: 'colleges'}
    ],
    subjects: [
        {name: 'name', label: 'Subject Name', type: 'text'},
        {name: 'department_id', label: 'Department', type: 'select', ref: 'departments'},
        {name: 'hours_per_week', label: 'Hours / Week', type: 'number'},
        {name: 'is_lab', label: 'Is Lab Requirement?', type: 'select', options: [{id: 0, name: 'No'}, {id: 1, name: 'Yes'}]}
    ],
    faculty: [
        {name: 'name', label: 'Faculty Name', type: 'text'},
        {name: 'department_id', label: 'Department', type: 'select', ref: 'departments'},
        {name: 'subject_id', label: 'Subject', type: 'select', ref: 'subjects'},
        {name: 'availability', label: 'Availability Profile', type: 'text'}
    ],
    classrooms: [
        {name: 'name', label: 'Room / Lab Name', type: 'text'},
        {name: 'is_lab', label: 'Room Type', type: 'select', options: [{id: 0, name: 'Standard Classroom'}, {id: 1, name: 'Computer/Science Lab'}]},
        {name: 'capacity', label: 'Seating Capacity', type: 'number'}
    ]
};

function renderMasterTable() {
    const schema = entitySchemas[currentEntity];
    const formFields = document.getElementById('form-fields');
    formFields.innerHTML = '';

    schema.forEach(field => {
        let inputHTML = '';
        if (field.type === 'select') {
            let optionsHTML = '';
            if (field.ref) {
                const refList = globalData[field.ref] || [];
                if (currentEntity === 'admin_users' && field.name === 'college_id') {
                    optionsHTML = '<option value="">No college assignment</option>';
                }
                optionsHTML += refList.map(item => `<option value="${item.id}">${item.name || item.username || item.full_name || item.id}</option>`).join('');
            } else if (field.options) {
                optionsHTML = field.options.map(opt => `<option value="${opt.id}">${opt.name}</option>`).join('');
            }
            const required = currentEntity === 'admin_users' && field.name === 'college_id' ? '' : ' required';
            inputHTML = `<select id="field-${field.name}"${required}>${optionsHTML}</select>`;
        } else {
            inputHTML = `<input type="${field.type}" id="field-${field.name}" ${field.type === 'password' ? 'placeholder="Leave blank to keep current password"' : ''} required>`;
        }
        formFields.innerHTML += `<div class="form-group"><label>${field.label}</label>${inputHTML}</div>`;
    });

    const thead = document.getElementById('table-head');
    const tbody = document.getElementById('table-body');
    let items = globalData[currentEntity] || [];
    if (currentEntity === 'admin_users') {
        items = items.map(item => ({
            ...item,
            college_id: globalData.admin_college_access.find(access => access.admin_user_id == item.id)?.college_id || ''
        }));
    }
    if (currentEntity === 'departments') {
        const selectedCollegeId = document.getElementById('field-college_id')?.value;
        if (selectedCollegeId) {
            items = items.filter(item => String(item.college_id) === String(selectedCollegeId));
        }
    }
    if (currentEntity === 'admin_users') items = items.map(item => ({ ...item, password_hash: undefined }));

    if (items.length === 0) {
        thead.innerHTML = `<tr><th>Records</th></tr>`;
        tbody.innerHTML = `<tr><td>No records found. Add one above.</td></tr>`;
        return;
    }

    const keys = Object.keys(items[0]).filter(key => key !== 'password_hash');
    thead.innerHTML = `<tr>${keys.map(k => `<th>${k.toUpperCase()}</th>`).join('')}<th>ACTIONS</th></tr>`;
    tbody.innerHTML = items.map(item => `
        <tr>
            ${keys.map(k => `<td>${item[k] === 1 || item[k] === 0 ? (item[k] === 1 ? 'Yes' : 'No') : (item[k] ?? '')}</td>`).join('')}
            <td>
                <button class="btn btn-warning" onclick='editRecord(${JSON.stringify(item)})'>Edit</button>
                <button class="btn btn-danger" onclick="deleteRecord('${currentEntity}', ${item.id})">Delete</button>
            </td>
        </tr>
    `).join('');
}

function resetForm() {
    document.getElementById('entity-id').value = '';
    document.getElementById('entity-form').reset();
}

function editRecord(item) {
    document.getElementById('entity-id').value = item.id;
    Object.keys(item).forEach(k => {
        const el = document.getElementById(`field-${k}`);
        if(el) el.value = item[k];
    });
}

async function handleFormSubmit(event) {
    event.preventDefault();
    const id = document.getElementById('entity-id').value;
    const schema = entitySchemas[currentEntity];
    let payload = {};
    if (id) payload.id = parseInt(id);

    schema.forEach(field => {
        const element = document.getElementById(`field-${field.name}`);
        if (!element) return;
        const val = element.value;
        if (field.name === 'password' && !val) return;
        payload[field.name] = field.type === 'number' || field.type === 'select' ? (val === '' ? val : (isNaN(val) ? val : parseInt(val))) : val;
    });

    if (currentEntity === 'admin_users' && payload.password) {
        payload.password = payload.password.trim();
    }
    const assignedCollegeId = currentEntity === 'admin_users' ? payload.college_id : null;
    if (currentEntity === 'admin_users') delete payload.college_id;

    const endpoint = endpointMap[currentEntity] || currentEntity;
    const method = id ? 'PUT' : 'POST';
    const response = await fetch(`/api/${endpoint}`, {
        method: method,
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });

    if (currentEntity === 'admin_users' && response.ok) {
        const result = await response.json();
        const adminUserId = id ? parseInt(id) : result.id;
        const previousAssignments = globalData.admin_college_access.filter(access => access.admin_user_id == adminUserId);
        await Promise.all(previousAssignments.map(access => fetch(`/api/admin-college-access?id=${access.id}`, {method: 'DELETE'})));
        if (adminUserId && assignedCollegeId) {
            await fetch('/api/admin-college-access', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({admin_user_id: adminUserId, college_id: parseInt(assignedCollegeId)})
            });
        }
    }

    resetForm();
    fetchAllData();
}

async function deleteRecord(entity, id) {
    if(!confirm("Are you sure you want to delete this record?")) return;
    const endpoint = endpointMap[entity] || entity;
    await fetch(`/api/${endpoint}?id=${id}`, {method: 'DELETE'});
    fetchAllData();
}

// --- AI Timetable Generation ---
async function generateAITimetable() {
    const btn = document.querySelector('.ai-control-box button');
    btn.textContent = "AI Optimizing Constraints...";
    btn.disabled = true;

    try {
        const res = await fetch('/api/generate-ai-timetable', {method: 'POST'});
        const data = await res.json();
        
        if(res.ok) {
            document.getElementById('score-display').innerText = `${data.score} / 100`;
            document.getElementById('conflict-display').innerText = data.conflicts_detected === 0 ? "Zero Conflicts" : `${data.conflicts_detected} Warnings`;
            
            const suggList = document.getElementById('suggestion-list');
            suggList.innerHTML = data.suggestions.map(s => `<li>${s}</li>`).join('');
            
            alert(`Timetables generated for ${data.colleges_generated || 1} college${(data.colleges_generated || 1) === 1 ? '' : 's'} using AI Constraint Optimization!`);
            fetchAllData();
        } else {
            alert(data.message || "Optimization failed.");
        }
    } catch(err) {
        console.error(err);
        alert("Server communication error.");
    } finally {
        btn.textContent = "🚀 Generate AI Timetable";
        btn.disabled = false;
    }
}

// --- Filter & Timetable Matrix ---
function populateDropdowns() {
    const collegeSel = document.getElementById('filter-college');

    collegeSel.innerHTML = '<option value="">Select a college</option>' + globalData.colleges.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    renderDepartmentFilter();
    renderDependentFilters();
}

function renderDepartmentFilter() {
    const collegeSel = document.getElementById('filter-college');
    const deptSel = document.getElementById('filter-dept');
    if (!collegeSel || !deptSel) return;

    const selectedCollege = collegeSel.value;
    const currentDepartment = deptSel.value;
    const departments = selectedCollege
        ? globalData.departments.filter(d => String(d.college_id) === String(selectedCollege))
        : globalData.departments.filter((department, index, all) => all.findIndex(item => item.name === department.name) === index);
    const selectedValue = selectedCollege
        ? currentDepartment
        : (departments.some(d => d.name === currentDepartment) ? currentDepartment : '');

    deptSel.innerHTML = '<option value="">All Departments</option>' + departments.map(d => {
        const value = selectedCollege ? d.id : d.name;
        return `<option value="${value}">${d.name}</option>`;
    }).join('');
    deptSel.value = selectedValue;
    deptSel.disabled = !selectedCollege;
}

function renderDependentFilters() {
    const collegeSel = document.getElementById('filter-college');
    const deptSel = document.getElementById('filter-dept');
    const secSel = document.getElementById('filter-section');
    const facSel = document.getElementById('filter-faculty');
    if (!collegeSel || !deptSel || !secSel || !facSel) return;

    const collegeId = collegeSel.value;
    const departmentId = deptSel.value;
    const sections = collegeId
        ? globalData.sections.filter(section => String(section.college_id) === String(collegeId) && (!departmentId || String(section.department_id) === String(departmentId)))
        : [];
    const faculty = collegeId
        ? globalData.faculty.filter(member => {
            const department = globalData.departments.find(item => item.id == member.department_id);
            return department && String(department.college_id) === String(collegeId) && (!departmentId || String(member.department_id) === String(departmentId));
        })
        : [];

    const currentSection = secSel.value;
    const currentFaculty = facSel.value;
    secSel.innerHTML = '<option value="">All Sections</option>' + sections.map(section => `<option value="${section.id}">${section.name}</option>`).join('');
    facSel.innerHTML = '<option value="">All Faculty</option>' + faculty.map(member => `<option value="${member.id}">${member.name}</option>`).join('');
    secSel.value = sections.some(section => String(section.id) === currentSection) ? currentSection : '';
    facSel.value = faculty.some(member => String(member.id) === currentFaculty) ? currentFaculty : '';
    secSel.disabled = !collegeId;
    facSel.disabled = !collegeId;
}

function renderTimetableMatrix() {
    const tbody = document.getElementById('timetable-matrix-body');
    const periods = globalData.periods;
    const timetable = globalData.timetable;

    const filterCollege = document.getElementById('filter-college') ? document.getElementById('filter-college').value : '';
    const filterDept = document.getElementById('filter-dept').value;
    const filterSec = document.getElementById('filter-section').value;
    const filterFac = document.getElementById('filter-faculty').value;

    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
    const timeSlots = [...new Set(periods.map(p => p.time_slot))];
    const matchesForSelection = timetable.filter(t => {
        const section = globalData.sections.find(s => s.id == t.section_id) || {};
        const dept = globalData.departments.find(d => d.id == section.department_id) || {};
        return (!filterCollege || (t.college_id != null && t.college_id == filterCollege) || (!t.college_id && section.college_id == filterCollege)) &&
               (!filterDept || dept.id == filterDept || dept.name == filterDept) &&
               (!filterSec || t.section_id == filterSec) &&
               (!filterFac || t.faculty_id == filterFac);
    });

    if (!filterCollege) {
        tbody.innerHTML = `<tr><td colspan="6" class="timetable-empty">Select a college to view its timetable.</td></tr>`;
        return;
    }

    if(timeSlots.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6">No time slots configuration found.</td></tr>`;
        return;
    }

    if (matchesForSelection.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="timetable-empty">No published timetable for this selection.</td></tr>`;
        return;
    }

    tbody.innerHTML = timeSlots.map(slot => {
        let rowHTML = `<tr><td><strong>${slot}</strong></td>`;
        days.forEach(day => {
            const matches = matchesForSelection.filter(t => {
                const p = periods.find(per => per.id === t.period_id);
                const section = globalData.sections.find(s => s.id == t.section_id) || {};
                const dept = globalData.departments.find(d => d.id == section.department_id) || {};
                return p && p.day === day && p.time_slot === slot &&
                       (!filterCollege || (t.college_id != null && t.college_id == filterCollege) || (!t.college_id && section.college_id == filterCollege)) &&
                       (!filterDept || dept.id == filterDept || dept.name == filterDept) &&
                       (!filterSec || t.section_id == filterSec) &&
                       (!filterFac || t.faculty_id == filterFac);
            });

            if (matches.length > 0) {
                rowHTML += `<td>` + matches.map(m => `
                    <div class="cell-card">
                        <strong>${m.subject_name}</strong><br>
                        👨‍🏫 ${m.faculty_name}<br>
                        🏫 ${m.classroom_name}<br>
                        🏷️ ${m.section_name}
                    </div>
                `).join('<hr style="margin:4px 0">') + `</td>`;
            } else {
                rowHTML += `<td><span style="color:#cbd5e1; font-size:0.8rem">Free / Unassigned</span></td>`;
            }
        });
        rowHTML += `</tr>`;
        return rowHTML;
    }).join('');
}

function filterTimetable() {
    renderDepartmentFilter();
    renderDependentFilters();
    renderTimetableMatrix();
}