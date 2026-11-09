const publicData = { colleges: [], departments: [], sections: [], faculty: [], periods: [], timetable: [] };

document.addEventListener('DOMContentLoaded', loadPublicTimetable);

let viewerType = 'student';

async function loadPublicTimetable() {
    const controls = document.querySelector('.public-controls');
    const viewerChoice = document.querySelector('.viewer-choice');
    if (controls && viewerChoice) controls.insertAdjacentElement('afterend', viewerChoice);

    try {
        const response = await fetch('data.json');
        if (response.ok) {
            Object.assign(publicData, await response.json());
        }
    } catch (e) {
        console.error("Could not load data.json:", e);
    }
    populatePublicFilters();
    renderPublicTimetable();
}

function populatePublicFilters() {
    renderCollegeDirectory();
    const collegeSelect = document.getElementById('filter-college');
    const departmentSelect = document.getElementById('filter-dept');
    const sectionSelect = document.getElementById('filter-section');
    const studentChoiceBtn = document.getElementById('student-choice');
    const facultyChoiceBtn = document.getElementById('faculty-choice');

    const collegeOptions = publicData.colleges.map(item => `<option value="${item.id}">${item.name}</option>`).join('');
    collegeSelect.innerHTML = '<option value="">Select college</option>' + collegeOptions;

    function syncCollegeSelection(selectedCollege) {
        collegeSelect.value = selectedCollege;
        const hasCollege = Boolean(selectedCollege);
        studentChoiceBtn.disabled = !hasCollege;
        facultyChoiceBtn.disabled = !hasCollege;

        if (!hasCollege) {
            viewerType = 'student';
            departmentSelect.innerHTML = '<option value="">Select department</option>';
            sectionSelect.disabled = true;
            sectionSelect.innerHTML = '<option value="">Select department first</option>';
            document.getElementById('filter-faculty').innerHTML = '<option value="">Select faculty</option>';
            document.querySelector('.student-filters').classList.add('hidden');
            document.querySelector('.faculty-filters').classList.add('hidden');
            document.getElementById('result-count').textContent = 'Select a college to view the timetable';
            return;
        }

        refreshDepartments();
        refreshFaculty();
        setViewerType(viewerType || 'student');
    }

    const refreshDepartments = () => {
        const collegeId = collegeSelect.value;
        const filteredDepartments = publicData.departments.filter(item => String(item.college_id) === String(collegeId));
        departmentSelect.innerHTML = '<option value="">Select department</option>' + filteredDepartments.map(item => `<option value="${item.id}">${item.name}</option>`).join('');
        sectionSelect.disabled = !departmentSelect.value;
        sectionSelect.innerHTML = '<option value="">Select batch / section</option>';
    };

    const refreshFaculty = () => {
        const collegeId = collegeSelect.value;
        const facultyOptions = publicData.faculty.filter(item => {
            const department = publicData.departments.find(dep => String(dep.id) === String(item.department_id));
            return department && String(department.college_id) === String(collegeId);
        });
        document.getElementById('filter-faculty').innerHTML = '<option value="">Select faculty</option>' + facultyOptions.map(item => `<option value="${item.id}">${item.name}</option>`).join('');
    };

    const refreshSections = () => {
        const collegeId = collegeSelect.value;
        const departmentId = departmentSelect.value;
        const filteredSections = publicData.sections.filter(item => String(item.college_id) === String(collegeId) && (!departmentId || String(item.department_id) === String(departmentId)));
        sectionSelect.disabled = !departmentId;
        sectionSelect.innerHTML = departmentId
            ? '<option value="">Select batch / section</option>' + filteredSections.map(item => `<option value="${item.id}">${item.name}</option>`).join('')
            : '<option value="">Select department first</option>';
        renderPublicTimetable();
    };

    departmentSelect.addEventListener('change', refreshSections);
    collegeSelect.addEventListener('change', () => {
        syncCollegeSelection(collegeSelect.value);
        renderPublicTimetable();
    });
    sectionSelect.addEventListener('change', renderPublicTimetable);
    document.getElementById('filter-faculty').addEventListener('change', renderPublicTimetable);
    studentChoiceBtn.addEventListener('click', () => setViewerType('student'));
    facultyChoiceBtn.addEventListener('click', () => setViewerType('faculty'));
    studentChoiceBtn.disabled = true;
    facultyChoiceBtn.disabled = true;
    syncCollegeSelection('');
}

function setViewerType(type) {
    const selectedCollege = document.getElementById('filter-college').value;
    if (!selectedCollege) {
        document.querySelector('.student-filters').classList.add('hidden');
        document.querySelector('.faculty-filters').classList.add('hidden');
        return;
    }
    viewerType = type;
    document.getElementById('student-choice').classList.toggle('active', type === 'student');
    document.getElementById('faculty-choice').classList.toggle('active', type === 'faculty');
    document.querySelector('.student-filters').classList.toggle('hidden', type !== 'student');
    document.querySelector('.faculty-filters').classList.toggle('hidden', type !== 'faculty');
    renderPublicTimetable();
}

function renderCollegeDirectory() {
    const directory = document.getElementById('college-grid');
    const count = document.getElementById('college-count');
    if (!directory || !count) return;
    count.textContent = `${publicData.colleges.length} colleges`;
    directory.innerHTML = publicData.colleges.map(c => `
        <div class="college-card">
            <img src="${c.logo_url || 'https://placehold.co/160x160/1d4ed8/ffffff?text=' + encodeURIComponent(c.short_name || 'COL')}" alt="${c.name}">
            <h3>${c.name}</h3>
            <p>${c.location || ''}</p>
            ${c.website ? `<a href="${c.website}" target="_blank" rel="noopener">Visit website &rarr;</a>` : ''}
        </div>
    `).join('');
}

function renderPublicTimetable() {
    const tbody = document.getElementById('timetable-matrix-body');
    const count = document.getElementById('result-count');
    const selectedCollege = document.getElementById('filter-college').value;
    const selectedSection = document.getElementById('filter-section').value;
    const selectedFaculty = document.getElementById('filter-faculty').value;

    if (!selectedCollege) {
        tbody.innerHTML = '<tr><td colspan="6" class="timetable-empty">Select a college to view the timetable.</td></tr>';
        count.textContent = 'Awaiting selection';
        return;
    }

    if (viewerType === 'student' && !selectedSection) {
        tbody.innerHTML = '<tr><td colspan="6" class="timetable-empty">Select a department and batch / section to view the schedule.</td></tr>';
        count.textContent = 'Awaiting section selection';
        return;
    }

    if (viewerType === 'faculty' && !selectedFaculty) {
        tbody.innerHTML = '<tr><td colspan="6" class="timetable-empty">Select a faculty member to view the assigned schedule.</td></tr>';
        count.textContent = 'Awaiting faculty selection';
        return;
    }

    const matched = publicData.timetable.filter(item => {
        if (viewerType === 'student') return String(item.section_id) === String(selectedSection);
        return String(item.faculty_id) === String(selectedFaculty);
    });

    count.textContent = `${matched.length} lecture slots scheduled`;

    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
    const slots = [
        '09:00 AM - 10:00 AM',
        '10:00 AM - 11:00 AM',
        '11:15 AM - 12:15 PM',
        '01:15 PM - 02:15 PM',
        '02:15 PM - 03:15 PM'
    ];

    tbody.innerHTML = slots.map(slot => `
        <tr>
            <td style="font-weight: 600; background: #f8fafc; color: var(--text-muted);">${slot}</td>
            ${days.map(day => {
                const entry = matched.find(item => item.day === day && item.time_slot === slot);
                if (!entry) return '<td><span class="free-slot">-- Free --</span></td>';
                const labBadge = entry.is_lab ? '<span style="background: #e0e7ff; color: #4338ca; padding: 2px 6px; border-radius: 4px; font-size: 0.72rem; font-weight: bold; margin-left: 4px;">LAB</span>' : '';
                return `
                    <td>
                        <div class="cell-card" style="border-left: 3px solid ${entry.is_lab ? '#818cf8' : 'var(--primary)'};">
                            <div style="font-weight: 700; color: #1e293b; margin-bottom: 2px;">${entry.subject_name || 'Subject'} ${labBadge}</div>
                            <div style="font-size: 0.78rem; color: #475569;">👨‍🏫 ${entry.faculty_name || 'Faculty'}</div>
                            <div style="font-size: 0.75rem; color: #64748b; margin-top: 2px;">🏛️ ${entry.classroom_name || 'Room'}</div>
                        </div>
                    </td>
                `;
            }).join('')}
        </tr>
    `).join('');
}
