import os
import json
import google.generativeai as genai
import google.generativeai.types as genai_types
from dotenv import load_dotenv
import datetime # Needed for date calculations

# Load environment variables
load_dotenv()

# --- Placeholder Tool Implementations --- (Keep as before, potentially useful later)
def _get_product_details_from_db(product_id: str) -> dict:
    print(f"--- TOOL EXECUTING: get_product_details_from_db (ID: {product_id}) ---")
    mock_db = {
        "prod_123": {"name": "Vintage Leather Jacket", "price": 85.00, "condition": "Used - Very Good", "stock": 1},
        "prod_456": {"name": "Trek Mountain Bike", "price": 250.00, "condition": "Used - Good", "stock": 0},
    }
    details = mock_db.get(product_id)
    return details if details else {"error": "Product ID not found"}

def _lookup_market_trends(category: str) -> dict:
    print(f"--- TOOL EXECUTING: lookup_market_trends (Category: {category}) ---")
    trends = {
        "clothing": {"trend": "Sustainable fabrics gaining popularity.", "avg_price_range": "$30-$150"},
        "bikes": {"trend": "E-bikes demand increasing, high-end models selling well.", "avg_price_range": "$200-$2000"},
        "electronics": {"trend": "Refurbished items offer good value, high demand for latest mobile tech.", "avg_price_range": "$50-$1000"},
    }
    trend_info = trends.get(category.lower())
    return trend_info if trend_info else {"info": "General market stable, specific trends unavailable."}

# --- Tool Executor Mapping --- (Keep as before)
tool_executor_map = {
    "get_product_details_from_db": _get_product_details_from_db,
    "lookup_market_trends": _lookup_market_trends,
}

# --- Tool Schema Definitions --- (Keep as before)
get_product_details_tool = genai_types.FunctionDeclaration(
    name="get_product_details_from_db",
    description="Get details about a specific product using its unique product ID from the internal database.",
    parameters=genai_types.Schema(
        type=genai_types.Type.OBJECT,
        properties={'product_id': genai_types.Schema(type=genai_types.Type.STRING, description="The unique identifier for the product.")},
        required=['product_id']
    )
)
lookup_trends_tool = genai_types.FunctionDeclaration(
    name="lookup_market_trends",
    description="Look up current market trends for a given product category.",
    parameters=genai_types.Schema(
        type=genai_types.Type.OBJECT,
        properties={'category': genai_types.Schema(type=genai_types.Type.STRING, description="The product category (e.g., 'clothing', 'electronics', 'bikes').")},
        required=['category']
    )
)
gemini_tools = genai_types.Tool(
    function_declarations=[get_product_details_tool, lookup_trends_tool]
)

# --- Model Initialization (Keep as before) ---
def initialize_model():
    """Initializes the Gemini model, configured with custom tools."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Gemini API key not found. Please set the GEMINI_API_KEY environment variable.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        'gemini-1.5-pro-latest',
        tools=[gemini_tools] # Keep tools configured
    )
    print("Gemini model initialized successfully (with tools configured).")
    return model

# --- NEW Function for Finding Local Events via Web Search ---
def find_local_events_via_search(
    model: genai.GenerativeModel,
    location: str,
    interest_description: str,
    timeframe_days: int = 14 # Search for events in the next X days
) -> str:
    """
    Uses Gemini's web search capability to find local events.

    Args:
        model: Initialized Gemini model.
        location: The target location (e.g., "Blaine, MN").
        interest_description: Natural language description of desired events.
        timeframe_days: How many days into the future to search for events.

    Returns:
        str: A formatted string summarizing the found events, or a message indicating none were found.

    Raises:
        Exception: If the API call fails or returns an error.
    """
    print(f"Searching for events matching '{interest_description}' in '{location}' for the next {timeframe_days} days.")

    # Calculate end date for search timeframe
    today = datetime.date.today()
    end_date = today + datetime.timedelta(days=timeframe_days)
    date_range_str = f"{today.strftime('%B %d, %Y')} and {end_date.strftime('%B %d, %Y')}"

    # --- Construct the Prompt for Web Search ---
    prompt = f"""
    Act as a helpful local event finder assistant for {location}. Your task is to find upcoming events based on a user's specific interest.

    **Location Focus:** {location} (and immediately surrounding areas if relevant).
    **Timeframe:** Events happening between {date_range_str}.
    **User's Interest:** Find events related to "{interest_description}". Interpret this interest broadly but accurately. For example, if the interest is 'live acoustic music', look for concerts, open mic nights, coffee shop performances etc. If it's 'volunteer gardening', look for park cleanups, community garden work days, planting events etc.

    **Instructions:**
    1.  **Use your web search capability extensively** to scan local news sites, city websites ({location.split(',')[0]} city website), community calendars, park districts, libraries, Facebook events (if accessible), Eventbrite, and other relevant online sources for {location}.
    2.  Filter the search results to find events that strongly match the user's interest: "{interest_description}".
    3.  For each matching event found, extract and list the following information clearly:
        * Event Name/Title
        * Date(s) and Time(s) (if available)
        * Specific Venue/Location (if available)
        * A brief summary or description of the event and why it matches the interest.
        * Source/Link where you found the information (if possible).
    4.  Format the results as a clean, easy-to-read list (e.g., using Markdown bullet points or numbered lists).
    5.  If you cannot find any events matching the criteria within the timeframe after searching, explicitly state that "No specific events matching '{interest_description}' were found in {location} for the next {timeframe_days} days."
    6.  Do not include events outside the specified timeframe.
    7.  Do not invent events. Only list events based on your web search findings.

    Begin search and report your findings.
    """

    print("\n--- Sending Prompt to Gemini (Web Search) ---")
    # print(prompt) # Uncomment to debug the exact prompt
    print("-------------------------------------------\n")

    try:
        # Send the prompt to the model (Tools are configured but likely won't be needed for this prompt)
        response = model.generate_content(prompt)

        # --- Handle the Response ---
        if not response.parts:
             if response.prompt_feedback.block_reason:
                 raise Exception(f"Content generation blocked. Reason: {response.prompt_feedback.block_reason.name}")
             else:
                 if hasattr(response, 'text') and response.text:
                    print("Warning: Response.parts empty, but text found.")
                    return response.text # Return text if available even without parts
                 raise Exception("Content generation failed. Received an empty response.")

        # Extract the generated text
        generated_text = response.text
        print("--- Received Response from Gemini (Web Search) ---")
        # print(generated_text) # Uncomment to see raw output
        print("-----------------------------------------------\n")
        return generated_text

    except Exception as e:
        print(f"Error during Gemini API call for event search: {e}")
        # Re-raise the exception to be handled by the FastAPI endpoint
        raise

# --- Keep the function for tool-based generation if needed for other features ---
# (generate_content_with_tools function from previous steps can remain here)
# def generate_content_with_tools(...)
# ...

# --- Example Usage (for testing this module directly) ---
if __name__ == "__main__":
    try:
        test_model = initialize_model()
        location_test = "Blaine, MN"
        interest_test = "free outdoor concerts or live music"

        print(f"\n--- Direct Module Test: Finding Events ---")
        generated_events = find_local_events_via_search(test_model, location_test, interest_test)
        print("\n--- Final Output ---")
        print(generated_events)

    except Exception as e:
        print(f"An error occurred during testing: {e}")