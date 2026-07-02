import requests

print("Checking GitHub repo structure...")
r = requests.get('https://api.github.com/repos/exorcisthb/DSSupdate/contents')

if r.status_code == 200:
    items = r.json()
    print(f"\nFound {len(items)} items in root:\n")
    for item in items:
        print(f"  {item['type']:10s} {item['name']}")
else:
    print(f"Error: {r.status_code}")
