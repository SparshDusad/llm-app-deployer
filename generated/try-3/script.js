document.addEventListener('DOMContentLoaded', () => {
    // --- Image Compressor Logic ---
    const imageInput = document.getElementById('imageInput');
    const originalImage = document.getElementById('originalImage');
    const originalSize = document.getElementById('originalSize');
    const compressedCanvas = document.getElementById('compressedCanvas');
    const compressedSize = document.getElementById('compressedSize');
    const downloadBtn = document.getElementById('downloadBtn');
    const qualityRange = document.getElementById('qualityRange');
    const qualityValue = document.getElementById('qualityValue');

    let originalFile = null;
    let currentImageSrc = null; // Stores the data URL of the original image

    // Displays the original image and its size
    function displayOriginalImage(file) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                currentImageSrc = e.target.result;
                originalImage.src = currentImageSrc;
                originalImage.style.display = 'block';
                originalImage.onload = () => {
                    originalSize.textContent = `Size: ${(file.size / 1024).toFixed(2)} KB`;
                    resolve();
                };
            };
            reader.readAsDataURL(file);
        });
    }

    // Compresses the image using canvas and displays the result
    function compressImage() {
        if (!currentImageSrc) return;

        const img = new Image();
        img.onload = () => {
            const ctx = compressedCanvas.getContext('2d');
            const quality = qualityRange.value / 100;

            // Set canvas dimensions to match image
            compressedCanvas.width = img.width;
            compressedCanvas.height = img.height;

            // Draw image on canvas
            ctx.clearRect(0, 0, compressedCanvas.width, compressedCanvas.height);
            ctx.drawImage(img, 0, 0, img.width, img.height);

            // Get compressed data URL
            // Using 'image/jpeg' for compression, even if original is PNG, for consistency
            const compressedDataUrl = compressedCanvas.toDataURL('image/jpeg', quality);

            // Display compressed image and size
            compressedCanvas.style.display = 'block';
            const compressedBlob = dataURLtoBlob(compressedDataUrl);
            compressedSize.textContent = `Size: ${(compressedBlob.size / 1024).toFixed(2)} KB`;
            downloadBtn.style.display = 'block';
        };
        img.src = currentImageSrc; // Use the already loaded original image src
    }

    // Helper function to convert data URL to Blob
    function dataURLtoBlob(dataurl) {
        const arr = dataurl.split(',');
        const mime = arr[0].match(/:(.*?);/)[1];
        const bstr = atob(arr[1]);
        let n = bstr.length;
        const u8arr = new Uint8Array(n);
        while (n--) {
            u8arr[n] = bstr.charCodeAt(n);
        }
        return new Blob([u8arr], { type: mime });
    }

    // Event listener for image input change
    imageInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (file) {
            originalFile = file; // Keep reference to original file for size
            await displayOriginalImage(file);
            compressImage(); // Compress automatically after loading
        } else {
            // Reset display if no file is selected
            originalImage.style.display = 'none';
            compressedCanvas.style.display = 'none';
            originalSize.textContent = '';
            compressedSize.textContent = '';
            downloadBtn.style.display = 'none';
            currentImageSrc = null;
            originalFile = null;
        }
    });

    // Event listener for quality range input
    qualityRange.addEventListener('input', () => {
        qualityValue.textContent = qualityRange.value;
        if (currentImageSrc) {
            compressImage(); // Re-compress when quality changes
        }
    });

    // Event listener for download button
    downloadBtn.addEventListener('click', () => {
        if (compressedCanvas.style.display === 'block') {
            const dataURL = compressedCanvas.toDataURL('image/jpeg', qualityRange.value / 100);
            const a = document.createElement('a');
            a.href = dataURL;
            a.download = `compressed_image_${Date.now()}.jpeg`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }
    });

    // --- Motivational Quote Logic ---
    const quoteText = document.getElementById('quoteText');
    const quoteAuthor = document.getElementById('quoteAuthor');
    const newQuoteBtn = document.getElementById('newQuoteBtn');

    async function fetchQuote() {
        quoteText.textContent = 'Loading quote...';
        quoteAuthor.textContent = '';
        try {
            const response = await fetch('https://api.quotable.io/random');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            quoteText.textContent = `"${data.content}"`;
            quoteAuthor.textContent = `- ${data.author}`;
        } catch (error) {
            quoteText.textContent = 'Failed to fetch quote.';
            quoteAuthor.textContent = '';
            console.error('Error fetching quote:', error);
        }
    }

    // Event listener for new quote button
    newQuoteBtn.addEventListener('click', fetchQuote);

    // Fetch a quote on page load
    fetchQuote();
});