"""
Test script to verify GitHub connection and list available files.
"""

from data_fetcher.github_fetcher import GitHubDataFetcher
from dotenv import load_dotenv
import os

load_dotenv()

def main():
    print("=" * 60)
    print("🧪 GitHub Connection Test")
    print("=" * 60)
    print()
    
    # Check environment variables
    print("📌 Configuration:")
    print(f"   Repo: {os.getenv('GITHUB_REPO_OWNER', 'exorcisthb')}/{os.getenv('GITHUB_REPO_NAME', 'DSSupdate')}")
    print(f"   Branch: {os.getenv('GITHUB_BRANCH', 'main')}")
    print(f"   Data Path: {os.getenv('GITHUB_DATA_PATH', 'data')}")
    print(f"   Token Set: {'Yes ✅' if os.getenv('GITHUB_TOKEN') else 'No ❌ (will use rate-limited anonymous access)'}")
    print()
    
    # Initialize fetcher
    fetcher = GitHubDataFetcher()
    
    # Test 1: List files in data directory
    print("🔍 Test 1: Listing files in data directory...")
    files = fetcher.list_files_in_directory()
    
    if files:
        print(f"✅ Found {len(files)} files:")
        for file in files[:10]:  # Show first 10
            print(f"   📄 {file['name']} ({file['size']:,} bytes)")
        if len(files) > 10:
            print(f"   ... and {len(files) - 10} more")
    else:
        print("❌ No files found or error accessing repository")
        return
    
    print()
    
    # Test 2: Find latest Tiki files
    print("🔍 Test 2: Finding latest Tiki data files...")
    latest_files = fetcher.find_latest_tiki_files()
    
    if latest_files:
        print(f"✅ Found {len(latest_files)} Tiki file types:")
        for file_type, file_info in latest_files.items():
            print(f"   📊 {file_type}: {file_info['name']}")
    else:
        print("❌ No Tiki files found matching patterns")
        return
    
    print()
    
    # Test 3: Get commit info
    print("🔍 Test 3: Getting latest commit info...")
    commit_info = fetcher.get_latest_commit_info(fetcher.data_path)
    
    if commit_info:
        print(f"✅ Latest commit:")
        print(f"   SHA: {commit_info['sha'][:8]}")
        print(f"   Date: {commit_info['date']}")
        print(f"   Message: {commit_info['message']}")
    else:
        print("❌ Could not fetch commit info")
    
    print()
    
    # Test 4: Download a sample file (just metadata, not full download)
    print("🔍 Test 4: Testing file download capability...")
    if 'clean' in latest_files:
        test_path = latest_files['clean']['path']
        print(f"   Testing with: {latest_files['clean']['name']}")
        
        content = fetcher.get_file_content(test_path)
        if content:
            print(f"✅ Successfully downloaded {len(content):,} bytes")
        else:
            print("❌ Failed to download file")
    
    print()
    print("=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
