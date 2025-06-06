import os
import sys
import shutil
import subprocess
import time

# ANSI codes for colored output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'

def print_status(msg, color=Colors.RESET):
    print(f"{color}{msg}{Colors.RESET}")

def print_success(msg):
    print_status(msg, Colors.GREEN)

def print_error(msg):
    print_status(msg, Colors.RED)

def print_info(msg):
    print_status(msg, Colors.YELLOW)

def install_package(package):
    print_info(f"\nChecking: {package}...")
    try:
        __import__(package)
        print_success(f"{package} is already installed.")
        return True
    except ImportError:
        print_info(f"{package} is being installed...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                check=True,
                capture_output=True,
                text=True
            )
            print_success(f"{package} installed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print_error(f"Error installing {package}: {e.stderr}")
            return False

def check_dependencies():
    print_info("\nChecking required libraries...")
    # main.py, requirements.txt ve export-win.py'den gelen tüm bağımlılıklar
    dependencies = [
        'requests',
        'pywin32',
        'winshell',
        'PyQt5',
        'pyinstaller'  # export-win.py'nin kendisi için
    ]
    
    # requirements.txt dosyasını oku ve bağımlılıklara ekle
    try:
        with open('requirements.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Sürüm belirtimlerini kaldır (örn: PyQt5==5.15.9 -> PyQt5)
                    package_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('!=')[0].split('~=')[0]
                    if package_name not in dependencies:
                        dependencies.append(package_name)
    except FileNotFoundError:
        print_warning("requirements.txt not found. Skipping additional dependency checks from this file.")
    except Exception as e:
        print_warning(f"Error reading requirements.txt: {e}")

    all_installed = True
    for dep in list(set(dependencies)): # Benzersiz bağımlılıklar için listeyi kopyala
        if not install_package(dep):
            all_installed = False
    return all_installed

def build_uninstaller():
    """Build the uninstaller"""
    try:
        print_info("\nBuilding uninstaller...")
        show_spinner(1)
        
        # Build uninstaller with PyInstaller
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller",
             "--name=uninstall",
             "--onefile",
             "--noconsole",
             "--icon=logo.ico",
             "--add-data=logo.png;.",
             "--add-binary=logo.png;.",
             "--collect-all=PyQt5",
             "--hidden-import=PyQt5.QtCore",
             "--hidden-import=PyQt5.QtGui",
             "--hidden-import=PyQt5.QtWidgets",
             "--hidden-import=PyQt5.sip",
             "--version-file=version.txt",
             "--uac-admin",
             "--clean",
             "uninstall.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print_error(f"\nError building uninstaller:\n{result.stderr}")
            return False
        
        # Cleanup
        if os.path.exists('uninstall.spec'):
            os.remove('uninstall.spec')
        
        return True
        
    except Exception as e:
        print_error(f"\nError building uninstaller: {str(e)}")
        return False

def check_requirements():
    # Check required files
    required_files = {
        'main.py': 'Main installer script',
        'logo.ico': 'Application icon',
        'logo.png': 'Application logo',
        'uninstall.py': 'Uninstaller script',
        'version.txt': 'Version information'
    }
    
    missing_files = []
    for file, desc in required_files.items():
        if not os.path.exists(file):
            missing_files.append(f"- {file}: {desc}")
    
    if missing_files:
        print_error("\nMissing required files:")
        for msg in missing_files:
            print_error(msg)
        return False
    
    # Check icon file
    try:
        icon_size = os.path.getsize('logo.ico')
        if icon_size < 1024:  # Less than 1KB
            print_error("\nWarning: logo.ico file seems too small!")
            print_error("Icon may not display correctly.")
    except:
        pass
    
    return True

def show_spinner(duration):
    chars = "-\|/"
    start_time = time.time()
    i = 0
    while time.time() - start_time < duration:
        sys.stdout.write(f'\r{chars[i]} ')
        sys.stdout.flush()
        time.sleep(0.1)
        i = (i + 1) % len(chars)
    sys.stdout.write('\r')
    sys.stdout.flush()

def export_installer():
    try:
        # Show title
        print("\n" + "=" * 50)
        print_info("Jule Installer Export Tool")
        print("=" * 50 + "\n")
        
        # Check requirements
        print_info("\nChecking requirements...")
        show_spinner(1)
        if not check_requirements():
            return
        
        # Build installer with PyInstaller
        print_info("\nBuilding installer...")
        show_spinner(1)
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller",
             "--name=Jule",
             "--onefile",
             "--noconsole",
             "--icon=logo.ico",
             "--add-data=logo.png;.",
             "--add-binary=logo.ico;.",
             "--collect-all=PyQt5",
             "--hidden-import=PyQt5.QtCore",
             "--hidden-import=PyQt5.QtGui",
             "--hidden-import=PyQt5.QtWidgets",
             "--hidden-import=PyQt5.sip",
             "--specpath=.",
             "--version-file=version.txt",
             "--uac-admin",
             "--clean",
             "main.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print_error(f"\nError occurred:\n{result.stderr}")
            return
        
        # Cleanup
        print_info("\nCleaning up...")
        show_spinner(1)
        # Removed temp_dir from cleanup as it's no longer created
        for item in ['build', '__pycache__', 'main.spec']:
            try:
                if os.path.isdir(item):
                    shutil.rmtree(item)
                elif os.path.exists(item):
                    os.remove(item)
            except Exception as e:
                print_error(f"\nError cleaning {item}: {e}")
        
        # Success message
        print("\n" + "=" * 50)
        print_success("Build completed successfully!")
        print_success("Installer created in 'dist' folder.")
        print("=" * 50 + "\n")
        
    except Exception as e:
        print_error(f"\nAn error occurred: {str(e)}")

def export_windows():
    try:
        # Show title
        print("\n" + "=" * 50)
        print_info("Jule Windows Export Tool")
        print("=" * 50 + "\n")
        
        # Check dependencies
        if not check_dependencies(): # Güncellenmiş fonksiyon çağrısı
            print_error("\nRequired libraries could not be installed. Please install them manually.")
            return
        
        # Check required files
        print_info("\nChecking required files...")
        show_spinner(1)
        if not check_requirements():
            return
        
        # Build with PyInstaller
        print_info("\nPackaging application...")
        show_spinner(1)
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller",
             "--name=Jule",
             "--onefile",
             "--noconsole",
             "--icon=logo.ico",
             "--add-data=logo.png;.",
             "--add-data=uninstall.py;.",
             "--add-binary=logo.ico;.",
             "--add-binary=logo.png;.",  # Also add logo as binary
             "--collect-all=PyQt5",  # Collect all PyQt5 modules
             "--hidden-import=PyQt5.QtCore",
             "--hidden-import=PyQt5.QtGui",
             "--hidden-import=PyQt5.QtWidgets",
             "--hidden-import=PyQt5.sip",
             "--specpath=.",
             "--version-file=version.txt",
             "--uac-admin",
             "--clean",
             "main.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print_error(f"\nError occurred:\n{result.stderr}")
            return
        
        # Cleanup
        print_info("\nCleaning up...")
        show_spinner(1)
        for item in ['build', '__pycache__', 'main.spec', 'uninstall.spec']:
            try:
                if os.path.isdir(item):
                    shutil.rmtree(item)
                elif os.path.exists(item):
                    os.remove(item)
            except Exception as e:
                print_error(f"\nError cleaning {item}: {e}")
        
        # Success message
        print("\n" + "=" * 50)
        print_success("Build completed successfully!")
        print_success("Installer created in 'dist' folder.")
        print("=" * 50 + "\n")
        
    except Exception as e:
        print_error(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    try:
        # Enable ANSI color codes for Windows
        os.system('')
        
        # Start export process
        export_windows() # Changed from export_installer()
        
        # Wait for user input
        input("\nPress Enter to exit...")
        
    except KeyboardInterrupt:
        print_info("\n\nOperation cancelled.")
    except Exception as e:
        print_error(f"\nAn unexpected error occurred: {str(e)}")
    finally:
        # Cleanup
        for file in ['main.spec', 'uninstall.spec']:
            if os.path.exists(file):
                try:
                    os.remove(file)
                except:
                    pass