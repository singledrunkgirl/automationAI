import os, subprocess, requests

def search_and_install(query):
    print(f"Searching GitHub for: {query}...")
    # Basic logic to found and clone
    api_url = f"https://api.github.com/search/repositories?q={query}+language:python&sort=stars"
    try:
        r = requests.get(api_url).json()
        if r['items']:
            clone_url = r['items'][0]['clone_url']
            name = r['items'][0]['name']
            dest = f"/home/kali/HackWithAI/tools/{name}"
            subprocess.run(["git", "clone", clone_url, dest])
            return f"Installed {name} at {dest}"
    except:
        return "Search failed or no tool found"
