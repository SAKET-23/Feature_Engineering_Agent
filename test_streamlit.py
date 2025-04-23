import streamlit as st
import subprocess
import os
from pathlib import Path
from streamlit_ace import st_ace

st.set_page_config(layout="wide")
st.title("🧠 AI-powered IDE")

# 📁 Select Folder from Sidebar
st.sidebar.header("📁 Choose Project Folder")
project_dir = st.sidebar.text_input("Paste the path to your project folder:", value="./generated_code")
project_path = Path(project_dir)
project_path.mkdir(parents=True, exist_ok=True)

# 📄 List Files
def list_files_recursively(path):
    return [f.relative_to(path) for f in path.rglob("*") if f.is_file() and f.suffix in [".py", ".txt", ".md", ".json"]]

st.sidebar.markdown("---")
st.sidebar.subheader("📄 Files")
file_list = ["<New File>"] + [str(f) for f in list_files_recursively(project_path)]
selected_file = st.sidebar.selectbox("Select File:", file_list)

# Editor Logic
st.subheader("📝 Code Editor")
col1, col2 = st.columns([3, 2])

with col1:
    if selected_file == "<New File>":
        filename = st.text_input("New filename (e.g. `script.py`):", "new_script.py")
        file_path = project_path / filename
        code_text = ""
    else:
        file_path = project_path / selected_file
        with open(file_path, "r", encoding="utf-8") as f:
            code_text = f.read()

    # Using st_ace for better editing experience
    code = st_ace(value=code_text, language="python", theme="monokai", height=400, key="ace-editor")

    if st.button("💾 Save Code"):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
        st.success(f"Saved: {file_path.relative_to(project_path)}")

with col2:
    st.markdown("### ▶️ Terminal Output")
    if st.button("Run Code") and file_path.suffix == ".py":
        with st.spinner("Running script..."):
            result = subprocess.run(["python", str(file_path)], capture_output=True, text=True)
            st.text_area("📤 Output", result.stdout + result.stderr, height=300)

# Logs placeholder
st.markdown("---")
st.markdown("Built with 💡 by your AI Agent")

