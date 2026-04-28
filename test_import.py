"""Import smoke checks for core project modules.

This file doubles as:
1. a lightweight unittest module collected by Django's test runner; and
2. a standalone script that can be run manually with `python test_import.py`.
"""

from __future__ import annotations

import importlib
import os
import sys
import unittest

import django
from django.apps import apps as django_apps


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")

if not django_apps.ready:
    django.setup()


class ImportSmokeTests(unittest.TestCase):
    """Basic import checks for frequently used project modules."""

    def test_import_core_modules(self) -> None:
        module_names = [
            "apps.accounts.models",
            "apps.accounts.forms",
            "apps.blog.models",
            "apps.blog.forms",
            "apps.forum.models",
            "apps.api.serializers",
            "moderation.services",
        ]

        for module_name in module_names:
            with self.subTest(module=module_name):
                module = importlib.import_module(module_name)
                self.assertIsNotNone(module)


def main() -> int:
    """Run the smoke test suite as a standalone script."""
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ImportSmokeTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
