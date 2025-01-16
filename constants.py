from dotenv import load_dotenv
from os import getenv

load_dotenv(override=True)

OPEN_API_KEY = getenv('OPEN_API_KEY')