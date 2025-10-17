const imageInput = document.getElementById('imageInput');
const qualitySlider = document.getElementById('qualitySlider');
const qualityValueSpan = document.getElementById('qualityValue');
const originalSizeSpan = document.getElementById('originalSize');
const compressedSizeSpan = document.getElementById('compressedSize');
const compressedImage = document.getElementById('compressedImage');
const downloadLink = document.getElementById('downloadLink');
const imageCanvas = document.getElementById('imageCanvas');
const ctx = imageCanvas.getContext('2d');

let currentImageObject = null; // Stores the loaded Image object

function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

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

function compressAndDisplayImage() {
    if (!currentImageObject) return;

    const quality = parseFloat(qualitySlider.value);
    qualityValueSpan.textContent = quality.toFixed(2);

    imageCanvas.width = currentImageObject.width;
    imageCanvas.height = currentImageObject.height;

    ctx.clearRect(0, 0, imageCanvas.width, imageCanvas.height);
    ctx.drawImage(currentImageObject, 0, 0, imageCanvas.width, imageCanvas.height);

    const compressedDataURL = imageCanvas.toDataURL('image/jpeg', quality);

    compressedImage.src = compressedDataURL;
    compressedImage.style.display = 'block';

    downloadLink.href = compressedDataURL;
    downloadLink.download = `compressed_${Date.now()}.jpeg`;
    downloadLink.style.display = 'block';

    const compressedBlob = dataURLtoBlob(compressedDataURL);
    compressedSizeSpan.textContent = formatBytes(compressedBlob.size);
}

imageInput.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
        alert('Please select an image file.');
        return;
    }

    originalSizeSpan.textContent = formatBytes(file.size);

    const reader = new FileReader();
    reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
            currentImageObject = img;
            compressAndDisplayImage();
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
});

qualitySlider.addEventListener('input', compressAndDisplayImage);

qualityValueSpan.textContent = qualitySlider.value;