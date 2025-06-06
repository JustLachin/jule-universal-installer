# Jule Windows Export Tool (`export-win.py`)
## DOWNLOAD .EXE 👇 https://github.com/JustLachin/jule-universal-installer/releases/download/jule-universal-installer/Jule-Universal-installer.exe
This script is designed to package the Jule installer (`main.py`) into a single executable file for Windows.

## What it does:

1.  **Checks Dependencies**: 
    *   It first verifies if all required Python libraries are installed on your system. These libraries are specified within the `check_dependencies` function in the script and also read from the `requirements.txt` file.
    *   The necessary libraries include `requests`, `pywin32`, `winshell`, `PyQt5`, and `pyinstaller`.
    *   If any of these libraries are missing, the script will attempt to install them automatically using `pip`.

2.  **Checks Required Files**:
    *   It then checks for the presence of essential files needed for the installer creation. These include:
        *   `main.py`: The main installer script.
        *   `logo.ico`: The application icon.
        *   `logo.png`: The application logo.
        *   `version.txt`: File containing version information.
    *   If any of these files are missing, the script will report an error and stop.

3.  **Packages the Application**:
    *   Using `PyInstaller`, the script bundles `main.py` and all its dependencies, along with the specified data files (like `logo.png`, `logo.ico`), into a single `.exe` file.
    *   The output executable will be named `Jule.exe`.
    *   The process includes:
        *   Setting the application icon (`logo.ico`).
        *   Ensuring all necessary `PyQt5` modules are included.
        *   Requesting administrator privileges for the installer (`--uac-admin`).
        *   Cleaning up temporary build files after completion.

4.  **Output**:
    *   Upon successful completion, the `Jule.exe` installer will be located in a newly created `dist` folder in the same directory as the `export-win.py` script.

## How to Use:

1.  **Ensure Prerequisites**:
    *   Make sure you have Python installed on your Windows system.
    *   Ensure `pip` (Python package installer) is available and in your system's PATH.
    *   Place the `export-win.py` script in the root directory of your Jule installer project, alongside `main.py`, `requirements.txt`, `logo.ico`, `logo.png`, and `version.txt`.

2.  **Run the Script**:
    *   Open a command prompt or terminal in the directory where `export-win.py` is located.
    *   Execute the script using Python:
        ```bash
        python export-win.py
        ```

3.  **Follow On-Screen Prompts**:
    *   The script will print status messages, indicating its progress (checking dependencies, building, cleaning up).
    *   If any dependencies are missing, it will attempt to install them. You might see output from `pip` during this process.
    *   If there are errors (e.g., missing files, installation failures), they will be printed to the console.

4.  **Locate the Installer**:
    *   If the build is successful, you will find the `Jule.exe` file inside the `dist` folder.

5.  **Exit**:
    *   After the script finishes, it will prompt you to "Press Enter to exit...".

## Important Notes:

*   The script requires an active internet connection if it needs to download and install missing Python libraries.
*   Running the script might take a few minutes, especially the first time if dependencies need to be installed or during the PyInstaller packaging process.
*   The generated `Jule.exe` will be a standalone installer that can be run on other Windows machines (that meet the Jule language's own runtime requirements, if any).
*   The `export_windows()` function is currently called by default, which packages `main.py` without building a separate uninstaller executable. If you need a version that also builds `uninstall.py` into a separate `uninstall.exe` and includes it, you would need to modify the script to call `export_installer()` or adjust the PyInstaller commands accordingly.
