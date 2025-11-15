#!/usr/bin/env python3
"""
O3DE (Open 3D Engine) Setup Automation Script
Automates the installation and project setup process for O3DE on Windows
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
    
    def clone_repo(self):
        """Clone O3DE repository if it doesn't exist"""
        if self.o3de_source.exists():
            print(f"\n✓ O3DE source already exists at {self.o3de_source}")
            return True
        
        print("\n" + "=" * 60)
        print("Cloning O3DE Repository...")
        print("=" * 60)
        print("This may take a while due to large files...")
        
        try:
            subprocess.run([
                'git', 'clone', 
                'https://github.com/o3de/o3de.git',
                str(self.o3de_source)
            ], check=True)
            print("✓ Repository cloned successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to clone repository: {e}")
            return False
    
    def create_packages_dir(self):
        """Create 3rd party packages directory"""
        if not self.packages_path.exists():
            print(f"\nCreating packages directory: {self.packages_path}")
            self.packages_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Packages directory ready: {self.packages_path}")
    
    def configure_engine(self):
        """Configure the engine with CMake"""
        print("\n" + "=" * 60)
        print("Configuring Engine with CMake...")
        print("=" * 60)
        print("This will download and configure third-party dependencies...")
        
        self.build_path.mkdir(parents=True, exist_ok=True)
        
        cmake_cmd = [
            'cmake',
            '-B', str(self.build_path),
            '-S', str(self.o3de_source),
            '-G', 'Visual Studio 16',
            f'-DLY_3RDPARTY_PATH={self.packages_path}'
        ]
        
        print(f"\nRunning: {' '.join(cmake_cmd)}\n")
        
        try:
            subprocess.run(cmake_cmd, check=True)
            print("\n✓ Engine configured successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"\n✗ CMake configuration failed: {e}")
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
        print("Building Project (This will take a while)...")
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
        print("Go grab a coffee, this will take 30+ minutes...\n")
        
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
        print("║" + " " * 10 + "O3DE Setup Automation Script" + " " * 20 + "║")
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
        
        # Execute setup steps
        steps = [
            ("Clone Repository", self.clone_repo),
            ("Create Packages Directory", self.create_packages_dir),
            ("Configure Engine", self.configure_engine),
            ("Register Engine", self.register_engine),
            ("Create Project", self.create_project),
            ("Configure Project", self.configure_project),
        ]
        
        for step_name, step_func in steps:
            if not step_func():
                print(f"\n✗✗✗ Setup failed at step: {step_name} ✗✗✗")
                return False
        
        # Ask about building
        print("\n" + "=" * 60)
        build = input("Build the project now? (This takes 30+ minutes) (y/n): ").strip().lower()
        if build == 'y':
            self.build_project()
        else:
            print("\nSkipping build. You can build later with:")
            project_build = self.project_path / "build" / "windows"
            print(f"cmake --build {project_build} --target {self.project_name}.GameLauncher Editor --config profile -- /m")
        
        print("\n" + "╔" + "═" * 58 + "╗")
        print("║" + " " * 15 + "Setup Complete!" + " " * 26 + "║")
        print("╚" + "═" * 58 + "╝")
        print(f"\nYour O3DE project is ready at: {self.project_path}")
        return True

if __name__ == "__main__":
    setup = O3DESetup()
    success = setup.run()
    sys.exit(0 if success else 1)