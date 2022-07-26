# Copyright (c) 2018 Lokster <http://lokspace.eu>
# Based on the SupportBlocker plugin by Ultimaker B.V., and licensed under LGPLv3 or higher.

IS_QT5 = False
try:
    import PyQt6.QtCore
except ImportError:
    IS_QT5 = True

from . import CustomSupports

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "tool": {
            "name": i18n_catalog.i18nc("@label", "Custom Supports"),
            "description": i18n_catalog.i18nc("@info:tooltip", "Add custom supports"),
            "icon": "tool_icon.svg",
            "tool_panel": "CustomSupportsQt5.qml" if IS_QT5 else "CustomSupportsQt6.qml",
            "weight": 4
        }
    }

def register(app):
    return { "tool": CustomSupports.CustomSupports() }
