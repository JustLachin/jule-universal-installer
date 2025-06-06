import sys
import os
import json
import zipfile
import requests
import winreg
import shutil
import subprocess
import win32gui
import win32con
import win32com.client
import ctypes
from datetime import datetime
from shortcut import create_shortcut
from PyQt5.QtWidgets import (QApplication, QWizard, QWizardPage, QLabel, 
                           QVBoxLayout, QCheckBox, QProgressBar, QLineEdit, 
                           QPushButton, QFileDialog, QComboBox, QHBoxLayout,
                           QScrollArea, QWidget, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QIcon

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    
    return os.path.join(base_path, relative_path)

GITHUB_API_URL = "https://api.github.com/repos/julelang/jule/releases"
DEFAULT_INSTALL_PATH = os.path.expanduser("~\\jule")

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, destination):
        super().__init__()
        self.url = url
        self.destination = destination

    def run(self):
        try:
            response = requests.get(self.url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            downloaded = 0

            with open(self.destination, 'wb') as f:
                for data in response.iter_content(block_size):
                    downloaded += len(data)
                    f.write(data)
                    progress = int((downloaded / total_size) * 100)
                    self.progress.emit(progress)
            
            self.finished.emit(self.destination)
        except Exception as e:
            self.error.emit(str(e))

class VersionInfo:
    def __init__(self, version, date, description, download_url):
        self.version = version
        self.date = date
        self.description = description
        self.download_url = download_url

class VersionSelectionPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Select Jule Version")
        self.versions = []
        layout = QVBoxLayout()
        
        # Version selection combo box
        version_layout = QHBoxLayout()
        version_label = QLabel("Version:")
        version_label.setFixedWidth(100)
        self.version_combo = QComboBox()
        self.version_combo.currentIndexChanged.connect(self.update_version_info)
        version_layout.addWidget(version_label)
        version_layout.addWidget(self.version_combo)
        layout.addLayout(version_layout)
        
        # Version info area
        info_scroll = QScrollArea()
        info_scroll.setWidgetResizable(True)
        info_scroll.setMinimumHeight(200)
        
        info_widget = QWidget()
        self.info_layout = QVBoxLayout(info_widget)
        
        # Release date
        date_layout = QHBoxLayout()
        date_label = QLabel("Release Date:")
        date_label.setFixedWidth(100)
        self.date_value = QLabel()
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_value)
        self.info_layout.addLayout(date_layout)
        
        # Description
        desc_label = QLabel("Description:")
        self.info_layout.addWidget(desc_label)
        self.desc_text = QLabel()
        self.desc_text.setWordWrap(True)
        self.desc_text.setTextFormat(Qt.MarkdownText)
        self.desc_text.setOpenExternalLinks(True)
        self.info_layout.addWidget(self.desc_text)
        
        info_scroll.setWidget(info_widget)
        layout.addWidget(info_scroll)
        
        # Loading indicator
        self.loading_label = QLabel("Loading versions from GitHub...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.loading_label)
        
        self.setLayout(layout)
        
        # Start loading versions
        self.load_versions_thread = LoadVersionsThread()
        self.load_versions_thread.versions_loaded.connect(self.on_versions_loaded)
        self.load_versions_thread.error.connect(self.on_load_error)
        self.load_versions_thread.start()
        
        # Register fields
        self.registerField("selected_version*", self.version_combo, "currentText")
        self.registerField("download_url*", self.version_combo, "currentData")
    
    def on_versions_loaded(self, versions):
        self.versions = versions
        self.loading_label.hide()
        
        if not versions:
            self.show_error("Could not load Jule versions!")
            return
        
        for version in versions:
            self.version_combo.addItem(
                f"Version {version.version}",
                version.download_url
            )
        
        # Select first version
        self.version_combo.setCurrentIndex(0)
        self.update_version_info(0)
    
    def on_load_error(self, error):
        error_msg = f"Error loading version information: {error}"
        self.loading_label.setText(error_msg)
        QMessageBox.critical(self, "Error", error_msg)
    
    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)
    
    def update_version_info(self, index):
        if 0 <= index < len(self.versions):
            version = self.versions[index]
            self.date_value.setText(version.date)
            self.desc_text.setText(version.description)

class LoadVersionsThread(QThread):
    versions_loaded = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def run(self):
        try:
            response = requests.get(GITHUB_API_URL)
            response.raise_for_status()
            releases = response.json()
            
            versions = []
            for release in releases:
                # Get Windows asset
                windows_asset = next(
                    (asset for asset in release["assets"] 
                     if "windows" in asset["name"].lower()),
                    None
                )
                
                if windows_asset:
                    # Parse date
                    date_str = release["published_at"].split("T")[0]
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                    formatted_date = date.strftime("%B %d, %Y")
                    
                    version = VersionInfo(
                        version=release["tag_name"],
                        date=formatted_date,
                        description=release["body"],
                        download_url=windows_asset["browser_download_url"]
                    )
                    versions.append(version)
            
            self.versions_loaded.emit(versions)
        except Exception as e:
            self.error.emit(str(e))

class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Jule Programming Language Installation")
        layout = QVBoxLayout()
        
        # Logo
        logo_label = QLabel()
        logo_path = get_resource_path("logo.png")
        logo_pixmap = QPixmap(logo_path)
        if not logo_pixmap.isNull():
            scaled_pixmap = logo_pixmap.scaled(200, 200, Qt.KeepAspectRatio, 
                                             Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            print(f"Error: Could not load logo: {logo_path}")
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        
        # Welcome message
        welcome = QLabel(
            "Welcome to the Jule programming language installation wizard.\n\n" +
            "Click Next to continue."
        )
        welcome.setWordWrap(True)
        welcome.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome)
        
        self.setLayout(layout)

class InstallationPathPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Installation Location")
        layout = QVBoxLayout()

        self.path_edit = QLineEdit(DEFAULT_INSTALL_PATH)
        self.registerField("install_path*", self.path_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_path)

        self.add_to_path = QCheckBox("Add Jule to system PATH")
        self.add_to_path.setChecked(True)
        self.registerField("add_to_path", self.add_to_path)

        layout.addWidget(QLabel("Select installation location:"))
        layout.addWidget(self.path_edit)
        layout.addWidget(browse_btn)
        layout.addWidget(self.add_to_path)
        self.setLayout(layout)

    def browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Installation Location", 
                                              DEFAULT_INSTALL_PATH)
        if path:
            self.path_edit.setText(path)

class InstallationPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Installation")
        layout = QVBoxLayout()

        self.progress = QProgressBar()
        self.status = QLabel("Starting installation...")
        self.status.setWordWrap(True)

        layout.addWidget(self.status)
        layout.addWidget(self.progress)
        self.setLayout(layout)

    def setup_registry_entries(self):
        """Setup Windows registry entries for Control Panel"""
        try:
            # Registry path for installed programs
            reg_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\JuleLang"
            
            # Create registry key
            key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE)
            
            # Set registry values
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "Jule Programming Language")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Jule Development Team")
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, self.install_path)
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, os.path.join(self.install_path, "logo.png"))
            
            # Close registry key
            winreg.CloseKey(key)
        except Exception as e:
            self.show_error(f"Failed to create registry entries: {str(e)}")

    def initializePage(self):
        self.install_path = self.field("install_path")
        self.add_to_path = self.field("add_to_path")
        
        # Get download URL
        download_url = self.field("download_url")
        if not download_url:
            self.show_error("Download URL not found!")
            return
        
        self.status.setText("Downloading...")
        self.download_thread = DownloadThread(
            download_url,
            os.path.join(self.install_path, "jule.zip")
        )
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(self.extract_files)
        self.download_thread.error.connect(self.show_error)
        self.download_thread.start()

    def update_progress(self, value):
        self.progress.setValue(value)
        self.status.setText(f"Downloading... {value}%")

    def cleanup_temp_files(self):
        """Clean up temporary files after installation"""
        try:
            # Files to remove
            files_to_remove = [
                "jule_idle.py",
                "jule_interpreter.py",
                "logo.png"
            ]
            
            for file in files_to_remove:
                file_path = os.path.join(os.path.dirname(__file__), file)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Error: {file} could not be removed: {e}")
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def extract_files(self, zip_path):
        try:
            self.status.setText("Extracting files...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.install_path)
            
            # Remove downloaded zip file
            os.remove(zip_path)
            
            # Add to PATH (if requested)
            if self.add_to_path:
                self.add_to_system_path()
            
            # Setup registry entries
            self.setup_registry_entries()
            
            # Create shortcuts
            self.create_shortcuts()
            
            # Clean up temporary files
            self.cleanup_temp_files()
            
            self.status.setText("Installation completed successfully!")
            self.progress.setValue(100)
        except Exception as e:
            self.show_error(f"Error extracting files: {str(e)}")

    def add_to_system_path(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               "Environment", 
                               0, 
                               winreg.KEY_ALL_ACCESS)
            
            current_path = winreg.QueryValueEx(key, "Path")[0]
            new_path = f"{current_path};{self.install_path}"
            # Clean up temporary file if needed
            if not hasattr(editor, "file_path") and os.path.exists(temp_file):
                os.remove(temp_file)

            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
            winreg.CloseKey(key)
        except Exception as e:
            self.show_error(f"Error setting PATH: {str(e)}")

    def show_error(self, error_msg):
        self.status.setText(f"Error: {error_msg}")
        
    def create_shortcuts(self):
        """Create desktop shortcuts for Jule"""
        try:
            # Create Jule Interpreter shortcut
            jule_exe = os.path.join(self.install_path, "jule.exe")
            if os.path.exists(jule_exe):
                create_shortcut(
                    jule_exe,
                    "Jule Interpreter",
                    icon_path=jule_exe,
                    description="Jule Programming Language Interpreter"
                )
            
            # Copy the interpreter and IDLE Python files
            self.copy_interpreter_files()
            
            # Create IDLE Jule shortcut
            idle_script = os.path.join(self.install_path, "jule_idle.py")
            if os.path.exists(idle_script):
                create_shortcut(
                    sys.executable,
                    "IDLE Jule",
                    arguments=f'"{idle_script}"',
                    icon_path=get_resource_path("logo.png"),
                    description="Jule Integrated Development Environment"
                )
        except Exception as e:
            self.show_error(f"Failed to create shortcuts: {str(e)}")
    

    

class CompletionPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Installation Complete")
        layout = QVBoxLayout()
        
        info = QLabel(
            "Jule has been successfully installed!\n\n"
            "System PATH has been updated. You may need to restart your "
            "terminal windows for the changes to take effect.\n\n"
            "Shortcuts for Jule Interpreter and IDLE Jule have been created on your desktop.\n\n"
            "Click Finish to complete the installation."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        self.setLayout(layout)

class JuleInstaller(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jule Setup")
        self.setWizardStyle(QWizard.ModernStyle)

        self.addPage(WelcomePage())
        self.addPage(VersionSelectionPage())
        self.addPage(InstallationPathPage())
        self.addPage(InstallationPage())
        self.addPage(CompletionPage())

        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

def main():
    # Check admin rights
    if not is_admin():
        # Restart as administrator
        try:
            if sys.argv[-1] != 'asadmin':
                script = os.path.abspath(sys.argv[0])
                params = ' '.join([script] + sys.argv[1:] + ['asadmin'])
                shell32.ShellExecuteW(
                    None, 'runas', sys.executable, params, None, 1
                )
                sys.exit()
        except Exception as e:
            QMessageBox.critical(
                None,
                "Error",
                "Could not obtain administrator rights!\n" +
                "Please run the installer as administrator.\n\n" +
                f"Error: {str(e)}"
            )
            sys.exit(1)
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create and show installer
    installer = JuleInstaller()
    
    # Window icon
    icon_path = get_resource_path("logo.ico")
    if os.path.exists(icon_path):
        installer.setWindowIcon(QIcon(icon_path))
    
    installer.show()
    
    # Start application loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
