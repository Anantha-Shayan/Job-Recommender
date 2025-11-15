# Tech Job Listing API

A complete Node.js Express API designed to aggregate tech job listings from LinkedIn and Naukri.com, providing a standardized, filtered, and rate-limited endpoint.

## Setup Instructions

1.  **Prerequisites**
    *   Node.js (v18+ recommended)

2.  **Installation**
    *   Create a project directory and place all the provided .js files and package.json inside.
    *   Install dependencies:
        ```bash
        npm install
        ```

3.  **Environment Variables**
    *   Create a .env file in the root directory.
    *   The linkedin-jobs-api package may require a LinkedIn session cookie (li_at) for extensive scraping. While the current implementation attempts to scrape without it, for reliable, high-volume scraping, you might need to provide it.

    ```env
    PORT=3000
    # Optional: LinkedIn session cookie for reliable scraping
    # LINKEDIN_SESSION_COOKIE="your_li_at_cookie_value"
    ```

4.  **Run the API**
    ```bash
    npm start
    ```
    Or for development with nodemon:
    ```bash
    npm run dev
    ```

## API Documentation

The API runs on the configured port (default 3000) and uses the base path /api/jobs.

### 1. Get LinkedIn Jobs
Fetches jobs from LinkedIn, filtered by the API's internal tech role logic.
*   **Endpoint:** GET /api/jobs/linkedin
*   **Query Parameters:**
    *   keyword (string, required): Search term (e.g., 'Software Engineer').
    *   location (string, optional): Location (e.g., 'San Francisco').
    *   limit (number, optional, default: 10): Maximum number of jobs to return.
    *   experienceLevel (string, optional): 'entry_level', 'mid_senior_level', 'director', 'internship', 'associate', 'executive'.
    *   jobType (string, optional): 'full_time', 'part_time', 'contract', 'temporary', 'volunteer'.
    *   remoteFilter (string, optional): 'remote', 'on_site', 'hybrid'.

### 2. Get Naukri Jobs
Fetches jobs from Naukri.com, filtered by the API's internal tech role logic.
*   **Endpoint:** GET /api/jobs/naukri
*   **Query Parameters:**
    *   keyword (string, required): Search term (e.g., 'developer').
    *   location (string, optional): Location (e.g., 'Bangalore').
    *   limit (number, optional, default: 10): Maximum number of jobs to return.

### 3. Get All Jobs (Combined)
Fetches jobs from both LinkedIn and Naukri.com and combines the results.
*   **Endpoint:** GET /api/jobs/all
*   **Query Parameters:** Accepts all parameters from the LinkedIn and Naukri endpoints.

### Response Format
All successful responses return a JSON object containing the source, count, and an array of job objects.
