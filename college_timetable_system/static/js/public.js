const publicData = { colleges: [], departments: [], sections: [], faculty: [], periods: [], timetable: [] };

document.addEventListener('DOMContentLoaded', loadPublicTimetable);

let viewerType = 'student';

async function loadPublicTimetable() {
    const controls = document.querySelector('.public-controls');
    const viewerChoice = document.querySelector('.viewer-choice');
    if (controls && viewerChoice) controls.insertAdjacentElement('afterend', viewerChoice);

    const response = await fetch('/api/public-timetable');
    if (!response.ok) return;
    Object.assign(publicData, await response.json());
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
        const filteredDepartments = publicData.departments.filter(item => item.college_id == collegeId);
        departmentSelect.innerHTML = '<option value="">Select department</option>' + filteredDepartments.map(item => `<option value="${item.id}">${item.name}</option>`).join('');
        sectionSelect.disabled = !departmentSelect.value;
        sectionSelect.innerHTML = '<option value="">Select batch / section</option>';
    };

    const refreshFaculty = () => {
        const collegeId = collegeSelect.value;
        const facultyOptions = publicData.faculty.filter(item => {
            const department = publicData.departments.find(dep => dep.id === item.department_id);
            return department && department.college_id == collegeId;
        });
        document.getElementById('filter-faculty').innerHTML = '<option value="">Select faculty</option>' + facultyOptions.map(item => `<option value="${item.id}">${item.name}</option>`).join('');
    };

    const refreshSections = () => {
        const collegeId = collegeSelect.value;
        const departmentId = departmentSelect.value;
        const filteredSections = publicData.sections.filter(item => item.college_id == collegeId && (!departmentId || item.department_id == departmentId));
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
    const grid = document.getElementById('college-grid');
    document.getElementById('college-count').textContent = `${publicData.colleges.length} colleges`;
    grid.innerHTML = publicData.colleges.map(college => `
        <article class="college-card">
            <img src="${college.logo_url || 'https://placehold.co/120x120/4f46e5/ffffff?text=' + encodeURIComponent((college.short_name || college.name || 'COL').slice(0, 4))}" alt="${college.name} logo" />
            <h3>${college.name}</h3>
            <p>${college.location || 'Location unavailable'}</p>
            <a href="${college.website || '#'}" target="_blank" rel="noreferrer">Visit website</a>
        </article>
    `).join('');
}

function renderPublicTimetable() {
    const selectedCollege = document.getElementById('filter-college').value;
    if (!selectedCollege) {
        document.getElementById('result-count').textContent = 'Select a college to view the timetable';
        document.getElementById('timetable-matrix-body').innerHTML = '<tr><td colspan="6">Choose a college to see the timetable.</td></tr>';
        return;
    }

    const departmentId = document.getElementById('filter-dept').value;
    const sectionId = document.getElementById('filter-section').value;
    const facultyId = document.getElementById('filter-faculty').value;
    const filtered = publicData.timetable.filter(item => {
        const matchesCollege = item.college_id == selectedCollege;
        if (viewerType === 'student') {
            return matchesCollege && (!departmentId || item.department_id == departmentId) && (!sectionId || item.section_id == sectionId);
        }
        return matchesCollege && (!facultyId || item.faculty_id == facultyId);
    });
    const slots = [...new Set(publicData.periods.map(item => item.time_slot))];
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
    const hasSelection = viewerType === 'student' ? (sectionId || departmentId || selectedCollege) : (facultyId || selectedCollege);
    document.getElementById('result-count').textContent = hasSelection ? `${filtered.length} published classes` : 'Select a college to view the timetable';
    document.getElementById('timetable-matrix-body').innerHTML = slots.map(slot => `<tr><td><strong>${slot}</strong></td>${days.map(day => {
        const matches = filtered.filter(item => item.day === day && item.time_slot === slot);
        return `<td>${matches.length ? matches.map(item => `<div class="cell-card"><strong>${item.subject_name}</strong><br>${item.faculty_name}<br>${item.classroom_name}<br>${item.section_name}</div>`).join('') : '<span class="free-slot">Free</span>'}</td>`;
    }).join('')}</tr>`).join('');
}