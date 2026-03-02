document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const statusCard = document.getElementById('status-card');
    const processBtn = document.getElementById('process-btn');
    const btnText = document.getElementById('btn-text');
    const loader = document.getElementById('loader');
    const errorMsg = document.getElementById('error-msg');
    const successMsg = document.getElementById('success-msg');

    // Stats elements
    const infoFilename = document.getElementById('info-filename');
    const infoType = document.getElementById('info-type');
    const infoCols = document.getElementById('info-cols');
    const infoRows = document.getElementById('info-rows');

    let currentFile = null;

    // Trigger file input
    dropZone.addEventListener('click', () => fileInput.click());

    // Drag and drop handlers
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    ['dragleave', 'drop'].forEach(evt => {
        dropZone.addEventListener(evt, () => dropZone.classList.remove('drag-over'));
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        const files = e.dataTransfer.files;
        if (files.length) handleFile(files[0]);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) handleFile(e.target.files[0]);
    });

    async function handleFile(file) {
        if (!file.name.endsWith('.csv')) {
            alert('Por favor, selecciona un archivo CSV válido.');
            return;
        }

        currentFile = file;
        errorMsg.style.display = 'none';
        successMsg.style.display = 'none';
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Error al validar el archivo');
            }

            const data = await response.json();
            
            // Update UI
            infoFilename.textContent = data.filename;
            infoType.textContent = data.type;
            infoCols.textContent = data.columns;
            infoRows.textContent = data.rows;
            
            statusCard.style.display = 'block';
            statusCard.scrollIntoView({ behavior: 'smooth' });
            
            // Set button text based on type
            btnText.textContent = data.type === 'Comprobantes de compras' 
                ? 'Procesar Comprobantes de Compras' 
                : 'Procesar Importación de Servicios';

        } catch (error) {
            alert(error.message);
        }
    }

    processBtn.addEventListener('click', async () => {
        if (!currentFile) return;

        processBtn.disabled = true;
        btnText.style.display = 'none';
        loader.style.display = 'block';
        errorMsg.style.display = 'none';

        const formData = new FormData();
        formData.append('file', currentFile);

        try {
            const response = await fetch('/process', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Error en el procesamiento');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'LIBRO_IVA_DIGITAL_SALIDA.zip';
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);

            successMsg.style.display = 'block';
        } catch (error) {
            errorMsg.textContent = error.message;
            errorMsg.style.display = 'block';
        } finally {
            processBtn.disabled = false;
            btnText.style.display = 'block';
            loader.style.display = 'none';
        }
    });
});
