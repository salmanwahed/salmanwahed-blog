Run ruff format and ruff check on the project's Python source files (excluding migrations and .venv).

Steps:
1. Run `ruff format salmanwahed_com/` to auto-format all Python files
2. Run `ruff check salmanwahed_com/ --fix` to auto-fix safe lint issues
3. Run `ruff check salmanwahed_com/` to report any remaining issues that need manual attention
4. Report a summary: how many files were reformatted, how many issues were auto-fixed, and any remaining violations

Use the Bash tool for each command, running from the repo root `C:\Users\Salman\PycharmProjects\salmanwahed-blog`.
If ruff is not found, tell the user to install it: `pip install -r requirements-dev.txt`
