#!/usr/bin/env python3
"""
O3DE (Open 3D Engine) Setup Automation Script - Clean Install Version
Nukes existing installations and does a fresh Git clone setup
"""

import subprocess
import sys
import os
from pathlib import Path
import shutil

class O3DESetup:
    def __init__(self):
        self.o3de_source = None
        self.build_path = None
        self.packages_path = None
        self.project_path = None
        self.project_name = None
        
    def check_prerequisites(self):
        """Check if required tools are installed"""
        print("=" * 60)
        print("Checking Prerequisites...")
        print("=" * 60)
        
        # Check Git
        try:
            result = subprocess.run(['git', '--version'], capture_output=True, text=True)
            print(f"✓ Git found: {result.stdout.strip()}")
        except FileNotFoundError:
            print("✗ Git not found! Please install Git first.")
            return False
        
        # Check Git LFS
        try:
            result = subprocess.run(['git', 'lfs', '--version'], capture_output=True, text=True)
            print(f"✓ Git LFS found: {result.stdout.strip()}")
        except:
            print("✗ Git LFS not found! Installing Git LFS hooks...")
            try:
                subprocess.run(['git', 'lfs', 'install'], check=True)
                print("✓ Git LFS installed")
            except:
                print("✗ Failed to install Git LFS. Please install manually from https://git-lfs.github.com/")
                return False
        
        # Check CMake
        try:
            result = subprocess.run(['cmake', '--version'], capture_output=True, text=True)
            version_line = result.stdout.split('\n')[0]
            print(f"✓ CMake found: {version_line}")
        except FileNotFoundError:
            print("✗ CMake not found! Please install CMake 3.24.0+ from https://cmake.org/download/")
            return False
        
        print("\n✓ All prerequisites met!\n")
        return True
    
    def get_user_paths(self):
        """Get paths from user"""
        print("=" * 60)
        print("Configuration Setup")
        print("=" * 60)
        
        # O3DE source path
        default_source = "C:\\o3de"
        source_input = input(f"O3DE source path [{default_source}]: ").strip()
        self.o3de_source = Path(source_input) if source_input else Path(default_source)
        
        # Build path
        default_build = self.o3de_source / "build" / "windows"
        build_input = input(f"Build path [{default_build}]: ").strip()
        self.build_path = Path(build_input) if build_input else default_build
        
        # 3rd party packages path
        default_packages = "C:\\o3de-packages"
        packages_input = input(f"3rd party packages path [{default_packages}]: ").strip()
        self.packages_path = Path(packages_input) if packages_input else Path(default_packages)
        
        # Project path
        default_project = "C:\\my-o3de-project"
        project_input = input(f"New project path [{default_project}]: ").strip()
        self.project_path = Path(project_input) if project_input else Path(default_project)
        self.project_name = self.project_path.name
        
        print("\n" + "=" * 60)
        print("Configuration Summary:")
        print("=" * 60)
        print(f"O3DE Source:     {self.o3de_source}")
        print(f"Build Path:      {self.build_path}")
        print(f"Packages Path:   {self.packages_path}")
        print(f"Project Path:    {self.project_path}")
        print(f"Project Name:    {self.project_name}")
        print("=" * 60)
        
        confirm = input("\nProceed with these settings? (y/n): ").strip().lower()
        return confirm == 'y'
    
    def nuke_existing_installations(self):
        """Clean up any existing O3DE installations"""
        print("\n" + "=" * 60)
        print("Cleaning Up Existing Installations...")
        print("=" * 60)
        
        paths_to_check = [
            self.o3de_source,
            Path("C:\\O3DE"),  # Common alternate location
            self.build_path,
        ]
        
        cleaned_something = False
        
        for path in paths_to_check:
            if path.exists():
                print(f"\n⚠ Found existing directory: {path}")
                confirm = input(f"  Delete this directory? (y/n): ").strip().lower()
                
                if confirm == 'y':
                    print(f"  Deleting {path}...")
                    try:
                        shutil.rmtree(path, ignore_errors=True)
                        print(f"  ✓ Deleted {path}")
                        cleaned_something = True
                    except Exception as e:
                        print(f"  ✗ Failed to delete {path}: {e}")
                        print(f"  Please manually delete this folder and try again.")
                        return False
                else:
                    print(f"  Skipping {path}")
        
        if not cleaned_something:
            print("\n✓ No existing installations found - clean slate!")
        else:
            print("\n✓ Cleanup complete!")
        
        return True
    
    def clone_repo(self):
        """Clone O3DE repository with Git LFS"""
        print("\n" + "=" * 60)
        print("Cloning O3DE Repository (Fresh Git Clone)...")
        print("=" * 60)
        print("This will take a while - O3DE is several GB...")
        print("Grab a coffee! ☕\n")
        
        if self.o3de_source.exists():
            print(f"⚠ Directory {self.o3de_source} still exists!")
            print("Please delete it manually or choose a different path.")
            return False
        
        # Create parent directory if needed
        self.o3de_source.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Clone the repo
            print(f"Cloning to {self.o3de_source}...")
            subprocess.run([
                'git', 'clone', 
                'https://github.com/o3de/o3de.git',
                str(self.o3de_source)
            ], check=True)
            
            print("\n✓ Repository cloned successfully!")
            
            # Setup Git LFS
            print("\nSetting up Git LFS...")
            subprocess.run(['git', 'lfs', 'install'], 
                         cwd=str(self.o3de_source), 
                         check=True)
            
            # Pull LFS files
            print("\nPulling Git LFS files (this will take a while)...")
            subprocess.run(['git', 'lfs', 'pull'], 
                         cwd=str(self.o3de_source), 
                         check=True)
            
            print("\n✓ Git LFS files downloaded!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"\n✗ Failed to clone repository: {e}")
            return False
    
    def verify_git_repo(self):
        """Verify that O3DE is a proper Git repository"""
        print("\n" + "=" * 60)
        print("Verifying Git Repository...")
        print("=" * 60)
        
        git_dir = self.o3de_source / ".git"
        cmake_file = self.o3de_source / "CMakeLists.txt"
        
        if not git_dir.exists():
            print(f"✗ {self.o3de_source} is not a Git repository!")
            print("  Missing .git folder")
            return False
        
        if not cmake_file.exists():
            print(f"✗ {self.o3de_source} is missing CMakeLists.txt!")
            print("  The repository may be incomplete")
            return False
        
        # Check if it's actually an O3DE repo
        try:
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'],
                                  cwd=str(self.o3de_source),
                                  capture_output=True,
                                  text=True,
                                  check=True)
            
            if 'o3de' in result.stdout.lower():
                print(f"✓ Valid O3DE Git repository")
                print(f"  Remote: {result.stdout.strip()}")
                return True
            else:
                print(f"✗ This doesn't appear to be an O3DE repository")
                print(f"  Remote: {result.stdout.strip()}")
                return False
                
        except subprocess.CalledProcessError:
            print("✗ Failed to verify Git remote")
            return False
    
    def create_packages_dir(self):
        """Create 3rd party packages directory"""
        if not self.packages_path.exists():
            print(f"\nCreating packages directory: {self.packages_path}")
            self.packages_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Packages directory ready: {self.packages_path}")
        return True
    
    def configure_engine(self):
        """Configure the engine with CMake"""
        print("\n" + "=" * 60)
        print("Configuring Engine with CMake...")
        print("=" * 60)
        print("This will download and configure third-party dependencies...")
        print("This takes 10-15 minutes...\n")
        
        self.build_path.mkdir(parents=True, exist_ok=True)
        
        cmake_cmd = [
            'cmake',
            '-B', str(self.build_path),
            '-S', str(self.o3de_source),
            '-G', 'Visual Studio 16',
            f'-DLY_3RDPARTY_PATH={self.packages_path}'
        ]
        
        print(f"Running: {' '.join(cmake_cmd)}\n")
        
        try:
            subprocess.run(cmake_cmd, check=True)
            print("\n✓ Engine configured successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"\n✗ CMake configuration failed: {e}")
            print("\nTroubleshooting tips:")
            print("  - Make sure Visual Studio 2019 is installed")
            print("  - Verify you have the 'Game Development with C++' workload")
            print("  - Try running this script as Administrator")
            return False
    
    def register_engine(self):
        """Register the engine"""
        print("\n" + "=" * 60)
        print("Registering Engine...")
        print("=" * 60)
        
        o3de_script = self.o3de_source / "scripts" / "o3de.bat"
        
        try:
            subprocess.run([
                str(o3de_script),
                'register',
                '--this-engine'
            ], cwd=str(self.o3de_source), check=True)
            print("✓ Engine registered successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to register engine: {e}")
            return False
    
    def create_project(self):
        """Create a new O3DE project"""
        print("\n" + "=" * 60)
        print("Creating New Project...")
        print("=" * 60)
        
        o3de_script = self.o3de_source / "scripts" / "o3de.bat"
        
        try:
            subprocess.run([
                str(o3de_script),
                'create-project',
                '--project-path', str(self.project_path)
            ], cwd=str(self.o3de_source), check=True)
            print(f"✓ Project created: {self.project_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to create project: {e}")
            return False
    
    def configure_project(self):
        """Configure the project with CMake"""
        print("\n" + "=" * 60)
        print("Configuring Project...")
        print("=" * 60)
        
        project_build = self.project_path / "build" / "windows"
        project_build.mkdir(parents=True, exist_ok=True)
        
        cmake_cmd = [
            'cmake',
            '-B', str(project_build),
            '-S', str(self.project_path),
            '-G', 'Visual Studio 16'
        ]
        
        print(f"\nRunning: {' '.join(cmake_cmd)}\n")
        
        try:
            subprocess.run(cmake_cmd, check=True)
            print("\n✓ Project configured successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"\n✗ Project configuration failed: {e}")
            return False
    
    def build_project(self):
        """Build the project"""
        print("\n" + "=" * 60)
        print("Building Project (This will take a LONG while)...")
        print("=" * 60)
        
        project_build = self.project_path / "build" / "windows"
        
        build_cmd = [
            'cmake',
            '--build', str(project_build),
            '--target', f'{self.project_name}.GameLauncher', 'Editor',
            '--config', 'profile',
            '--', '/m'
        ]
        
        print(f"\nRunning: {' '.join(build_cmd)}\n")
        print("⏰ Go grab lunch, this takes 30-60 minutes...\n")
        
        try:
            subprocess.run(build_cmd, check=True)
            print("\n✓ Project built successfully!")
            print(f"\nBinaries location: {project_build / 'bin' / 'profile'}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"\n✗ Build failed: {e}")
            return False
    
    def run(self):
        """Main execution flow"""
        print("\n")
        print("╔" + "═" * 58 + "╗")
        print("║" + " " * 8 + "O3DE Clean Install Automation Script" + " " * 13 + "║")
        print("╚" + "═" * 58 + "╝")
        print()
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("\n✗ Prerequisites not met. Please install missing tools and try again.")
            return False
        
        # Get user configuration
        if not self.get_user_paths():
            print("\n✗ Setup cancelled by user.")
            return False
        
        # Nuke existing installations
        if not self.nuke_existing_installations():
            print("\n✗ Failed to clean up existing installations.")
            return False
        
        # Execute setup steps
        steps = [
            ("Clone Repository (Git + LFS)", self.clone_repo),
            ("Verify Git Repository", self.verify_git_repo),
            ("Create Packages Directory", self.create_packages_dir),
            ("Configure Engine", self.configure_engine),
            ("Register Engine", self.register_engine),
            ("Create Project", self.create_project),
            ("Configure Project", self.configure_project),
        ]
        
        for i, (step_name, step_func) in enumerate(steps, 1):
            print(f"\n{'='*60}")
            print(f"[Step {i}/{len(steps)}] {step_name}")
            print(f"{'='*60}")
            try:
                if not step_func():
                    print(f"\n✗✗✗ Setup failed at step: {step_name} ✗✗✗")
                    print("Check the error messages above for details.")
                    return False
            except Exception as e:
                print(f"\n✗✗✗ Setup failed at step: {step_name} ✗✗✗")
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        # Ask about building
        print("\n" + "=" * 60)
        build = input("Build the project now? (This takes 30-60 minutes) (y/n): ").strip().lower()
        if build == 'y':
            self.build_project()
        else:
            print("\n⏭ Skipping build. You can build later with:")
            project_build = self.project_path / "build" / "windows"
            print(f"\ncmake --build {project_build} --target {self.project_name}.GameLauncher Editor --config profile -- /m\n")
        
        print("\n" + "╔" + "═" * 58 + "╗")
        print("║" + " " * 18 + "Setup Complete!" + " " * 23 + "║")
        print("╚" + "═" * 58 + "╝")
        print(f"\n✓ Your O3DE project is ready at: {self.project_path}")
        print(f"✓ O3DE engine is at: {self.o3de_source}")
        print("\nHappy game developing! 🎮\n")
        return True

if __name__ == "__main__":
    setup = O3DESetup()
    success = setup.run()
    sys.exit(0 if success else 1)
