"""
GitHub Data Fetcher for Tiki products.
Fetches Excel files from GitHub repository and processes them.
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()


class GitHubDataFetcher:
    """Fetch Tiki data from GitHub repository."""
    
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.repo_owner = os.getenv("GITHUB_REPO_OWNER", "exorcisthb")
        self.repo_name = os.getenv("GITHUB_REPO_NAME", "DSSupdate")
        self.branch = os.getenv("GITHUB_BRANCH", "main")
        self.data_path = os.getenv("GITHUB_DATA_PATH", "data")
        
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        
        self.base_api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"
    
    def list_files_in_directory(self, path: str = "") -> List[Dict]:
        """
        List all files in a GitHub directory.
        
        Args:
            path: Directory path within the repository
            
        Returns:
            List of file metadata dictionaries
        """
        actual_path = f"{self.data_path}/{path}" if path else self.data_path
        url = f"{self.base_api_url}/contents/{actual_path}?ref={self.branch}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            files = response.json()
            if not isinstance(files, list):
                files = [files]
            
            return [f for f in files if f['type'] == 'file']
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Error listing files from GitHub: {e}")
            return []
    
    def get_file_content(self, file_path: str) -> Optional[bytes]:
        """
        Download file content from GitHub.
        
        Args:
            file_path: Full path to file in repository
            
        Returns:
            File content as bytes
        """
        # Use raw.githubusercontent.com for direct file download
        raw_url = f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/{self.branch}/{file_path}"
        
        try:
            response = requests.get(raw_url, headers=self.headers, timeout=60)
            response.raise_for_status()
            return response.content
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Error downloading file {file_path}: {e}")
            return None
    
    def find_latest_tiki_files(self, days_back: int = 7) -> Dict[str, Dict]:
        """
        Find latest Tiki data files (clean, historical, changes).
        
        Args:
            days_back: Number of days to look back for files
            
        Returns:
            Dictionary with file types and their metadata
        """
        files = self.list_files_in_directory()
        
        if not files:
            print("⚠️  No files found in GitHub repository data directory")
            return {}
        
        # Expected file patterns
        patterns = {
            'clean': 'tiki_clean_data',
            'historical': 'tiki_historical_data',
            'changes': 'tiki_changes_report'
        }
        
        result = {}
        
        for file_type, pattern in patterns.items():
            matching_files = [
                f for f in files 
                if pattern in f['name'].lower() and f['name'].endswith('.xlsx')
            ]
            
            if matching_files:
                # Sort by name (assuming date in filename) and get most recent
                matching_files.sort(key=lambda x: x['name'], reverse=True)
                latest = matching_files[0]
                
                result[file_type] = {
                    'name': latest['name'],
                    'path': latest['path'],
                    'download_url': latest.get('download_url'),
                    'size': latest['size'],
                    'sha': latest['sha']
                }
                
                print(f"✅ Found {file_type} file: {latest['name']}")
        
        return result
    
    def download_and_parse_excel(self, file_path: str) -> Optional[pd.DataFrame]:
        """
        Download Excel file from GitHub and parse to DataFrame.
        
        Args:
            file_path: Path to Excel file in repository
            
        Returns:
            Parsed DataFrame or None
        """
        print(f"📥 Downloading {file_path}...")
        
        content = self.get_file_content(file_path)
        if content is None:
            return None
        
        try:
            df = pd.read_excel(BytesIO(content))
            print(f"✅ Parsed {len(df)} rows from {file_path}")
            return df
        
        except Exception as e:
            print(f"❌ Error parsing Excel file: {e}")
            return None
    
    def fetch_latest_data(self) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """
        Fetch latest Tiki data files from GitHub.
        
        Returns:
            Tuple of (clean_df, historical_df, changes_df)
        """
        print("🔍 Searching for latest Tiki data files on GitHub...")
        
        latest_files = self.find_latest_tiki_files()
        
        if not latest_files:
            print("❌ No Tiki data files found in GitHub repository")
            return None, None, None
        
        clean_df = None
        historical_df = None
        changes_df = None
        
        if 'clean' in latest_files:
            clean_df = self.download_and_parse_excel(latest_files['clean']['path'])
        
        if 'historical' in latest_files:
            historical_df = self.download_and_parse_excel(latest_files['historical']['path'])
        
        if 'changes' in latest_files:
            changes_df = self.download_and_parse_excel(latest_files['changes']['path'])
        
        return clean_df, historical_df, changes_df
    
    def get_latest_commit_info(self, file_path: str = "") -> Optional[Dict]:
        """
        Get latest commit information for a path.
        
        Args:
            file_path: Path to check commits for
            
        Returns:
            Commit metadata dictionary
        """
        path_param = f"&path={file_path}" if file_path else ""
        url = f"{self.base_api_url}/commits?sha={self.branch}{path_param}&per_page=1"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            commits = response.json()
            if commits:
                return {
                    'sha': commits[0]['sha'],
                    'date': commits[0]['commit']['committer']['date'],
                    'message': commits[0]['commit']['message']
                }
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching commit info: {e}")
        
        return None


if __name__ == "__main__":
    # Test the fetcher
    fetcher = GitHubDataFetcher()
    
    print(f"📂 Repository: {fetcher.repo_owner}/{fetcher.repo_name}")
    print(f"🌿 Branch: {fetcher.branch}")
    print(f"📁 Data path: {fetcher.data_path}")
    print()
    
    clean_df, historical_df, changes_df = fetcher.fetch_latest_data()
    
    if clean_df is not None:
        print(f"\n✅ Clean data: {len(clean_df)} products")
    if historical_df is not None:
        print(f"✅ Historical data: {len(historical_df)} records")
    if changes_df is not None:
        print(f"✅ Changes data: {len(changes_df)} changes")
