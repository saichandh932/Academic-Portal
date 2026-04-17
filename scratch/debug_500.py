import requests

def debug():
    url = "http://127.0.0.1:5000/api/db/students/231FA04029/history"
    r = requests.get(url)
    print(f"STATUS: {r.status_code}")
    print("CONTENT:")
    print(r.text)

if __name__ == "__main__":
    debug()
