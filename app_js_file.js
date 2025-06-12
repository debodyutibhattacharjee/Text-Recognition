// JPG File Uploader with Translation - JavaScript
// app.js

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const filePreview = document.getElementById('filePreview');
const successMessage = document.getElementById('successMessage');
const errorMessage = document.getElementById('errorMessage');

// Global variables
let uploadedFiles = [];

// Initialize event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
});

function initializeEventListeners() {
    // Click to upload
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    // Drag and drop functionality
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files);
        handleFiles(files);
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        handleFiles(files);
    });
}

function handleFiles(files) {
    hideMessages();
    
    const jpgFiles = files.filter(file => {
        const fileType = file.type.toLowerCase();
        const fileName = file.name.toLowerCase();
        return fileType === 'image/jpeg' || fileType === 'image/jpg' || 
               fileName.endsWith('.jpg') || fileName.endsWith('.jpeg');
    });

    if (jpgFiles.length === 0) {
        showError('Please select only JPG files.');
        return;
    }

    if (jpgFiles.length !== files.length) {
        showError('Some files were not JPG format and were skipped.');
    }

    jpgFiles.forEach(file => {
        uploadedFiles.push(file);
        displayFile(file);
    });

    if (jpgFiles.length > 0) {
        showSuccess(`${jpgFiles.length} file(s) uploaded successfully!`);
    }
}

function displayFile(file) {
    const fileDiv = document.createElement('div');
    fileDiv.className = 'file-info';
    fileDiv.style.marginBottom = '20px';
    
    const reader = new FileReader();
    reader.onload = function(e) {
        fileDiv.innerHTML = `
            <div class="file-icon">🖼️</div>
            <div class="file-details">
                <div class="file-name">${file.name}</div>
                <div class="file-size">${formatFileSize(file.size)}</div>
            </div>
        `;
        
        const img = document.createElement('img');
        img.src = e.target.result;
        img.className = 'preview-image';
        img.alt = file.name;
        
        fileDiv.appendChild(img);
    };
    reader.readAsDataURL(file);
    
    filePreview.appendChild(fileDiv);
    filePreview.style.display = 'block';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function clearFiles() {
    uploadedFiles = [];
    filePreview.innerHTML = '';
    filePreview.style.display = 'none';
    document.getElementById('textResult').style.display = 'none';
    document.getElementById('translationResult').style.display = 'none';
    document.getElementById('processingStatus').style.display = 'none';
    fileInput.value = '';
    hideMessages();
}

function showSuccess(message) {
    successMessage.textContent = '✅ ' + message;
    successMessage.style.display = 'block';
    errorMessage.style.display = 'none';
}

function showError(message) {
    errorMessage.textContent = '❌ ' + message;
    errorMessage.style.display = 'block';
    successMessage.style.display = 'none';
}

function hideMessages() {
    successMessage.style.display = 'none';
    errorMessage.style.display = 'none';
}

function showProcessing() {
    document.getElementById('processingStatus').style.display = 'block';
    document.getElementById('sendToPythonBtn').disabled = true;
}

function hideProcessing() {
    document.getElementById('processingStatus').style.display = 'none';
    document.getElementById('sendToPythonBtn').disabled = false;
}

// Example functions to access uploaded files
function processFiles() {
    if (uploadedFiles.length === 0) {
        showError('No files uploaded yet!');
        return;
    }

    console.log('Total files:', uploadedFiles.length);
    
    // Loop through all uploaded files
    uploadedFiles.forEach((file, index) => {
        console.log(`File ${index + 1}:`, {
            name: file.name,
            size: file.size,
            type: file.type,
            lastModified: new Date(file.lastModified)
        });
        
        // You can access the actual file data like this:
        const reader = new FileReader();
        reader.onload = function(e) {
            // e.target.result contains the file data as base64
            console.log(`File ${index + 1} data:`, e.target.result.substring(0, 100) + '...');
            
            // Here you could:
            // - Send to server via fetch/XMLHttpRequest
            // - Process the image data
            // - Convert to different formats
            // - Apply filters or modifications
        };
        reader.readAsDataURL(file); // or readAsArrayBuffer(), readAsText(), etc.
    });
    
    showSuccess(`Processed ${uploadedFiles.length} files! Check console for details.`);
}

function downloadFile() {
    if (uploadedFiles.length === 0) {
        showError('No files to download!');
        return;
    }

    // Download the first uploaded file
    const file = uploadedFiles[0];
    const url = URL.createObjectURL(file);
    const a = document.createElement('a');
    a.href = url;
    a.download = file.name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showSuccess(`Downloaded: ${file.name}`);
}

// Enhanced: Send files to Python Flask server with translation support
async function sendToPython() {
    if (uploadedFiles.length === 0) {
        showError('No files to send!');
        return;
    }

    try {
        showProcessing();
        hideMessages();
        document.getElementById('textResult').style.display = 'none';
        document.getElementById('translationResult').style.display = 'none';
        
        let allExtractedTexts = [];
        
        for (let i = 0; i < uploadedFiles.length; i++) {
            const file = uploadedFiles[i];
            const formData = new FormData();
            formData.append('file', file);
            formData.append('filename', file.name);

            console.log(`📤 Sending file ${i + 1}/${uploadedFiles.length}: ${file.name}`);

            const response = await fetch('https://text-recognition-2.onrender.com/upload', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log(`✅ File ${i + 1} processed successfully:`, result);
                
                // Check if we have extracted_text in the response
                if (result.extracted_text) {
                    console.log('📝 Found extracted text for', file.name);
                    allExtractedTexts.push({
                        filename: file.name,
                        textData: result.extracted_text
                    });
                } else {
                    console.warn('⚠️ No extracted_text in response for', file.name);
                }
            } else {
                const errorText = await response.text();
                console.error(`❌ Server error for ${file.name}:`, response.status, errorText);
                throw new Error(`Failed to process ${file.name}: ${response.status} - ${errorText}`);
            }
        }
        
        hideProcessing();
        
        if (allExtractedTexts.length > 0) {
            // Display the first extracted text result
            displayExtractedText(allExtractedTexts[0].textData, allExtractedTexts[0].filename);
            showSuccess(`Successfully processed ${uploadedFiles.length} files! Text and translation from first file are displayed below.`);
        } else {
            showError('No text could be extracted from the uploaded files.');
        }
        
    } catch (error) {
        console.error('❌ Error processing files:', error);
        hideProcessing();
        showError('Failed to process files. Error: ' + error.message);
    }
}

// Enhanced: Display extracted text and translation
function displayExtractedText(textData, filename) {
    console.log('🔍 Displaying text data for', filename, ':', textData);
    
    const textResult = document.getElementById('textResult');
    const extractedText = document.getElementById('extractedText');
    const textMethod = document.getElementById('textMethod');
    const confidenceFill = document.getElementById('confidenceFill');
    const confidenceText = document.getElementById('confidenceText');
    const debugInfo = document.getElementById('debugInfo');
    
    // Translation elements
    const translationResult = document.getElementById('translationResult');
    const bengaliText = document.getElementById('bengaliText');
    const translationStatus = document.getElementById('translationStatus');
    const translationStatusIcon = document.getElementById('translationStatusIcon');
    const detectedLanguage = document.getElementById('detectedLanguage');
    const translationService = document.getElementById('translationService');
    
    // Initialize default values
    let displayText = 'No text found';
    let method = 'Unknown';
    let confidence = 0;
    let translationData = null;
    
    try {
        // Check if textData is valid
        if (!textData) {
            console.warn('⚠️ No text data provided');
            displayText = 'Error: No text data received from server';
        } else if (typeof textData === 'string') {
            // Simple string response
            console.log('📝 Processing string response');
            displayText = textData;
            method = 'Direct';
            confidence = textData.length > 0 ? Math.min(textData.length * 2, 100) : 0;
        } else if (typeof textData === 'object') {
            // Object response from Python server
            console.log('📝 Processing object response:', Object.keys(textData));
            
            // Extract text from various possible fields
            displayText = textData.best_text || textData.text || textData.extracted_text || 'No text found in image';
            method = textData.method_used || 'Unknown';
            confidence = textData.confidence || 0;
            
            // Extract translation data if available
            if (textData.translation) {
                translationData = textData.translation;
                console.log('🌐 Found translation data:', translationData);
            }
            
            // Show debug info if available
            if (textData.all_results || textData.total_methods_tried) {
                const debugHTML = `
                    <strong>Debug Information for ${filename}:</strong><br>
                    Method used: ${method}<br>
                    Total methods tried: ${textData.total_methods_tried || 'Unknown'}<br>
                    Successful methods: ${textData.successful_methods || 'Unknown'}<br>
                    Confidence: ${confidence}%<br>
                    ${textData.all_results ? '<br><strong>All Results:</strong><br>' + 
                      Object.entries(textData.all_results).map(([k, v]) => `${k}: "${v}"`).join('<br>') : ''}
                `;
                debugInfo.innerHTML = debugHTML;
            }
        } else {
            console.warn('⚠️ Unexpected textData type:', typeof textData);
            displayText = 'Error: Unexpected data format';
        }
        
        // Display the OCR results
        extractedText.textContent = displayText;
        textMethod.textContent = `Method: ${method}`;
        
        // Update confidence bar
        const confidencePercent = Math.max(0, Math.min(100, confidence));
        confidenceFill.style.width = confidencePercent + '%';
        confidenceText.textContent = confidencePercent + '%';
        
        // Show the OCR result container
        textResult.style.display = 'block';
        
        // Display translation results if available
        if (translationData) {
            displayTranslationResult(translationData);
        } else {
            // Hide translation result if no translation data
            translationResult.style.display = 'none';
        }
        
        // Log results for debugging
        console.log('✅ Text extraction display completed:');
        console.log('  📄 File:', filename);
        console.log('  📝 Text length:', displayText.length);
        console.log('  🔧 Method:', method);
        console.log('  📊 Confidence:', confidencePercent + '%');
        console.log('  🌐 Translation available:', !!translationData);
        
        // Scroll to results
        textResult.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
    } catch (error) {
        console.error('❌ Error displaying extracted text:', error);
        extractedText.textContent = 'Error displaying extracted text: ' + error.message;
        textMethod.textContent = 'Method: Error';
        confidenceFill.style.width = '0%';
        confidenceText.textContent = '0%';
        textResult.style.display = 'block';
        translationResult.style.display = 'none';
    }
}

// New function to display translation results
function displayTranslationResult(translationData) {
    console.log('🌐 Displaying translation data:', translationData);

    const translationResult = document.getElementById('translationResult');
    const bengaliText = document.getElementById('bengaliText');
    const translationStatus = document.getElementById('translationStatus');
    const translationStatusIcon = document.getElementById('translationStatusIcon');
    const detectedLanguage = document.getElementById('detectedLanguage');
    const translationService = document.getElementById('translationService');

    try {
        if (!translationData) {
            console.warn('⚠️ No translation data provided');
            translationResult.textContent = 'No translation data available.';
            return;
        }

        // Extract translation information
        const bengaliTranslation = translationData.bengali_text || translationData.translated_text || 'Translation not available';
        const isSuccess = translationData.translation_success || false;
        const detectedLang = translationData.detected_language || 'Auto';
        const service = translationData.translator_service || 'Google Translate';

        // Update UI Elements
        bengaliText.textContent = bengaliTranslation;
        detectedLanguage.textContent = `Detected Language: ${detectedLang}`;
        translationService.textContent = `Translation Service: ${service}`;

        if (isSuccess) {
            translationStatus.textContent = 'Translation Successful';
            translationStatus.style.color = 'green';
            translationStatusIcon.innerHTML = '✅';
        } else {
            translationStatus.textContent = 'Translation Failed';
            translationStatus.style.color = 'red';
            translationStatusIcon.innerHTML = '❌';
        }

        // Show the translation result container
        if (translationResult) {
            translationResult.style.display = 'block';
        }

    } catch (error) {
        console.error('❌ Error displaying translation:', error);
        translationStatus.textContent = 'Error displaying translation';
        translationStatus.style.color = 'red';
        translationStatusIcon.innerHTML = '⚠️';
    }
}
