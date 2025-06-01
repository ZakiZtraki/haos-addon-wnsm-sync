#!/usr/bin/env pwsh

Write-Host "🚀 Setting up Conventional Commits for WNSM Sync project..." -ForegroundColor Green

# Check if Node.js is installed
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js is not installed. Please install Node.js first." -ForegroundColor Red
    exit 1
}

# Check if Python is installed
if (-not (Get-Command python -ErrorAction SilentlyContinue) -and -not (Get-Command python3 -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python is not installed. Please install Python first." -ForegroundColor Red
    exit 1
}

Write-Host "📦 Installing Node.js dependencies..." -ForegroundColor Yellow
npm install

Write-Host "🐍 Installing Python commitizen..." -ForegroundColor Yellow
pip install commitizen

Write-Host "⚙️ Setting up Git configuration..." -ForegroundColor Yellow
git config commit.template .gitmessage
git config --global init.defaultBranch main

Write-Host "🔧 Setting up Git hooks..." -ForegroundColor Yellow
# Create pre-commit hook for commit message validation
New-Item -ItemType Directory -Force -Path .git/hooks | Out-Null

$commitMsgHook = @'
#!/bin/sh
# Validate commit message format
commit_regex='^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?: .{1,50}'

if ! grep -qE "$commit_regex" "$1"; then
    echo "❌ Invalid commit message format!"
    echo "Format: <type>[optional scope]: <description>"
    echo "Example: feat(api): add support for 15-minute intervals"
    echo ""
    echo "Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert"
    exit 1
fi
'@

$commitMsgHook | Out-File -FilePath .git/hooks/commit-msg -Encoding ASCII

Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Usage:" -ForegroundColor Cyan
Write-Host "  npm run commit          # Interactive commit with Commitizen" -ForegroundColor White
Write-Host "  npm run release         # Generate changelog and bump version" -ForegroundColor White
Write-Host "  cz commit              # Python commitizen (alternative)" -ForegroundColor White
Write-Host "  cz bump                # Python version bump and changelog" -ForegroundColor White
Write-Host ""
Write-Host "🎯 Next steps:" -ForegroundColor Cyan
Write-Host "1. Make your changes" -ForegroundColor White
Write-Host "2. Stage files: git add ." -ForegroundColor White
Write-Host "3. Commit: npm run commit" -ForegroundColor White
Write-Host "4. Release: npm run release" -ForegroundColor White