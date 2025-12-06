import os
import urllib.request

def download_assets():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(base_dir, 'app', 'static')
    css_dir = os.path.join(static_dir, 'css')
    js_dir = os.path.join(static_dir, 'js')

    # Create directories if they don't exist
    for directory in [css_dir, js_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

    assets = {
        'https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css': os.path.join(css_dir, 'bootstrap.min.css'),
        'https://code.jquery.com/jquery-3.2.1.slim.min.js': os.path.join(js_dir, 'jquery.min.js'),
        'https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.12.9/umd/popper.min.js': os.path.join(js_dir, 'popper.min.js'),
        'https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js': os.path.join(js_dir, 'bootstrap.min.js')
    }

    print("Downloading assets...")
    for url, filepath in assets.items():
        try:
            print(f"Downloading {url} to {filepath}...")
            urllib.request.urlretrieve(url, filepath)
            print(f"Successfully downloaded {os.path.basename(filepath)}")
        except Exception as e:
            print(f"Failed to download {url}: {e}")

    print("Asset download complete.")

if __name__ == "__main__":
    download_assets()
