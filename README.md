# AI Agent for Feature Engineering


## 📦 Prerequisites

Before running the application, ensure to run the following command:
- Preferred to create a virtual environment.
- pip install -r requirement.txt
- Python==3.12

---

## 🧰 Setup & Run Instructions

### 1. 🔐 Set OpenAI API Key

You must have a valid OpenAI API key to use AI-related features.

- Create a file named `.env` in the root directory:
    - `OPENAI_API_KEY= XXXXX`
  

### 2. To the program
Use the following command to run the program.
- streamlit run app.py

Note that the program takes only .csv file as the input.

### Prompts to test
- List the column names
- Plot a bar/violin/pie chart of `target_column_name`.

To perform Feature Engineering use the following prompt.
- Perform Feature Engineering with target column as `target_column_name`