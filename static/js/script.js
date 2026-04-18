document.addEventListener('DOMContentLoaded', () => {

    // --- Theme Toggle ---
    const themeToggleBtn = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');

    // Make sure we apply saved theme immediately
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    if(themeIcon) {
        themeIcon.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            if(themeIcon) {
                themeIcon.textContent = newTheme === 'dark' ? '☀️' : '🌙';
            }
        });
    }

    // --- Generate Test Logic ---
    const generateForm = document.getElementById('generate-form');
    if (generateForm) {
        const semesterSelect = document.getElementById('semester');
        const subjectSelect = document.getElementById('subject');
        const subjectGroup = document.getElementById('subject-group');
        const unitGroup = document.getElementById('unit-group');
        const unitCheckboxes = document.getElementById('unit-checkboxes');
        
        // Modal elements
        const modal = document.getElementById('loading-modal');
        const closeModal = document.querySelector('.close-modal');

        // Subject Mapping
        const subjectsData = {
            '1': [
                { name: 'COOS', displayName: 'Computer Organization And Operating System', marks: 60, units: 6 },
                { name: 'Physics', displayName: 'Engineering Physics', marks: 30, units: 4 },
                { name: 'LAUC', displayName: 'Linear Algebra and Univariate Calculus', marks: 30, units: 4 }
            ],
            '3': [
                { name: 'DSA', displayName: 'Data Structures And Algorithms', marks: 60, units: 6 }
            ]
        };

        semesterSelect.addEventListener('change', function() {
            const sem = this.value;
            subjectSelect.innerHTML = '<option value="" disabled selected>Select Subject</option>';
            subjectGroup.style.display = 'none';
            unitGroup.style.display = 'none';
            
            if (subjectsData[sem]) {
                subjectsData[sem].forEach(sub => {
                    const option = document.createElement('option');
                    option.value = sub.name; // Use short name 'DSA' for the backend
                    option.textContent = `${sub.displayName || sub.name} (${sub.marks} Marks)`; // Show full name to user
                    option.dataset.units = sub.units;
                    option.dataset.marks = sub.marks;
                    subjectSelect.appendChild(option);
                });
                subjectGroup.style.display = 'block';
            } else {
                // For other semesters (demo)
                const option = document.createElement('option');
                option.textContent = "No subjects available for this demo";
                option.disabled = true;
                subjectSelect.appendChild(option);
                subjectGroup.style.display = 'block';
            }
        });

        subjectSelect.addEventListener('change', function() {
            unitGroup.style.display = 'block';
            unitCheckboxes.innerHTML = '';
            
            const selectedOption = this.options[this.selectedIndex];
            const numUnits = parseInt(selectedOption.dataset.units);
            
            for (let i = 1; i <= numUnits; i++) {
                const div = document.createElement('div');
                div.innerHTML = `
                    <input type="checkbox" id="u${i}" name="units" value="Unit ${i}" checked>
                    <label for="u${i}">Unit ${i}</label>
                `;
                unitCheckboxes.appendChild(div);
            }
        });

        if (modal) {
            closeModal.addEventListener('click', () => {
                modal.classList.add('hidden');
            });
            window.addEventListener('click', (e) => {
                if (e.target == modal) {
                    modal.classList.add('hidden');
                }
            });
        }

        generateForm.addEventListener('submit', function(e) {
            // Show modal on submit, let form submission proceed naturally
            if (modal) modal.classList.remove('hidden');
        });
    }

    // --- Preview Page Logic Removed (Handled by Backend) ---

    // --- FAQ Accordion ---
    const acc = document.getElementsByClassName("faq-question");
    for (let i = 0; i < acc.length; i++) {
        acc[i].addEventListener("click", function() {
            this.classList.toggle("active");
            var panel = this.nextElementSibling;
            if (panel.style.maxHeight) {
                panel.style.maxHeight = null;
            } else {
                panel.style.maxHeight = panel.scrollHeight + "px";
                panel.classList.add('show');
            }
        });
    }

    // --- Feedback Character Counter & Modal ---
    const feedbackText = document.getElementById('feedback-text');
    const charCount = document.getElementById('feedback-char-count');
    
    // Modal logic
    const feedbackModal = document.getElementById('feedback-modal');
    const openFeedbackBtn = document.getElementById('give-feedback-btn');
    const closeFeedbackBtn = document.getElementById('close-feedback');

    if (openFeedbackBtn && feedbackModal) {
        openFeedbackBtn.addEventListener('click', () => {
            feedbackModal.style.display = 'block';
        });
    }

    if (closeFeedbackBtn && feedbackModal) {
        closeFeedbackBtn.addEventListener('click', () => {
            feedbackModal.style.display = 'none';
        });
    }

    if (feedbackModal) {
        window.addEventListener('click', (e) => {
            if (e.target === feedbackModal) {
                feedbackModal.style.display = 'none';
            }
        });
    }

    if (feedbackText && charCount) {
        const maxChars = Number(feedbackText.getAttribute('maxlength')) || 250;
        feedbackText.addEventListener('input', function() {
            charCount.textContent = `${this.value.length}/${maxChars} chars`;
        });
    }

    const feedbackForms = document.querySelectorAll('form[data-feedback-form="true"]');
    feedbackForms.forEach((feedbackForm) => {
        feedbackForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            try {
                const formData = new FormData(feedbackForm);
                const response = await fetch('/feedback', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (!response.ok) {
                    throw new Error(result.message || 'Failed to submit feedback.');
                }

                alert(result.message || 'Feedback submitted successfully!');
                feedbackForm.reset();
                if (charCount) {
                    const maxChars = Number(feedbackText?.getAttribute('maxlength')) || 250;
                    charCount.textContent = `0/${maxChars} chars`;
                }
                if (feedbackModal) feedbackModal.style.display = 'none';

                if (window.location.pathname === '/') {
                    window.location.reload();
                }
            } catch (error) {
                alert(error.message || 'Something went wrong while submitting feedback.');
            }
        });
    });

    // --- Image Grid Filtering logic removed ---

});
