# Image Compressor with Motivational Quotes

This is a simple web application that combines an image compression tool with a motivational quote display. Users can upload an image, adjust its compression quality, and download the optimized version, all while being inspired by random quotes.

## Features

*   **Image Compression:**
    *   Upload an image file (JPEG, PNG, etc.).
    *   Displays the original image and its file size.
    *   Provides a live preview of the compressed image and its new file size.
    *   Adjust compression quality using a slider (JPEG compression).
    *   Download the compressed image.
*   **Motivational Quotes:**
    *   Displays a random motivational quote on page load.
    *   Includes the author of the quote.
    *   A "Get New Quote" button to fetch another random quote.

## How to Run

1.  **Save the files:**
    *   Save the HTML code into a file named `index.html`.
    *   Save the CSS code into a file named `style.css` in the same directory as `index.html`.
    *   Save the JavaScript code into a file named `script.js` in the same directory as `index.html`.
2.  **Open in browser:**
    *   Open `index.html` in your web browser.

## Technologies Used

*   **HTML5:** For structuring the web page content.
*   **CSS3:** For styling the application and making it responsive.
*   **JavaScript (ES6+):** For handling image processing (using Canvas API), fetching quotes from an external API, and managing user interactions.
*   **Quotable API (`https://api.quotable.io/random`):** Used to fetch random motivational quotes.