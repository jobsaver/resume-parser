// Resume Parser Demo Frontend JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Common Elements
    const statusIndicator = document.getElementById('status');
    
    // Auth elements
    const userIdInput = document.getElementById('userId');
    const tokenInput = document.getElementById('token');
    
    // Extract Only Tab Elements
    const dropAreaExtract = document.getElementById('drop-area-extract');
    const fileInputExtract = document.getElementById('fileUploadExtract');
    const extractOnlyBtn = document.getElementById('extractOnlyBtn');
    const extractProgress = document.getElementById('extractProgress');
    const extractProgressBar = extractProgress.querySelector('.progress-bar');
    const extractResultsSection = document.getElementById('extractResultsSection');
    const extractShowRawTextBtn = document.getElementById('extractShowRawText');
    const extractRawTextSection = document.getElementById('extractRawTextSection');
    const extractRawText = document.getElementById('extractRawText');
    
    // Save Resume Tab Elements
    const dropAreaSave = document.getElementById('drop-area-save');
    const fileInputSave = document.getElementById('fileUploadSave');
    const saveResumeBtn = document.getElementById('saveResumeBtn');
    const saveProgress = document.getElementById('saveProgress');
    const saveProgressBar = saveProgress.querySelector('.progress-bar');
    const saveResultsSection = document.getElementById('saveResultsSection');
    const resumeIdInput = document.getElementById('resumeId');
    const resumeFormatInput = document.getElementById('resumeFormat');
    const resumeUrlInput = document.getElementById('resumeUrl');
    const viewFullContentBtn = document.getElementById('viewFullContent');
    const fullContentSection = document.getElementById('fullContentSection');
    const fullContent = document.getElementById('fullContent');
    
    // Add a small notification about token authentication
    const authSection = document.querySelector('.auth-section');
    if (authSection) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-info small mt-2';
        alert.innerHTML = 'Using token authentication. The default values match what\'s configured in your .env file.<br>In production, tokens should be kept secret.';
        authSection.appendChild(alert);
    }
    
    // Only show token partially
    if (tokenInput) {
        const originalToken = tokenInput.value;
        // Add an event listener to toggle showing full token on click
        tokenInput.addEventListener('focus', function() {
            tokenInput.type = 'text';
            tokenInput.value = originalToken;
        });
        
        tokenInput.addEventListener('blur', function() {
            if (tokenInput.value === originalToken) {
                tokenInput.type = 'password';
                // Show only first and last 4 characters
                const masked = originalToken.substring(0, 4) + '...' + 
                            originalToken.substring(originalToken.length - 4);
                tokenInput.placeholder = masked;
            }
        });
        
        // Trigger blur initially to mask token
        tokenInput.type = 'password';
        const masked = originalToken.substring(0, 4) + '...' + 
                    originalToken.substring(originalToken.length - 4);
        tokenInput.placeholder = masked;
    }
    
    // Add drag and drop functionality for Extract Only
    setupDragAndDrop(dropAreaExtract, fileInputExtract);
    
    // Add drag and drop functionality for Save Resume
    setupDragAndDrop(dropAreaSave, fileInputSave);
    
    // Function to set up drag and drop
    function setupDragAndDrop(dropArea, fileInput) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        // Highlight drop area when dragging over it
        dropArea.addEventListener('dragenter', () => highlight(dropArea));
        dropArea.addEventListener('dragover', () => highlight(dropArea));
        
        // Remove highlight when leaving or after drop
        dropArea.addEventListener('dragleave', () => unhighlight(dropArea));
        dropArea.addEventListener('drop', () => unhighlight(dropArea));
        
        function highlight(element) {
            element.classList.add('highlight');
        }
        
        function unhighlight(element) {
            element.classList.remove('highlight');
        }
        
        // Handle file drop
        dropArea.addEventListener('drop', function(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                fileInput.files = files;
                // Display selected file name
                dropArea.querySelector('p').textContent = `Selected: ${files[0].name}`;
            }
        }, false);
        
        // Handle click on dropzone
        dropArea.addEventListener('click', () => {
            fileInput.click();
        });
        
        // Handle file selection via input
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                dropArea.querySelector('p').textContent = `Selected: ${fileInput.files[0].name}`;
            }
        });
    }
    
    // Handle extract only button click
    extractOnlyBtn.addEventListener('click', function() {
        console.log('Extract Only button clicked');
        extractResumeOnly();
    });
    
    // Handle save resume button click
    saveResumeBtn.addEventListener('click', function() {
        console.log('Save Resume button clicked');
        saveResume();
    });
    
    // Handle raw text toggle for extract only
    extractShowRawTextBtn.addEventListener('click', () => {
        extractRawTextSection.classList.toggle('d-none');
    });
    
    // Handle full content toggle for save resume
    viewFullContentBtn.addEventListener('click', () => {
        fullContentSection.classList.toggle('d-none');
    });
    
    // Extract resume without saving to database
    function extractResumeOnly() {
        const file = fileInputExtract.files[0];
        if (!file) {
            alert('Please select a PDF file first.');
            return;
        }
        
        console.log('File selected:', file.name);
        
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            alert('Only PDF files are supported.');
            return;
        }
        
        // Update status
        setStatus('Extracting...', 'warning');
        console.log('Status updated to Extracting');
        
        // Show progress
        extractProgress.classList.remove('d-none');
        extractProgressBar.style.width = '25%';
        
        // Create form data
        const formData = new FormData();
        formData.append('resume', file);
        
        // Send request to extract-only endpoint
        fetch('/api/extract-only', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            extractProgressBar.style.width = '75%';
            return response.json();
        })
        .then(data => {
            console.log('Response received:', data);
            extractProgressBar.style.width = '100%';
            
            if (data.success) {
                displayExtractResults(data.data);
                setStatus('Success', 'success');
            } else {
                alert('Error: ' + data.error);
                setStatus('Error', 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error: ' + error.message);
            setStatus('Error', 'danger');
        })
        .finally(() => {
            setTimeout(() => {
                extractProgress.classList.add('d-none');
                extractProgressBar.style.width = '0%';
            }, 500);
        });
    }
    
    // Save resume to database
    function saveResume() {
        const file = fileInputSave.files[0];
        if (!file) {
            alert('Please select a PDF file first.');
            return;
        }
        
        console.log('File selected:', file.name);
        
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            alert('Only PDF files are supported.');
            return;
        }
        
        const userId = userIdInput.value.trim();
        const token = tokenInput.value.trim();
        
        console.log('Authentication:', { userId, token: '***' });
        
        if (!userId || !token) {
            alert('Please provide both User ID and Token for authentication.');
            return;
        }
        
        // Get additional parameters
        const resumeId = resumeIdInput.value.trim();
        const format = resumeFormatInput.value;
        const resumeUrl = resumeUrlInput.value.trim();
        
        // Update status
        setStatus('Saving...', 'warning');
        console.log('Status updated to Saving');
        
        // Show progress
        saveProgress.classList.remove('d-none');
        saveProgressBar.style.width = '25%';
        
        // Create form data
        const formData = new FormData();
        formData.append('resume', file);
        formData.append('user_id', userId);
        formData.append('token', token);
        
        if (resumeId) {
            formData.append('resume_id', resumeId);
        }
        
        formData.append('format', format);
        
        if (resumeUrl) {
            formData.append('resume_url', resumeUrl);
        }
        
        // Send request to save-resume endpoint
        fetch('/api/save-resume', {
            method: 'POST',
            body: formData,
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            saveProgressBar.style.width = '75%';
            return response.json();
        })
        .then(data => {
            console.log('Response received:', data);
            saveProgressBar.style.width = '100%';
            
            if (data.success) {
                displaySaveResults(data.data);
                setStatus('Success', 'success');
            } else {
                alert('Error: ' + data.error);
                setStatus('Error', 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error: ' + error.message);
            setStatus('Error', 'danger');
        })
        .finally(() => {
            setTimeout(() => {
                saveProgress.classList.add('d-none');
                saveProgressBar.style.width = '0%';
            }, 500);
        });
    }
    
    // Display results for extract only
    function displayExtractResults(data) {
        const parsedData = data.parsedData;
        const textContent = data.textContent;
        
        // Show results section
        extractResultsSection.classList.remove('d-none');
        
        // Set basic information
        document.getElementById('extractName').textContent = parsedData.name || '';
        document.getElementById('extractEmail').textContent = parsedData.email || '';
        document.getElementById('extractPhone').textContent = parsedData.phone || '';
        document.getElementById('extractLinkedin').textContent = parsedData.linkedin || '';
        document.getElementById('extractLocation').textContent = parsedData.location || '';
        
        // Set skills
        const skillsElement = document.getElementById('extractSkills');
        skillsElement.innerHTML = '';
        if (parsedData.skills && parsedData.skills.length > 0) {
            parsedData.skills.forEach(skill => {
                const badge = document.createElement('span');
                badge.className = 'badge bg-secondary me-1 mb-1';
                badge.textContent = skill;
                skillsElement.appendChild(badge);
            });
        } else {
            skillsElement.textContent = 'No skills detected';
        }
        
        // Set education
        const educationElement = document.getElementById('extractEducation');
        educationElement.innerHTML = '';
        if (parsedData.education && parsedData.education.length > 0) {
            parsedData.education.forEach(edu => {
                const item = document.createElement('div');
                item.className = 'list-group-item';
                item.textContent = edu;
                educationElement.appendChild(item);
            });
        } else {
            const item = document.createElement('div');
            item.className = 'list-group-item text-muted';
            item.textContent = 'No education detected';
            educationElement.appendChild(item);
        }
        
        // Set experience
        const experienceElement = document.getElementById('extractExperience');
        experienceElement.innerHTML = '';
        if (parsedData.experience && parsedData.experience.length > 0) {
            parsedData.experience.forEach(exp => {
                const item = document.createElement('div');
                item.className = 'list-group-item';
                item.textContent = exp;
                experienceElement.appendChild(item);
            });
        } else {
            const item = document.createElement('div');
            item.className = 'list-group-item text-muted';
            item.textContent = 'No experience detected';
            experienceElement.appendChild(item);
        }
        
        // Set summary
        document.getElementById('extractSummary').textContent = parsedData.summary || 'No summary available';
        
        // Set raw text
        document.getElementById('extractRawText').textContent = textContent || 'No text content available';
    }
    
    // Display results for save resume
    function displaySaveResults(data) {
        // Show results section
        saveResultsSection.classList.remove('d-none');
        
        // Set basic information
        document.getElementById('saveResId').textContent = data.resume_id || '';
        document.getElementById('saveUserId').textContent = data.user_id || '';
        document.getElementById('saveFormat').textContent = data.format || '';
        document.getElementById('saveUrl').textContent = data.url || '';
        
        // Set content sample
        const content = data.content || {};
        document.getElementById('saveName').textContent = content.name || '';
        document.getElementById('saveEmail').textContent = content.email || '';
        
        // Set skills
        const saveSkills = document.getElementById('saveSkills');
        if (content.skills && content.skills.length > 0) {
            saveSkills.textContent = content.skills.slice(0, 5).join(', ');
            if (content.skills.length > 5) {
                saveSkills.textContent += '... (' + (content.skills.length - 5) + ' more)';
            }
        } else {
            saveSkills.textContent = 'None detected';
        }
        
        // Set full content
        document.getElementById('fullContent').textContent = JSON.stringify(content, null, 2);
    }
    
    // Update status function
    function setStatus(message, type) {
        const statusElement = document.getElementById('status');
        statusElement.textContent = message;
        statusElement.className = `badge bg-${type}`;
    }
}); 