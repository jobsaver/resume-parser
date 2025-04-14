// Resume Parser Demo Frontend JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('fileUpload');
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadProgress = document.getElementById('uploadProgress');
    const progressBar = uploadProgress.querySelector('.progress-bar');
    const resultsSection = document.getElementById('resultsSection');
    const showRawTextBtn = document.getElementById('showRawText');
    const rawTextSection = document.getElementById('rawTextSection');
    const rawText = document.getElementById('rawText');
    const statusIndicator = document.getElementById('status');
    const loadHistoryBtn = document.getElementById('loadHistoryBtn');
    const historyList = document.getElementById('historyList');
    
    // Auth elements
    const userIdInput = document.getElementById('userId');
    const tokenInput = document.getElementById('token');
    
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
    
    // Add event listeners for drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    // Highlight drop area when dragging over it
    dropArea.addEventListener('dragenter', highlight);
    dropArea.addEventListener('dragover', highlight);
    
    // Remove highlight when leaving or after drop
    dropArea.addEventListener('dragleave', unhighlight);
    dropArea.addEventListener('drop', unhighlight);
    
    function highlight() {
        dropArea.classList.add('highlight');
    }
    
    function unhighlight() {
        dropArea.classList.remove('highlight');
    }
    
    // Handle file drop
    dropArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            // Display selected file name
            dropArea.querySelector('p').textContent = `Selected: ${files[0].name}`;
        }
    }
    
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
    
    // Handle upload button click
    uploadBtn.addEventListener('click', function() {
        console.log('Upload button clicked');
        uploadFile();
    });
    
    // Handle raw text toggle
    showRawTextBtn.addEventListener('click', () => {
        rawTextSection.classList.toggle('d-none');
    });
    
    // Handle load history button
    loadHistoryBtn.addEventListener('click', loadResumeHistory);
    
    // Setup direct form submission
    const directUploadForm = document.getElementById('directUploadForm');
    const formUserId = document.getElementById('formUserId');
    const formToken = document.getElementById('formToken');
    const formFileUpload = document.getElementById('formFileUpload');
    
    // Update form values when user ID or token changes
    userIdInput.addEventListener('change', updateFormValues);
    tokenInput.addEventListener('change', updateFormValues);
    
    function updateFormValues() {
        if (formUserId && formToken) {
            formUserId.value = userIdInput.value.trim();
            formToken.value = tokenInput.value.trim();
            console.log('Form values updated:', { userId: formUserId.value, token: '***' });
        }
    }
    
    // Initialize form values
    updateFormValues();
    
    // Copy selected file to form input
    fileInput.addEventListener('change', function() {
        if (fileInput.files.length > 0 && formFileUpload) {
            try {
                // Create a new DataTransfer object
                const dataTransfer = new DataTransfer();
                // Add the selected file
                dataTransfer.items.add(fileInput.files[0]);
                // Set the files to the form input
                formFileUpload.files = dataTransfer.files;
                console.log('File copied to form input:', formFileUpload.files[0].name);
            } catch (e) {
                console.error('Error copying file to form input:', e);
            }
        }
    });
    
    // Prepare form submission
    directUploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Force update form values before submission
        if (formUserId && formToken && userIdInput && tokenInput) {
            formUserId.value = userIdInput.value.trim();
            formToken.value = tokenInput.value.trim();
        }
        
        // Check if file is selected
        if (!formFileUpload || formFileUpload.files.length === 0) {
            alert('Please select a PDF file first.');
            return false;
        }
        
        console.log('Form submission starting with:');
        console.log('- User ID:', formUserId.value);
        console.log('- File:', formFileUpload.files[0].name);
        
        // Show progress
        setStatus('Uploading...', 'warning');
        uploadProgress.classList.remove('d-none');
        
        // Create form data programmatically
        const formData = new FormData();
        formData.append('user_id', formUserId.value);
        formData.append('token', formToken.value);
        formData.append('resume', formFileUpload.files[0]);
        
        // Submit with fetch API
        fetch('/api/parse', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log('Response received:', data);
            if (data.success) {
                displayResults(data.data);
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
            uploadProgress.classList.add('d-none');
        });
        
        return false;
    });
    
    // Upload file function
    function uploadFile() {
        console.log('Upload button clicked');
        const file = fileInput.files[0];
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
        
        // Update status
        setStatus('Uploading...', 'warning');
        console.log('Status updated to Uploading');
        
        // Show progress
        uploadProgress.classList.remove('d-none');
        progressBar.style.width = '0%';
        
        // Hide results if previously shown
        resultsSection.classList.add('d-none');
        
        // Create FormData
        const formData = new FormData();
        formData.append('resume', file);
        
        // Create XMLHttpRequest
        const xhr = new XMLHttpRequest();
        
        // Setup progress tracking
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                progressBar.style.width = percentComplete + '%';
                console.log('Upload progress:', percentComplete + '%');
                
                if (percentComplete === 100) {
                    setStatus('Processing...', 'info');
                    console.log('Status updated to Processing');
                }
            }
        });
        
        // Setup completion handling
        xhr.addEventListener('load', () => {
            console.log('Response received:', xhr.status);
            console.log('Response text:', xhr.responseText);
            
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    console.log('Parsed response:', response);
                    
                    if (response.success) {
                        displayResults(response.data);
                        setStatus('Success', 'success');
                        console.log('Results displayed successfully');
                    } else {
                        alert('Error: ' + response.error);
                        setStatus('Error', 'danger');
                        console.error('API error:', response.error);
                    }
                } catch (e) {
                    console.error('Error parsing JSON response:', e);
                    alert('Error parsing server response');
                    setStatus('Error', 'danger');
                }
            } else {
                try {
                    const response = JSON.parse(xhr.responseText);
                    alert('Error: ' + (response.error || 'Unknown error'));
                    console.error('HTTP error with response:', response);
                } catch (e) {
                    alert('Error: Server returned status ' + xhr.status);
                    console.error('HTTP error:', xhr.status);
                }
                setStatus('Error', 'danger');
            }
            
            // Hide progress
            uploadProgress.classList.add('d-none');
            console.log('Progress bar hidden');
        });
        
        // Setup error handling
        xhr.addEventListener('error', (e) => {
            console.error('Network error:', e);
            alert('Network error occurred');
            setStatus('Error', 'danger');
            uploadProgress.classList.add('d-none');
        });
        
        // Setup timeout handling
        xhr.addEventListener('timeout', () => {
            console.error('Request timed out');
            alert('Request timed out');
            setStatus('Error', 'danger');
            uploadProgress.classList.add('d-none');
        });
        
        // Log the request URL
        const requestUrl = `/api/parse?user_id=${encodeURIComponent(userId)}&token=${encodeURIComponent(token)}`;
        console.log('Sending request to:', requestUrl);
        
        // Open and send request
        try {
            xhr.open('POST', requestUrl);
            xhr.send(formData);
            console.log('Request sent');
        } catch (e) {
            console.error('Error sending request:', e);
            alert('Error sending request: ' + e.message);
            setStatus('Error', 'danger');
            uploadProgress.classList.add('d-none');
        }
    }
    
    // Function to load resume history
    function loadResumeHistory() {
        const userId = userIdInput.value.trim();
        const token = tokenInput.value.trim();
        
        if (!userId || !token) {
            alert('Please provide both User ID and Token for authentication.');
            return;
        }
        
        // Clear existing items
        historyList.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        // Make request to get resume history
        fetch(`/api/user/resumes?user_id=${encodeURIComponent(userId)}&token=${encodeURIComponent(token)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load resume history');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    displayResumeHistory(data.data.resumes);
                } else {
                    throw new Error(data.error || 'Unknown error');
                }
            })
            .catch(error => {
                historyList.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
            });
    }
    
    // Function to display resume history
    function displayResumeHistory(resumes) {
        if (resumes.length === 0) {
            historyList.innerHTML = '<div class="alert alert-info">No resumes found</div>';
            return;
        }
        
        historyList.innerHTML = '';
        
        resumes.forEach(resume => {
            const date = new Date(resume.created_at);
            const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
            
            const item = document.createElement('a');
            item.className = 'list-group-item list-group-item-action history-item';
            item.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h5 class="mb-1">${resume.file_name}</h5>
                    <small class="history-item-date">${formattedDate}</small>
                </div>
                <p class="mb-1">Name: ${resume.parsed_data.name || 'Not found'}</p>
                <small>ID: ${resume._id}</small>
            `;
            
            // Add click event to view resume details
            item.addEventListener('click', () => {
                viewResumeDetails(resume._id);
            });
            
            historyList.appendChild(item);
        });
    }
    
    // Function to view resume details
    function viewResumeDetails(resumeId) {
        const userId = userIdInput.value.trim();
        const token = tokenInput.value.trim();
        
        const modal = new bootstrap.Modal(document.getElementById('resumeDetailModal'));
        const modalContent = document.getElementById('resumeDetailContent');
        
        modalContent.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        modal.show();
        
        // Make request to get resume details
        fetch(`/api/resume/${resumeId}?user_id=${encodeURIComponent(userId)}&token=${encodeURIComponent(token)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load resume details');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    modalContent.innerHTML = generateResumeDetailsHTML(data.data);
                } else {
                    throw new Error(data.error || 'Unknown error');
                }
            })
            .catch(error => {
                modalContent.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
            });
    }
    
    // Function to generate HTML for resume details
    function generateResumeDetailsHTML(resume) {
        const parsedData = resume.parsed_data;
        const date = new Date(resume.created_at);
        const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        
        let skillsHtml = '';
        if (parsedData.skills && parsedData.skills.length > 0) {
            skillsHtml = parsedData.skills.map(skill => `<span class="skill-tag">${skill}</span>`).join(' ');
        } else {
            skillsHtml = '<em>No skills found</em>';
        }
        
        let educationHtml = '';
        if (parsedData.education && parsedData.education.length > 0) {
            educationHtml = parsedData.education.map(edu => `<li class="list-group-item">${edu}</li>`).join('');
            educationHtml = `<ul class="list-group">${educationHtml}</ul>`;
        } else {
            educationHtml = '<em>No education history found</em>';
        }
        
        let experienceHtml = '';
        if (parsedData.experience && parsedData.experience.length > 0) {
            experienceHtml = parsedData.experience.map(exp => `<li class="list-group-item">${exp}</li>`).join('');
            experienceHtml = `<ul class="list-group">${experienceHtml}</ul>`;
        } else {
            experienceHtml = '<em>No work experience found</em>';
        }
        
        return `
            <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">${resume.file_name}</h5>
                    <h6 class="card-subtitle mb-2 text-muted">Uploaded: ${formattedDate}</h6>
                    
                    <div class="row mt-3">
                        <div class="col-md-6">
                            <h6>Basic Information</h6>
                            <table class="table table-bordered">
                                <tr>
                                    <td><strong>Name</strong></td>
                                    <td>${parsedData.name || 'Not found'}</td>
                                </tr>
                                <tr>
                                    <td><strong>Email</strong></td>
                                    <td>${parsedData.email || 'Not found'}</td>
                                </tr>
                                <tr>
                                    <td><strong>Phone</strong></td>
                                    <td>${parsedData.phone || 'Not found'}</td>
                                </tr>
                            </table>
                            
                            <h6>Skills</h6>
                            <div class="skills-list mb-3">
                                ${skillsHtml}
                            </div>
                        </div>
                        <div class="col-md-6">
                            <h6>Education</h6>
                            ${educationHtml}
                            
                            <h6 class="mt-3">Experience</h6>
                            ${experienceHtml}
                        </div>
                    </div>
                    
                    <div class="mt-3">
                        <h6>Summary</h6>
                        <div class="p-3 bg-light rounded">
                            ${parsedData.summary || 'No summary available'}
                        </div>
                    </div>
                    
                    <div class="accordion mt-3" id="resumeTextAccordion">
                        <div class="accordion-item">
                            <h2 class="accordion-header" id="headingOne">
                                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseOne" aria-expanded="false" aria-controls="collapseOne">
                                    View Raw Text Content
                                </button>
                            </h2>
                            <div id="collapseOne" class="accordion-collapse collapse" aria-labelledby="headingOne" data-bs-parent="#resumeTextAccordion">
                                <div class="accordion-body">
                                    <pre class="bg-light p-3 rounded text-wrap" style="max-height: 300px; overflow-y: auto;">${resume.text_content}</pre>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Function to display results
    function displayResults(data) {
        // Show results section
        resultsSection.classList.remove('d-none');
        
        // Get the parsed data
        const parsedData = data.parsedData;
        
        // Basic information
        document.getElementById('name').textContent = parsedData.name || 'Not found';
        document.getElementById('email').textContent = parsedData.email || 'Not found';
        document.getElementById('phone').textContent = parsedData.phone || 'Not found';
        
        // Skills
        const skillsContainer = document.getElementById('skills');
        skillsContainer.innerHTML = '';
        
        if (parsedData.skills && parsedData.skills.length > 0) {
            parsedData.skills.forEach(skill => {
                const skillTag = document.createElement('span');
                skillTag.className = 'skill-tag';
                skillTag.textContent = skill;
                skillsContainer.appendChild(skillTag);
            });
        } else {
            skillsContainer.innerHTML = '<em>No skills found</em>';
        }
        
        // Education
        const educationContainer = document.getElementById('education');
        educationContainer.innerHTML = '';
        
        if (parsedData.education && parsedData.education.length > 0) {
            parsedData.education.forEach(edu => {
                const item = document.createElement('div');
                item.className = 'list-group-item';
                item.textContent = edu;
                educationContainer.appendChild(item);
            });
        } else {
            educationContainer.innerHTML = '<em>No education history found</em>';
        }
        
        // Experience
        const experienceContainer = document.getElementById('experience');
        experienceContainer.innerHTML = '';
        
        if (parsedData.experience && parsedData.experience.length > 0) {
            parsedData.experience.forEach(exp => {
                const item = document.createElement('div');
                item.className = 'list-group-item';
                item.textContent = exp;
                experienceContainer.appendChild(item);
            });
        } else {
            experienceContainer.innerHTML = '<em>No work experience found</em>';
        }
        
        // Summary
        const summaryContainer = document.getElementById('summary');
        summaryContainer.textContent = parsedData.summary || 'No summary available';
        
        // Raw text
        rawText.textContent = data.textContent || '';
    }
    
    // Function to update status indicator
    function setStatus(message, type) {
        statusIndicator.textContent = message;
        statusIndicator.className = `badge bg-${type}`;
    }

    // Simple upload button
    const simpleUploadBtn = document.getElementById('simpleUploadBtn');
    if (simpleUploadBtn) {
        simpleUploadBtn.addEventListener('click', function() {
            console.log('Simple upload button clicked');
            
            const file = fileInput.files[0];
            if (!file) {
                alert('Please select a PDF file first.');
                return;
            }
            
            const userId = userIdInput.value.trim();
            const token = tokenInput.value.trim();
            
            if (!userId || !token) {
                alert('Please provide both User ID and Token for authentication.');
                return;
            }
            
            // Show status
            setStatus('Uploading...', 'warning');
            
            // Create FormData
            const formData = new FormData();
            formData.append('resume', file);
            formData.append('user_id', userId);
            formData.append('token', token);
            
            console.log('Simple upload with:', {
                userId: userId,
                tokenLength: token.length,
                file: file.name
            });
            
            // Use fetch API to upload
            fetch('/api/parse', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                console.log('Response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Response data:', data);
                if (data.success) {
                    displayResults(data.data);
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
            });
        });
    }
}); 