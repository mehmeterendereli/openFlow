# Autonomous Execution & Handoff Protocol
You are operating in a fully autonomous loop. Follow these strict rules:
1. **The Handoff:** When you finish a distinct logical phase (e.g., Frontend UI is done), you MUST:
   - Run `git add .` and `git commit -m "feat: completed [Phase Name]"`
   - Update `todo.md` with checkmarks [x].
   - Explicitly output: "[HANDOFF] Transitioning to next phase..." and IMMEDIATELY start writing code for the next phase.
2. **Zero-Block Policy:** If a specific AI model library fails to install, mock its output temporarily so the end-to-end pipeline doesn't break, document it, and continue building the pipeline.
3. **Git Rules:** Initialize the repo. Commit after every major component.
