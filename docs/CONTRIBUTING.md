# Contributing to ContextKeeper

First off, thank you for considering contributing to ContextKeeper! It's people like you that make this development context awareness system better for everyone.

**ContextKeeper** is developed by [LostMindAI](https://github.com/lostmind008) as an open-source project, and we welcome contributions from the community.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- Use a clear and descriptive title
- Describe the exact steps to reproduce the problem
- Provide specific examples
- Describe the behavior you observed and what you expected
- Include logs if relevant

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- Use a clear and descriptive title
- Provide a step-by-step description of the suggested enhancement
- Provide specific examples to demonstrate the steps
- Describe the current behavior and explain why the enhancement would be useful

### Pull Requests

1. Fork the repo and create your branch from `master`
2. If you've added code that should be tested, add tests
3. Ensure your code follows the existing style
4. Make sure your code passes all tests
5. Issue that pull request!

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment: `python3 -m venv venv`
3. Activate it: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up your `.env` file with Google Cloud credentials

## Code Style and Quality

We use `pre-commit` hooks to enforce code style and quality automatically. This helps us maintain a clean and consistent codebase.

### Activating Pre-Commit Hooks

To get started, you need to install `pre-commit` and set up the hooks in your local repository. This only needs to be done once.

1.  **Install pre-commit:**
    ```bash
    pip install pre-commit
    ```

2.  **Install the hooks:**
    ```bash
    pre-commit install
    ```

Now, every time you run `git commit`, the hooks will automatically check your changes for issues like formatting, trailing whitespace, and syntax errors. If any issues are found, the commit will be aborted, allowing you to fix them before committing again.

### Style Guidelines

- **Python:** We follow `black` for formatting and `flake8` for linting.
- **YAML:** Basic syntax checking is enforced.
- Follow PEP 8 for Python code where not covered by `black`.
- Use meaningful variable and function names.
- Add comments for complex logic.
- Keep functions focused and small.

## Questions?

Feel free to open an issue with your question or reach out to the maintainer.

Thank you! 🚀