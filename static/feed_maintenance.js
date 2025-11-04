document.addEventListener('DOMContentLoaded', () => {
    // Get all checkboxes whose id starts with "dead-feed-"
    const deadFeedCheckboxes = document.querySelectorAll('input[id^="dead-feed-"]');
    const cleanUpDeadFeedsButton = document.getElementById('clean-up-dead-feeds-button');

    // Function to update button text and visibility based on checked count
    function updateButtonState() {
        const checkedCount = Array.from(deadFeedCheckboxes).filter(checkbox => checkbox.checked).length;

        // Save the original button content on first run if not already saved
        if (!cleanUpDeadFeedsButton.dataset.originalText) {
            const buttonText = cleanUpDeadFeedsButton.childNodes[0].textContent.trim();
            cleanUpDeadFeedsButton.dataset.originalText = buttonText;
        }

        // Get the original text which contains the i18n string
        const originalText = cleanUpDeadFeedsButton.dataset.originalText;

        // Replace the number in the text with the current count
        const updatedText = originalText.replace(/\d+/, checkedCount);

        // Update visibility based on count
        if (checkedCount > 0) {
            cleanUpDeadFeedsButton.style.display = 'block';
        } else {
            cleanUpDeadFeedsButton.style.display = 'none';
        }

        // Update only the text node, preserving the structure
        cleanUpDeadFeedsButton.childNodes[0].textContent = updatedText;

        // Make sure the HTMX indicator is preserved
        if (!cleanUpDeadFeedsButton.querySelector('.htmx-indicator')) {
            const indicatorSpan = document.createElement('span');
            indicatorSpan.className = 'htmx-indicator';
            indicatorSpan.textContent = '...';
            cleanUpDeadFeedsButton.appendChild(indicatorSpan);
        }
    }

    // Add change event listener to each checkbox
    deadFeedCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateButtonState);
    });

    // Initialize button state
    updateButtonState();
});
