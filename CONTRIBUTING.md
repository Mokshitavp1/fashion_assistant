# Contributing

Thanks for helping improve Fashion App.

## Before You Start

1. Read the main [README.md](README.md) and the backend notes in [backend/README.md](backend/README.md).
2. Make sure your local environment is configured in `backend/.env`.
3. Avoid committing secrets, uploaded images, or generated database files.

## Local Workflow

1. Install dependencies.

   ```bash
   pip install -r requirements.txt
   cd frontend
   npm install
   ```

2. Run the backend and frontend locally.

   ```bash
   npm run backend:dev
   cd frontend
   npm run dev
   ```

3. Validate your changes before opening a pull request.

   ```bash
   ./scripts/run_tests.sh
   cd frontend
   npm run lint
   npm run build
   ```

   On Windows PowerShell, use `powershell -File .\scripts\run_tests.ps1`.

## Code Style

- Keep changes focused and minimal.
- Prefer small, readable functions with comments only where the control flow or scoring logic is not obvious.
- Match the existing style in the file you are editing.
- Use ASCII unless the file already includes other characters.

## Commits

- Use short, descriptive commit messages.
- Group unrelated changes into separate commits when possible.
- Reference the area you changed, for example `docs: rewrite README` or `backend: clarify scoring logic`.

## Pull Requests

- Summarize the user-facing change.
- List validation commands you ran.
- Include screenshots or GIF updates when the UI changes.
- Mention any environment variables or setup steps that changed.
