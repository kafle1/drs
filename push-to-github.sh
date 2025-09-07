#!/bin/bash

# DRS GitHub Push Script
# This script helps push the DRS project to GitHub

set -e

echo "🚀 DRS GitHub Push Script"
echo "========================="

# Check if remote origin exists
if ! git remote get-url origin >/dev/null 2>&1; then
    echo "❌ No remote origin found!"
    echo ""
    echo "Please set up your GitHub repository first:"
    echo "1. Create a new repository on GitHub"
    echo "2. Copy the repository URL"
    echo "3. Run: git remote add origin <your-repo-url>"
    echo "4. Then run this script again"
    exit 1
fi

echo "📡 Remote origin found:"
git remote get-url origin
echo ""

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "⚠️  Not on main branch. Switching to main..."
    git checkout main
fi

echo ""
echo "📤 Pushing to GitHub..."

# Push to GitHub
git push -u origin main

echo ""
echo "✅ Successfully pushed to GitHub!"
echo ""
echo "🌐 Your repository is now live at:"
git remote get-url origin | sed 's/\.git$//' | sed 's/git@github\.com:/https:\/\/github.com\//'
echo ""
echo "📖 View your README at the repository URL above"
echo "🛠️  Use 'make dev' to start development"
echo "🐳 Use 'make docker-up' for Docker deployment"
