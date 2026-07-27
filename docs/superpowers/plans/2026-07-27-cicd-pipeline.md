# GitHub Actions CI/CD Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a GitHub Actions CI/CD workflow (`.github/workflows/deploy.yml`) that automatically runs backend unit tests, frontend build checks, and deploys to Google Cloud Run via Workload Identity Federation on `git push main`.

**Architecture:** A two-job workflow (`test-and-lint` -> `deploy-production`). Keyless OIDC authentication to GCP using Workload Identity Federation (`github-pool`/`github-provider`).

**Tech Stack:** GitHub Actions, Google Cloud SDK, `google-github-actions/auth@v2`, Next.js 16, Python 3.11 / FastAPI.

## Global Constraints

- Workflow file must be located at `.github/workflows/deploy.yml`.
- Must trigger on `push` to `main` branch and `workflow_dispatch`.
- Must run backend unit tests: `python3 -m unittest discover -s backend/tests`.
- Must run frontend build check: `npm run build` in `./frontend`.
- Must authenticate to GCP using `google-github-actions/auth@v2` with Workload Identity Federation.

---

### Task 1: Create GitHub Actions Workflow File

**Files:**
- Create: `.github/workflows/deploy.yml`

**Interfaces:**
- Consumes: Workload Identity Provider `projects/686815886180/locations/global/workloadIdentityPools/github-pool/providers/github-provider` and Service Account `github-actions-deployer@bd-to-dd.iam.gserviceaccount.com`.
- Produces: GitHub Actions deployment pipeline for `.github/workflows/deploy.yml`.

- [ ] **Step 1: Write `.github/workflows/deploy.yml`**

Create `.github/workflows/deploy.yml` with the following content:

```yaml
name: CI/CD Production Pipeline

on:
  push:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: read
  id-token: write

jobs:
  test-and-lint:
    name: Run Unit Tests & Build Checks
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Setup Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"
          cache-dependency-path: "backend/requirements.txt"

      - name: Install Backend Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.txt

      - name: Run Backend Unit Tests
        run: |
          python -m unittest discover -s backend/tests

      - name: Setup Node.js 22
        uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: "npm"
          cache-dependency-path: "frontend/package-lock.json"

      - name: Install Frontend Dependencies
        working-directory: ./frontend
        run: |
          npm ci

      - name: Check Frontend Build Compilation
        working-directory: ./frontend
        run: |
          npm run build

  deploy-production:
    name: Deploy to Google Cloud Run
    needs: test-and-lint
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Authenticate to Google Cloud (Keyless WIF)
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: 'projects/686815886180/locations/global/workloadIdentityPools/github-pool/providers/github-provider'
          service_account: 'github-actions-deployer@bd-to-dd.iam.gserviceaccount.com'

      - name: Setup Google Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Deploy to Cloud Run Production
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          QDRANT_URL: ${{ secrets.QDRANT_URL }}
          QDRANT_API_KEY: ${{ secrets.QDRANT_API_KEY }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          CLOUD_SQL_INSTANCE: "bd-to-dd:asia-southeast1:bd-to-dd"
          GCS_BUCKET_NAME: "bd-to-dd-assets"
        run: |
          chmod +x ./deploy_production.sh
          ./deploy_production.sh
```

- [ ] **Step 2: Verify file creation**

Run: `ls -la .github/workflows/deploy.yml`
Expected: File exists with correct permissions.

- [ ] **Step 3: Commit workflow file**

```bash
git add .github/workflows/deploy.yml docs/
git commit -m "ci: add GitHub Actions production deployment workflow using WIF keyless auth"
```
