from app import app

if __name__ == "__main__":
    # Run on all network interfaces so students can connect from other devices
    app.run(debug=True, host='0.0.0.0', port=5000) 