"""Backward-compatible entry point for the renamed colour profile validator."""

from validate_color_profiles import main


if __name__ == "__main__":
    raise SystemExit(main())
