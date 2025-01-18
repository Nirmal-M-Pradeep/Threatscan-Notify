document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('audioInput');
    const dropArea = document.getElementById('dropArea');
    const progressBar = document.getElementById('progressBar');
    const statusMessage = document.getElementById('statusMessage');
    const results = document.getElementById('results');

    const processedChunks = new Set();

   

    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, e => e.preventDefault());
    });

    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.add('highlight'));
    });

    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => dropArea.classList.remove('highlight'));
    });

    
    dropArea.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length) {
            if (files[0].type === 'audio/mp3' || files[0].type === 'audio/wav' || files[0].name.endsWith('.mp3') || files[0].name.endsWith('.wav') || files[0].name.endsWith('.mp4') || files[0].name.endsWith('.mkv') || files[0].name.endsWith('.mov')|| files[0].name.endsWith('.avi')) {
                fileInput.files = files;
                statusMessage.textContent = 'File ready for upload!';
            } else {
                statusMessage.textContent = 'Invalid file type. Please upload an MP3 file.';
            }
        }
    });

    
    dropArea.addEventListener('click', () => {
        fileInput.click();
    });

    
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            const file = fileInput.files[0];
            if (file.type === 'audio/mp3' || file.type === 'audio/wav' || file.name.endsWith('.mp3') || file.name.endsWith('.wav') || file.name.endsWith('.mp4') || file.name.endsWith('.mkv') || file.name.endsWith('.mov') || file.name.endsWith('.avi')) {
                statusMessage.textContent = 'File ready for upload!';
            } else {
                statusMessage.textContent = 'Invalid file type. Please upload an MP3 file.';
                fileInput.value = '';
            }
        }
    });

    async function hashChunk(chunk) {
        const encoder = new TextEncoder();
        const data = encoder.encode(chunk);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        return Array.from(new Uint8Array(hashBuffer))
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    }

    async function analyzeChunks(chunks) {
        

        for (const chunk of chunks) {
            const chunkHash = await hashChunk(chunk);

            if (processedChunks.has(chunkHash)) {
                console.log(`Skipping already processed chunk: ${chunkHash}`);
                continue;
            }

            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: JSON.stringify({ chunk }),
                    headers: { 'Content-Type': 'application/json' },
                });

                if (response.ok) {
                    const result = await response.json();
                    console.log(`Chunk result:`, result);

                    processedChunks.add(chunkHash);
                } else {
                    console.error(`Failed to process chunk: ${response.statusText}`);
                }
            } catch (error) {
                console.error(`Error processing chunk: ${error.message}`);
            }
        }
    }

    
    
    async function checkProgress() {
        try {
            const response = await fetch('/progress');
            if (!response.ok) {
                throw new Error("Failed to fetch progress");
            }
    
            const data = await response.json();
            statusMessage.textContent = data.message;
    
            if (data.message === "Transcribing audio...") {
                progressBar.style.width = "33%";
            } else if (data.message === "Analyzing text...") {
                progressBar.style.width = "66%";
            } else if (data.message === "Complete") {
                progressBar.style.width = "100%";
                return; 
            }
    
            
            setTimeout(checkProgress, 1000);
        } catch (error) {
            console.error("Error checking progress:", error);
            statusMessage.textContent = "Error checking progress. Please try again.";
        }
    }

    
    uploadForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        checkProgress();
    
        progressBar.style.width = '0%';
        results.innerHTML = '';
        statusMessage.textContent = 'Uploading file...';
    
        const file = fileInput.files[0];
        if (!file) {
            statusMessage.textContent = 'No file selected!';
            return;
        }
    
        const formData = new FormData();
        formData.append('file', file);
    
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData,
            });
    
            if (!response.ok) {
                const errorData = await response.json();
                statusMessage.textContent = `Error: ${errorData.error}`;
                return;
            }
    
            progressBar.style.width = '100%';
            const data = await response.json();
    
            
            console.log("Received transcriptionChunks:", data.transcriptionChunks);
    
            if (!data.transcriptionChunks || !Array.isArray(data.transcriptionChunks)) {
                throw new Error("Invalid transcriptionChunks received");
            }
    
            statusMessage.textContent = 'Analysis complete';
            results.innerHTML = `
                <h3>Results:</h3>
                <p><strong>Sentiment:</strong> ${JSON.stringify(data.sentiment)}</p>
                <p><strong>Detected Keywords:</strong> ${JSON.stringify(data.keywords)}</p>
                <p><strong>Email Status :</strong>${data.emailStatus}</p>
                <p><strong>Thank you</strong></p>
            `;
    
            const transcriptionChunks = data.transcriptionChunks;
            await analyzeChunks(transcriptionChunks); 
            statusMessage.textContent = 'Analysis complete.';
        } catch (error) {
            console.error(`Error during upload: ${error.message}`);
            statusMessage.textContent = `An error occurred: ${error.message}`;
        }
    });
    
});
