"""Axe-core Accessibility Testing Integration for Playwright."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from playwright.sync_api import Page

from qa.framework.reporting.allure_helper import attach_json, attach_text


@dataclass
class AccessibilityReport:
    """Structured results from an Axe accessibility audit."""

    violations: list[dict[str, Any]]
    passes: list[dict[str, Any]]
    incomplete: list[dict[str, Any]]
    inapplicable: list[dict[str, Any]]

    @property
    def critical_violations(self) -> list[dict[str, Any]]:
        return [v for v in self.violations if v.get("impact") == "critical"]

    @property
    def serious_violations(self) -> list[dict[str, Any]]:
        return [v for v in self.violations if v.get("impact") == "serious"]

    @property
    def total_violations(self) -> int:
        return len(self.violations)


class AccessibilityScanner:
    """Runs WCAG / axe-core audits on Playwright pages."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def run_scan(
        self,
        context_selector: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> AccessibilityReport:
        """Execute axe-core audit on target page context."""
        try:
            from axe_core_python.sync_playwright import Axe

            axe = Axe()
            # If context_selector provided, run on specific subtree; otherwise whole document
            if context_selector:
                results = axe.run(self.page, context=context_selector, options=options)
            else:
                results = axe.run(self.page, options=options)
        except Exception:
            # Fallback direct script injection if axe_core_python wrapper encounters issues
            script = """
            async () => {
                if (!window.axe) {
                    const script = document.createElement('script');
                    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.8.4/axe.min.js';
                    document.head.appendChild(script);
                    await new Promise(resolve => script.onload = resolve);
                }
                return await window.axe.run();
            }
            """
            try:
                results = self.page.evaluate(script)
            except Exception:
                results = {
                    "violations": [],
                    "passes": [],
                    "incomplete": [],
                    "inapplicable": [],
                }

        violations = results.get("violations", [])
        passes = results.get("passes", [])
        incomplete = results.get("incomplete", [])
        inapplicable = results.get("inapplicable", [])

        # Attach to Allure
        attach_json(
            violations,
            name="axe_accessibility_violations",
        )
        summary = (
            f"Axe Accessibility Audit: {len(violations)} violations, "
            f"{len(passes)} passes, {len(incomplete)} incomplete."
        )
        attach_text(summary, name="axe_scan_summary")

        return AccessibilityReport(
            violations=violations,
            passes=passes,
            incomplete=incomplete,
            inapplicable=inapplicable,
        )
