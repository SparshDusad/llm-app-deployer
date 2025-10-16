document.addEventListener('DOMContentLoaded', () => {
    const body = document.getElementById('app-body');

    body.addEventListener('click', () => {
        body.classList.toggle('dark-theme');
    });
});