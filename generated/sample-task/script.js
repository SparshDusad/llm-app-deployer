document.addEventListener('DOMContentLoaded', () => {
    const quoteText = document.getElementById('quoteText');
    const quoteAuthor = document.getElementById('quoteAuthor');
    const newQuoteBtn = document.getElementById('newQuoteBtn');

    const API_URL = 'https://api.quotable.io/random';

    /**
     * Fetches a random quote from the API and updates the UI.
     */
    async function fetchRandomQuote() {
        // Disable button during fetch to prevent multiple requests
        newQuoteBtn.disabled = true;
        newQuoteBtn.textContent = 'Loading...';
        quoteText.textContent = 'Fetching a new quote...';
        quoteAuthor.textContent = '-';

        try {
            const response = await fetch(API_URL);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            quoteText.textContent = data.content;
            quoteAuthor.textContent = `- ${data.author}`;
        } catch (error) {
            console.error('Error fetching quote:', error);
            quoteText.textContent = 'Failed to load quote. Please try again!';
            quoteAuthor.textContent = '- Error';
        } finally {
            // Re-enable button
            newQuoteBtn.disabled = false;
            newQuoteBtn.textContent = 'New Quote';
        }
    }

    // Add event listener to the button to fetch a new quote on click
    newQuoteBtn.addEventListener('click', fetchRandomQuote);

    // Fetch an initial quote when the page loads
    fetchRandomQuote();
});