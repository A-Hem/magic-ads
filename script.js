
document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Element References ---
    const interestInput = document.getElementById('interest-input');
    const locationInput = document.getElementById('location-input'); // Although read-only, might read its value
    const findButton = document.getElementById('find-button');
    const loadingIndicator = document.getElementById('loading-indicator');
    const resultsArea = document.getElementById('results-area');
    const resultsOutput = document.getElementById('results-output');
    const errorArea = document.getElementById('error-area');
    const errorMessage = document.getElementById('error-message');
    const noResultsArea = document.getElementById('no-results-area');
    const currentTimeSpan = document.getElementById('current-time');

    // --- Function to Update Time in Footer ---
    const updateTime = () => {
        if (currentTimeSpan) {
            const now = new Date();
            // Format time simply for this example
            currentTimeSpan.textContent = now.toLocaleTimeString();
        }
    };

    // --- Main Function to Find Events ---
    const findEvents = async () => {
        const interest = interestInput.value.trim();
        const location = locationInput.value.trim(); // Read the value even if read-only

        // Basic validation
        if (!interest) {
            errorMessage.textContent = "Please enter a description of the events you are interested in.";
            errorArea.style.display = 'block';
            resultsArea.style.display = 'none'; // Hide other areas
            noResultsArea.style.display = 'none';
            return; // Stop execution
        }

        // --- Start UI Feedback ---
        findButton.disabled = true;
        findButton.textContent = 'Searching...';
        loadingIndicator.style.display = 'block';
        resultsArea.style.display = 'none';
        errorArea.style.display = 'none';
        noResultsArea.style.display = 'none';
        errorMessage.textContent = ''; // Clear previous errors

        // --- Prepare API Request Data ---
        const requestData = {
            interest_description: interest,
            location: location
            // timeframe_days: 14 // Example if we added this later
        };

        console.log("Sending request to /find-events:", requestData);

        try {
            // --- Call Backend API ---
            const response = await fetch('/find-events', { // Uses the relative path to your FastAPI endpoint
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json' // Indicate we expect JSON back
                },
                body: JSON.stringify(requestData)
            });

            // --- Handle API Response ---
            if (!response.ok) {
                // Try to get error details from response body
                let errorDetails = `HTTP error! Status: ${response.status}`;
                try {
                    const errorJson = await response.json();
                    // Use the error field from our Pydantic EventResponse model, or FastAPI's detail
                    errorDetails = errorJson.error || errorJson.detail || errorDetails;
                } catch (e) {
                    // Ignore if response body isn't valid JSON or parsing fails
                    console.warn("Could not parse error response JSON:", e);
                }
                throw new Error(errorDetails); // Throw error to be caught below
            }

            // Parse the successful JSON response (should match EventResponse model)
            const result = await response.json();
            console.log("Received response:", result);

            // Check if the backend itself reported an error in the response structure
            if (result.error) {
                throw new Error(result.error);
            }

            // --- Display Results ---
            const resultsText = result.results_text || ""; // Default to empty string if null/undefined

            // Check for the specific "no events found" message (adjust string if needed based on Gemini output)
            const noEventsFoundPattern = /No specific events matching.*were found/i; // Case-insensitive check
            if (!resultsText.trim() || noEventsFoundPattern.test(resultsText)) {
                // Show the dedicated "no results" message
                noResultsArea.style.display = 'block';
                resultsArea.style.display = 'none'; // Ensure main results area is hidden
            } else {
                // Populate and show the results area
                resultsOutput.textContent = resultsText; // Display the formatted text from backend
                resultsArea.style.display = 'block';
                noResultsArea.style.display = 'none'; // Ensure no-results area is hidden
            }

        } catch (error) {
            // --- Handle Errors (Network or API) ---
            console.error('Error finding events:', error);
            errorMessage.textContent = error.message || "An unknown error occurred.";
            errorArea.style.display = 'block';
            resultsArea.style.display = 'none'; // Hide results on error
            noResultsArea.style.display = 'none';

        } finally {
            // --- End UI Feedback ---
            loadingIndicator.style.display = 'none';
            findButton.disabled = false;
            findButton.textContent = 'Find Events';
        }
    };

    // --- Attach Event Listener ---
    if (findButton) {
        findButton.addEventListener('click', findEvents);
    } else {
        console.error("Could not find the 'Find Events' button element.");
    }

    // --- Initial Setup ---
    updateTime(); // Set initial time
    setInterval(updateTime, 60000); // Update time every minute

}); // End DOMContentLoaded

