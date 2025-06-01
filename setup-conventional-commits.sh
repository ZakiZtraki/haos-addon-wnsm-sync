#!/bin/bash

echo "🚀 Setting up Conventional Commits for WNSM Sync project..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if Python is installed
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python is not installed. Please install Python first."
    exit 1
fi

echo "📦 Installing Node.js dependencies..."
npm install

echo "🐍 Installing Python commitizen..."
pip install commitizen

echo "⚙️ Setting up Git configuration..."
git config commit.template .gitmessage
git config --global init.defaultBranch main

echo "🔧 Setting up Git hooks..."
# Create pre-commit hook for commit message validation
mkdir -p .git/hooks
cat > .git/hooks/commit-msg << 'EOF'
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
EOF

chmod +x .git/hooks/commit-msg

echo "✅ Setup complete!"
echo ""
echo "📋 Usage:"
echo "  npm run commit          # Interactive commit with Commitizen"
echo "  npm run release         # Generate changelog and bump version"
echo "  cz commit              # Python commitizen (alternative)"
echo "  cz bump                # Python version bump and changelog"
echo ""
echo "🎯 Next steps:"
echo "1. Make your changes"
echo "2. Stage files: git add ."
echo "3. Commit: npm run commit"
echo "4. Release: npm run release"