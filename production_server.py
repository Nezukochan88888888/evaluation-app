from app import app
from waitress import serve

if __name__ == '__main__':
    print('=============================================')
    print('?? STARTING PRODUCTION SERVER (Waitress)')
    print('?? Capacity: Configured for 45-60 Students')
    print('?? Listening on: http://0.0.0.0:5000')
    print('? Press Ctrl+C to stop')
    print('=============================================')
    
    # threads=6 ensures enough concurrency for your class size
    serve(app, host='0.0.0.0', port=5000, threads=6)
