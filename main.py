from app import app
from waitress import serve

if __name__ == "__main__":
    print('=============================================')
    print('🚀 STARTING PRODUCTION SERVER (Waitress)')
    print('👥 Capacity: Configured for 60+ Students')
    print('🌐 Listening on: http://0.0.0.0:5000')
    print('🔒 Security: Enhanced anti-cheating measures')
    print('⏹️ Press Ctrl+C to stop')
    print('=============================================')
    
    # Use Waitress production server instead of Flask dev server
    # threads=64 ensures enough concurrency for 60 students (1 thread per active request)
    serve(app, host='0.0.0.0', port=5000, threads=64) 