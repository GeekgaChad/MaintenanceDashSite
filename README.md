# MaintenanceDashSite

## NDA-Safe Maintenance Dashboard Demo

This is a demo/preview of a **Site Maintenance Reporting Dashboard** built with [Streamlit](https://streamlit.io/) for internal use.

**All data in this repository is DUMMY/FAKE and safe for demo purposes. No confidential or real client data is present.**

---

### Features

- Multi-dashboard UI for Maintenance, Work Permits, QC, Patrol, and MAP activities
- Interactive data filtering and chart visualizations (trend, area, type breakdowns)
- Uploads with dummy/sample SQLite database (`sample_site_reporting.db`)
- Modular Python backend, designed for easy connection to production data
- NDA-safe for code reviews and demo

---

## How To Run Locally

1. **Clone this repository**
    ```bash
    git clone https://github.com/GeekgaChad/MaintenanceDashSite.git
    cd MaintenanceDashSite
    ```

2. **Create and activate a virtual environment (recommended)**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3. **Install the requirements**
    ```bash
    pip install -r requirements.txt
    ```

4. **Run the Streamlit app**
    ```bash
    streamlit run site_reporting_app.py
    ```

5. **Open in your browser:**  
   Go to [http://localhost:8501](http://localhost:8501) (Streamlit will provide the link).

---

## Project Structure

├── .gitignore
├── create_sample_db.py # Script to create the dummy/sample database
├── requirements.txt
├── sample_site_reporting.db # DUMMY sample SQLite DB for local testing
├── site_reporting_app.py # Main Streamlit app
├── sql_schema_script.py # (If present) Schema generation scripts
├── utils.py
├── ...

yaml
Copy
Edit

---

## Notes

- **Dummy DB Only:**  
  This repo includes only a DUMMY database (`sample_site_reporting.db`) to allow code review and feature testing.  
  **Replace with real DB in production.**

- **NDA Compliance:**  
  No proprietary or confidential client data is present here.

- **Customization:**  
  For production use, connect your real database and update user authentication as needed.

---

## Contact

For access, deployment, or integration questions, please contact [msagar2606@gmail.com].

---

