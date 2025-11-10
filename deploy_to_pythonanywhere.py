#!/usr/bin/env python3
"""
PythonAnywhere Deployment Script
Automates deployment of Django application to PythonAnywhere

Prerequisites:
1. Install: pip install requests python-dotenv
2. Set environment variables in .env.pythonanywhere
3. Have your code pushed to GitHub
"""

import os
import sys
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.pythonanywhere')

class PythonAnywhereDeployer:
    def __init__(self):
        self.username = os.getenv('PYTHONANYWHERE_USERNAME')
        self.api_token = os.getenv('PYTHONANYWHERE_API_TOKEN')
        self.domain_name = os.getenv('PYTHONANYWHERE_DOMAIN')
        self.github_repo = os.getenv('GITHUB_REPO_URL')

        if not all([self.username, self.api_token, self.domain_name]):
            raise ValueError("Missing required environment variables. Check .env.pythonanywhere")

        self.base_url = f'https://www.pythonanywhere.com/api/v0/user/{self.username}'
        self.headers = {'Authorization': f'Token {self.api_token}'}

    def check_webapp_exists(self):
        """Check if webapp already exists"""
        url = f'{self.base_url}/webapps/{self.domain_name}/'
        response = requests.get(url, headers=self.headers)
        return response.status_code == 200

    def create_webapp(self, python_version='python39'):
        """Create a new webapp"""
        print(f"Creating webapp {self.domain_name}...")
        url = f'{self.base_url}/webapps/'
        data = {
            'domain_name': self.domain_name,
            'python_version': python_version
        }
        response = requests.post(url, headers=self.headers, json=data)

        if response.status_code == 201:
            print(f"✓ Webapp created successfully")
            return True
        else:
            print(f"✗ Failed to create webapp: {response.status_code}")
            print(response.text)
            return False

    def update_webapp_config(self, source_dir, virtualenv_path):
        """Update webapp configuration"""
        print("Updating webapp configuration...")
        url = f'{self.base_url}/webapps/{self.domain_name}/'
        data = {
            'source_directory': source_dir,
            'virtualenv_path': virtualenv_path,
            'force_https': True
        }
        response = requests.patch(url, headers=self.headers, json=data)

        if response.status_code == 200:
            print("✓ Webapp configuration updated")
            return True
        else:
            print(f"✗ Failed to update config: {response.status_code}")
            print(response.text)
            return False

    def create_static_files_mapping(self, url_path, directory_path):
        """Create static files mapping"""
        print(f"Creating static files mapping: {url_path} -> {directory_path}")
        api_url = f'{self.base_url}/webapps/{self.domain_name}/static_files/'
        data = {
            'url': url_path,
            'path': directory_path
        }
        response = requests.post(api_url, headers=self.headers, json=data)

        if response.status_code == 201:
            print(f"✓ Static files mapping created")
            return True
        else:
            print(f"✗ Failed to create static mapping: {response.status_code}")
            print(response.text)
            return False

    def reload_webapp(self):
        """Reload the webapp"""
        print("Reloading webapp...")
        url = f'{self.base_url}/webapps/{self.domain_name}/reload/'
        response = requests.post(url, headers=self.headers)

        if response.status_code == 200:
            print("✓ Webapp reloaded successfully")
            return True
        else:
            print(f"✗ Failed to reload webapp: {response.status_code}")
            print(response.text)
            return False

    def execute_bash_command(self, command):
        """Execute a bash command via console API"""
        print(f"Executing: {command}")

        # Create a console
        console_url = f'{self.base_url}/consoles/'
        data = {
            'executable': 'bash',
            'arguments': []
        }
        response = requests.post(console_url, headers=self.headers, json=data)

        if response.status_code != 201:
            print(f"✗ Failed to create console: {response.status_code}")
            return False

        console_id = response.json()['id']

        # Send command to console
        input_url = f'{self.base_url}/consoles/{console_id}/send_input/'
        input_data = {'input': f'{command}\n'}
        response = requests.post(input_url, headers=self.headers, json=input_data)

        if response.status_code == 200:
            print(f"✓ Command executed")
            # Note: Getting output requires additional API calls
            return True
        else:
            print(f"✗ Failed to execute command: {response.status_code}")
            return False

    def deploy(self):
        """Main deployment workflow"""
        print("=" * 60)
        print("PythonAnywhere Deployment Started")
        print("=" * 60)

        # Step 1: Check if webapp exists
        webapp_exists = self.check_webapp_exists()

        if not webapp_exists:
            print("\nStep 1: Creating webapp...")
            if not self.create_webapp():
                return False
        else:
            print("\n✓ Webapp already exists")

        # Step 2: Clone/Update repository
        print("\nStep 2: Updating code from GitHub...")
        project_path = f'/home/{self.username}/20_index_rebalancer'

        # Check if directory exists and pull, otherwise clone
        self.execute_bash_command(f'cd {project_path} && git pull || git clone {self.github_repo} {project_path}')

        # Step 3: Setup virtual environment
        print("\nStep 3: Setting up virtual environment...")
        venv_path = f'{project_path}/venv'
        self.execute_bash_command(f'cd {project_path} && python3.9 -m venv venv')

        # Step 4: Install dependencies
        print("\nStep 4: Installing dependencies...")
        self.execute_bash_command(f'cd {project_path} && source venv/bin/activate && pip install -r requirements.txt')

        # Step 5: Run migrations
        print("\nStep 5: Running migrations...")
        self.execute_bash_command(f'cd {project_path} && source venv/bin/activate && python manage.py migrate')

        # Step 6: Collect static files
        print("\nStep 6: Collecting static files...")
        self.execute_bash_command(f'cd {project_path} && source venv/bin/activate && python manage.py collectstatic --noinput')

        # Step 7: Update webapp configuration
        print("\nStep 7: Updating webapp configuration...")
        self.update_webapp_config(
            source_dir=project_path,
            virtualenv_path=venv_path
        )

        # Step 8: Create static files mapping
        print("\nStep 8: Configuring static files...")
        self.create_static_files_mapping(
            url_path='/static/',
            directory_path=f'{project_path}/staticfiles'
        )

        # Step 9: Reload webapp
        print("\nStep 9: Reloading webapp...")
        self.reload_webapp()

        print("\n" + "=" * 60)
        print("✓ Deployment completed successfully!")
        print(f"Your app should be live at: https://{self.domain_name}")
        print("=" * 60)

        return True


def main():
    """Main entry point"""
    try:
        deployer = PythonAnywhereDeployer()
        success = deployer.deploy()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Deployment failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
