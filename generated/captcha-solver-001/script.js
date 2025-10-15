let correctCaptchaText = '';

function generateCaptcha() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let captcha = '';
    for (let i = 0; i < 6; i++) { // Generate a 6-character captcha
        captcha += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    correctCaptchaText = captcha;

    const canvas = document.getElementById('captchaCanvas');
    const ctx = canvas.getContext('2d');

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Background
    ctx.fillStyle = '#f0f0f0';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Add some random lines/noise
    ctx.strokeStyle = '#ccc';
    ctx.lineWidth = 1;
    for (let i = 0; i < 5; i++) {
        ctx.beginPath();
        ctx.moveTo(Math.random() * canvas.width, Math.random() * canvas.height);
        ctx.lineTo(Math.random() * canvas.width, Math.random() * canvas.height);
        ctx.stroke();
    }

    // Draw text
    ctx.font = '30px Arial';
    ctx.fillStyle = '#333';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    // Draw each character with slight rotation and offset
    for (let i = 0; i < captcha.length; i++) {
        ctx.save();
        const x = (canvas.width / captcha.length) * i + (canvas.width / captcha.length) / 2;
        const y = canvas.height / 2 + (Math.random() - 0.5) * 10; // Vertical offset

        ctx.translate(x, y);
        ctx.rotate((Math.random() - 0.5) * 0.3); // Rotate between -0.15 and 0.15 radians
        ctx.fillText(captcha[i], 0, 0);
        ctx.restore();
    }

    const captchaImage = document.getElementById('captchaImage');
    captchaImage.src = canvas.toDataURL(); // Convert canvas to image data URL
    document.getElementById('captchaInput').value = ''; // Clear input field
    document.getElementById('feedback').textContent = ''; // Clear feedback message
}

function checkCaptcha() {
    const userInput = document.getElementById('captchaInput').value;
    const feedback = document.getElementById('feedback');

    if (userInput.toLowerCase() === correctCaptchaText.toLowerCase()) {
        feedback.textContent = 'Correct! You are human.';
        feedback.style.color = 'green';
        // Optionally generate a new captcha after a short delay on success
        setTimeout(generateCaptcha, 1500);
    } else {
        feedback.textContent = 'Incorrect. Please try again.';
        feedback.style.color = 'red';
        generateCaptcha(); // Generate a new captcha on incorrect attempt
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    generateCaptcha(); // Generate captcha on page load
    document.getElementById('submitCaptcha').addEventListener('click', checkCaptcha);
    document.getElementById('newCaptcha').addEventListener('click', generateCaptcha);
});