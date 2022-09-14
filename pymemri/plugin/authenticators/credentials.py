from ...data.basic import HOME_DIR, read_json

PLUGIN_DIR = HOME_DIR / ".pymemri" / "plugins"


def read_username_password(plugin: str):
    credentials_path = PLUGIN_DIR / plugin / "credentials.json"
    credentials = read_json(credentials_path)
    username, password = credentials["username"], credentials["password"]
    return username, password
