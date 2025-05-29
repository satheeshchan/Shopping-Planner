# Shopping-Planner



## **Project Title: "Smart German Grocery Deal Finder (Wochenprospekt Optimierer)" - AI-Powered Edition**

**Problem Statement:**
In Germany, consumers receive weekly physical or digital offer brochures ("Werbung" or "Prospekte") from numerous supermarkets like Aldi (Süd/Nord), Edeka, Lidl, Rewe, Kaufland, Globus, Netto, etc. Manually sifting through each brochure to compare prices for specific grocery items is incredibly time-consuming and inefficient. Users want to optimize their weekly shopping by identifying the cheapest sources for their desired items across multiple stores, thereby maximizing savings and planning efficient shopping routes.

**Goal:**
Develop a fully functional, user-friendly web application that leverages advanced AI models (like Google Gemini, OpenAI GPT-4 Vision, etc.) to automate the comparison of weekly supermarket offers, generate an optimized shopping list grouped by store, and quantify potential savings for the user. The application itself will act as an intelligent agent orchestrating these AI capabilities.

---

### **I. Core Functionality & User Flow:**

1.  **User Location & Store Selection:**
    *   The app should prompt the user to enter a **German postal code (PLZ)** or city.
    *   Based on the input, the app should automatically identify and display a list of commonly available supermarkets in that region (e.g., Aldi Süd, Aldi Nord, Edeka, Lidl, Rewe, Kaufland, Globus, Netto, Penny).
    *   The user can then **select their preferred supermarkets** from this list.

2.  **Brochure Acquisition & AI Processing (CORE AI INTEGRATION):**
    *   **Primary Method (Automated):** The app will attempt to fetch the *current week's* and ideally *next week's (if available)* digital offer brochures automatically. These are typically interactive flipbooks (like the Aldi Süd example: `https://prospekt.aldi-sued.de/kw22-25-op-mp/page/1`).
    *   **Alternative Method (User Upload):** If automatic acquisition is not feasible or fails for a particular store, the user must be given an explicit option to **upload PDF versions of the weekly brochures** for each selected supermarket.
    *   **AI Model Integration:** Crucially, for *both* automatically acquired (scraped) content and uploaded PDF content, the application will act as an intelligent agent that leverages **external, user-provided AI models (e.g., Google Gemini API, OpenAI API like GPT-4 Vision)** for intelligent content parsing.
        *   The user will be prompted to provide their respective **API Key** for these services within the application settings or upon first use.
        *   The application will be responsible for sending the necessary data (e.g., extracted text, image representations of brochure pages) to the chosen AI API.

3.  **Grocery List Input:**
    *   The user is provided with a simple interface (e.g., a multi-line text area or an input field with an "Add" button) to **add their desired grocery items**.
    *   Input should be flexible (e.g., "Tomaten", "Milch", "Brot", "Hackfleisch Rind").
    *   Users should also be able to specify quantities if desired (e.g., "Tomaten 1kg", "Milch 2 Liter"). If no quantity is specified, a default (e.g., 1 unit/pack) can be assumed.

4.  **Intelligent Comparison Engine (AI-Powered Core Logic):**
    *   Instead of implementing proprietary NLP/OCR logic, the application will act as an orchestrating agent, feeding the processed brochure content (either text extracted via scraping, or image/text from uploaded PDFs) to the user's provided AI model API.
    *   **The AI model's role will be to:**
        *   **Extract Structured Data:** Accurately identify and extract product names, prices, units (e.g., €/kg, €/pack, €/Liter), and any specific offer conditions (e.g., "Kaufe 2, zahle 1", "Ab 3 Packungen X€") from the unstructured brochure content.
        *   **Semantic Understanding & Matching:** Interpret the user's grocery list items and semantically match them to the extracted product offers from the brochures. This includes handling variations, synonyms, and different phrasing (e.g., matching "Tomaten" to "Rispentomaten", "Vollmilch" to "Frische Vollmilch 3.5%"). The AI should be robust in identifying the correct product despite slight textual differences.
        *   **Unit Standardization & Comparison:** Where applicable, the AI model should assist in or provide sufficient context for the application to standardize units for direct price comparison (e.g., converting 500g price to €/kg, or unit price for multi-packs).
        *   **Contextual Awareness:** Understand complex offers like multi-buy discounts or tiered pricing (e.g., "3 for 2", "buy 2 for X€").
    *   The application will then process the structured data received from the AI model to determine the lowest price for each specific item across all selected stores.

5.  **Personalized Shopping Plan Generation:**
    *   The app will generate an **optimized shopping list** for the user.
    *   **Grouped by Supermarket:** The list should be clearly grouped by the supermarket where each item is cheapest.
    *   For each supermarket:
        *   List the items to buy there.
        *   Display the individual price and quantity.
        *   Show a subtotal for that specific store.
    *   **Overall Summary:**
        *   Display the **total estimated cost** if the user follows the optimized plan.
        *   Clearly show the **total potential savings**. This can be calculated by comparing the optimized total cost against a baseline (e.g., what it would cost to buy all items at the most expensive option found for each item, or if all items were bought at a single, user-selected 'base' store).
        *   A clear "You saved X€ / Y%" statement.

6.  **User-Friendly Enhancements (Optional/Future Considerations):**
    *   Ability to **adjust quantities** of items on the generated list.
    *   Option to **exclude specific items** from a particular store's recommendation (e.g., "I don't want to go to Aldi for just one item").
    *   Visual representation of savings.
    *   Ability to **save/print** the generated list.

---

### **II. Technical Considerations:**

*   **Technology Stack:** The agent should select an appropriate web development stack (e.g., Python/Django/Flask, Node.js/React/Vue, etc.) that best supports the requirements, particularly the dynamic interaction with external APIs.
*   **AI API Integration:**
    *   Robust client implementations for Google Gemini API, OpenAI API (and potentially others).
    *   Secure handling and storage of user-provided API keys.
    *   Efficient rate limit management and error handling for API calls.
*   **Data Pre-processing for AI:**
    *   For automatically acquired brochures, intelligently extract content (text, or images of pages if needed by multimodal models).
    *   For uploaded PDFs, implement PDF parsing capabilities (e.g., converting PDF pages to images or extracting text chunks) suitable for input to the AI models.
    *   **Prompt Engineering:** The application's agent logic must be capable of crafting effective and precise prompts for the AI models to ensure accurate extraction of product data and semantic matching.
*   **Database:** To store user preferences, temporary cached offer data (to reduce API calls for identical brochure processing), and potentially processed structured data for faster retrieval.
*   **Scalability:** Design for potential future growth in users and data volume, considering API usage costs.
*   **Responsiveness:** The web app must be fully responsive and work seamlessly on desktop, tablet, and mobile devices.
*   **Error Handling:** Graceful handling of errors (e.g., AI API failures, no offers found, item not found, invalid API key).

---

### **III. User Interface (UI) & User Experience (UX) Guidelines:**

*   **Clean & Intuitive:** The interface should be simple, uncluttered, and easy for anyone to understand and use.
*   **Mobile-First Design:** Prioritize the mobile experience.
*   **Clear Visual Feedback:** Provide clear loading indicators, success messages, and error notifications, especially when interacting with AI APIs (e.g., "Processing offers with AI...").
*   **Accessibility:** Ensure the app is accessible to users with disabilities.
*   **German Localization:** All UI text and outputs should be in German.

---

### **IV. Deployment:**

*   The agent should aim to deploy the web application to a suitable cloud platform (e.g., Google Cloud Platform, AWS, Azure, Heroku, Vercel) as a publicly accessible web service.

---

### **V. Success Metrics:**

*   **Accuracy of AI-driven Data Extraction & Matching:** The most critical metric. The generated shopping lists and savings calculations must be based on correctly identified products and prices.
*   **User Satisfaction:** Positive feedback on ease of use and utility.
*   **Performance:** Fast loading times and quick processing of grocery lists, considering AI API latencies.
*   **Reliability of Brochure Acquisition:** Consistent success in either scraping or handling user PDF uploads.
*   **Cost-Effectiveness (AI API Usage):** Implement strategies to minimize unnecessary API calls where possible (e.g., caching processed brochure data).

---

**Example Offer Link for Reference (for automated acquisition attempt):**
*   Aldi Süd (KW 22-25, Op-Mp): `https://prospekt.aldi-sued.de/kw22-25-op-mp/page/1`
    *(Note: Other supermarkets will have different formats and URLs. The agent will need to discover and adapt to these for automated acquisition or guide the user for PDF uploads.)*

---

**Final Request to Agent:**
"Please proceed with the design, development, and deployment of the 'Smart German Grocery Deal Finder' web application. Crucially, architect the application as an intelligent agent that primarily leverages external, user-provided AI models (like Google Gemini or OpenAI) for robust data extraction and semantic understanding of supermarket offers. Prioritize accurate AI processing and a highly practical, user-friendly solution that significantly simplifies weekly grocery shopping in Germany."
