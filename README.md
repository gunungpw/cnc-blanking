# Automatic CNC Blanking Material

## Overview

CNC Blanking is a project designed to facilitate CNC (Computer Numerical Control) operations for blanking processes, specifically tailored for cutting or shaping materials using CNC machines. This repository contains scripts, configurations, and tools to streamline the blanking workflow, including G-code generation and machine control.

## Features
- G-code Generation: Scripts to generate G-code for CNC blanking tasks.
- Material Support: Configurable for various materials such as metal, wood, or composites.
- Compatibility: Works with GRBL-based CNC controllers and other common CNC systems.
- Customizable Parameters: Adjust feed rates, spindle speeds, and tool paths to suit specific requirements.

# Instructions for Running `blanking.py`

## Option 1: Using `uv`
`uv` is a Python package and project manager that simplifies running Python scripts and managing dependencies.

### Prerequisites
- Ensure you have `uv` installed. If not, install it by following the instructions at [uv documentation](https://github.com/astral-sh/uv).
- The repository should be cloned:
  ```bash
  git clone https://github.com/gunungpw/cnc-blanking.git
  cd cnc-blanking
  ```

### Steps
1. **Navigate to the Repository Directory**:
   ```bash
   cd path/to/cnc-blanking
   ```
2. **Run the Script with `uv`**:
   Use the `uv run` command to execute `blanking.py`:
   ```bash
   uv run blanking.py
   ```
3. Check the script's output in the terminal for any errors or logs.

## Option 2: Double-Clicking (as .pyw)
This method involves installing Python and converting the script to a `.pyw` file to run it without a console window by double-clicking.

### Prerequisites
- **Python Installation**: Install Python 3.4+ from [python.org](https://www.python.org/downloads/). Ensure the "Add Python to PATH" option is selected during installation.
- The repository should be cloned:
  ```bash
  git clone https://github.com/gunungpw/cnc-blanking.git
  cd cnc-blanking
  ```

### Steps
1. **Install Dependencies**:
   - Navigate to the repository directory:
     ```bash
     cd path/to/cnc-blanking
     ```

2. **Convert .py to .pyw**:
   - Rename `blanking.py` to `blanking.pyw`:
     - On Windows: Right-click `blanking.py`, select "Rename," and change the extension to `.pyw`.
     - On Linux/Mac: Run:
       ```bash
       mv blanking.py blanking.pyw
       ```
   - The `.pyw` extension suppresses the console window, making it ideal for scripts with a GUI or silent execution.
3. **Run the Script**:
   - Double-click the `blanking.pyw` file in your file explorer.
   - If Python is correctly associated with `.pyw` files, the script will execute.

### Notes
- On Windows: Right-click `blanking.pyw`, select "Open with" > "Choose another app" > Select `pythonw.exe`.

## Troubleshooting
- **uv Command Not Found**: Ensure `uv` is installed and added to your PATH. Run `pip install uv` or check the [uv installation guide](https://github.com/astral-sh/uv).
- **Module Not Found Errors**: Run `uv sync` or `pip install -r requirements.txt` to install missing dependencies.
- **Script Fails to Run**: Check the script for required arguments or configuration. View logs by running in a terminal:
  ```bash
  python blanking.py
  ```
