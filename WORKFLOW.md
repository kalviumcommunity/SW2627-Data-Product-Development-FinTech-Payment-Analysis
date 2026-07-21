# GitHub Workflow

## Branching Strategy

- The main branch always contains stable and releasable code.
- Every new feature is developed in its own feature branch.
- Branch naming convention:
  - feature/<feature-name>
  - fix/<bug-name>
  - docs/<documentation>
  - refactor/<module>
  - chore/<task>
- Feature branches are deleted after merging.

---

## Commit Message Convention

Format

[type]: description

Types

- feat
- fix
- docs
- refactor
- chore

Examples

feat: add payment retry analytics

docs: update README

chore: organize project folders

---

## Pull Request Process

- Create a feature branch.
- Push commits.
- Open a Pull Request.
- Link related GitHub Issues.
- Review changes.
- Merge after approval.

---

## Code Review Checklist

- Code correctness
- Readability
- Data integrity
- Performance
- Documentation
- Testing

---

## Issue Tracking

Every new feature begins with a GitHub Issue.

Each issue includes:
- Title
- Description
- Label
- Assignee

Issues are closed automatically after merging the related Pull Request.