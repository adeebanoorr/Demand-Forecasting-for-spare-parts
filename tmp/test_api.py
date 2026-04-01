import sys
from pathlib import Path
project_root = Path(r"d:\KPCL_SparePartConsumption_Project\kpcl_selected_item_forecasting")
sys.path.append(str(project_root))

from backend.api.settings import settings
from backend.api.routers.items import get_items

print(f"BASE_DIR: {settings.BASE_DIR}")
try:
    items = get_items()
    print(f"Items found: {items}")
except Exception as e:
    print(f"Error: {e}")
