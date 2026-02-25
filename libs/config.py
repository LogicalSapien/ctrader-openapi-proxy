import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))

CTRADER_TOKEN         = os.getenv('CTRADER_TOKEN', '')
CTRADER_CLIENT_ID     = os.getenv('CTRADER_CLIENT_ID', '')
CTRADER_CLIENT_SECRET = os.getenv('CTRADER_CLIENT_SECRET', '')
CTRADER_ACCOUNTID     = os.getenv('CTRADER_ACCOUNTID', '')
CTRADER_HOST          = os.getenv('CTRADER_HOST', 'demo')  # "demo" or "live"

CONSOLE_LOG_LEVEL = os.getenv('CONSOLE_LOG_LEVEL', 'INFO')
