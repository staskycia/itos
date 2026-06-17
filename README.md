# ITOS
Digital school announcments system

## Development
- create and activate virtual enviornment `python3 -m venv venv && source venv/bin/activate`
- install required packages `pip install -r requirements.txt`
- reload the enviornment `deactivate && source venv/bin/activate`
- create enviornmental configuration (`cp sample.env .env`) and adjust values as needed
- create uploads folder `mkdir app/uploads`
- initialize the app and create admin account `python init_db.py`
- run the development server `flask run --debug`
