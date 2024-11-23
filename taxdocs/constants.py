from decouple import config

USE_LIVE_SHEET = config("TAXDOCS_USE_LIVE_SHEET", cast=bool, default=False)
DEBUG_EXTRACTION = config("TAXDOCS_DEBUG_EXTRACTION", cast=bool, default=False)

PDF_TO_IMAGE_DPI = 200
