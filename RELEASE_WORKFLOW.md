# 🚀 Release Workflow Guide

## How It Works Now

Your release process has been updated to use a pull request-based workflow that keeps your local development environment in sync.

### The New Process

1. **You make changes locally** and push to `main` branch
2. **Release workflow triggers** and creates a release pull request
3. **You review and merge** the release PR (this syncs your local repo)
4. **Post-release actions** create the GitHub release automatically

## Step-by-Step Workflow

### 1. Development Phase
```bash
# Make your changes locally
# Edit your code files
# Test locally

# Commit and push (this triggers the release workflow)
git add .
git commit -m "feat: your new feature"
git push origin main
```

### 2. Release Phase
- ✅ GitHub Actions runs the "Release and Changelog" workflow
- ✅ Creates a pull request with:
  - Updated `package.json` version
  - Generated/updated `CHANGELOG.md`
  - Updated `wnsm-smartmeter/config.json`
  - Built and pushed Docker images

### 3. Review and Merge
- 📋 Check the release PR on GitHub
- 🔍 Review the changes (version bump, changelog, etc.)
- ✅ Merge the PR (this automatically syncs your local repo when you pull)

### 4. Sync Your Local Environment
```bash
# Pull the merged changes to your local repository
git pull origin main

# You now have all the release changes locally!
# Ready for your next development cycle
```

### 5. Automatic Post-Release
- 🎉 GitHub release is created automatically
- 📦 Docker images are available in the registry
- 🏷️ Git tags are properly set

## Benefits of This Approach

✅ **No more sync issues** - Your local repo stays in sync  
✅ **Review before release** - You can see exactly what changed  
✅ **Clean history** - All release changes are in organized PRs  
✅ **Automated Docker builds** - Images are built and pushed automatically  
✅ **Proper GitHub releases** - Created automatically after merge  

## Manual Release (Optional)

You can also trigger releases manually:

1. Go to GitHub Actions tab
2. Select "Release and Changelog" workflow  
3. Click "Run workflow"
4. Choose release type (patch/minor/major)
5. Follow the same review and merge process

## Troubleshooting

**Q: What if I forget to pull after merging a release PR?**  
A: Just run `git pull origin main` before your next development session.

**Q: Can I still push directly to main for small fixes?**  
A: Yes! The workflow only triggers release PRs, it doesn't prevent regular pushes.

**Q: What if the release workflow fails?**  
A: Check the GitHub Actions logs, fix the issue, and push again to trigger a new release.