#!/bin/bash

# Pre-commit setup script for myunla project
set -e

echo "🚀 Setting up pre-commit hooks for myunla..."

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "❌ pre-commit is not installed. Installing it..."

    # Try to install via pip
    if command -v pip &> /dev/null; then
        pip install pre-commit
    elif command -v pip3 &> /dev/null; then
        pip3 install pre-commit
    else
        echo "❌ pip is not available. Please install pre-commit manually:"
        echo "   pip install pre-commit"
        exit 1
    fi
else
    echo "✅ pre-commit is already installed"
fi

# Install the pre-commit hooks
echo "📦 Installing pre-commit hooks..."
pre-commit install

# Install commit-msg hook for conventional commits (optional)
echo "📝 Installing commit-msg hook..."
pre-commit install --hook-type commit-msg

# Update pre-commit hooks to latest versions
echo "🔄 Updating pre-commit hooks..."
pre-commit autoupdate

# Run pre-commit on all files to check setup
echo "🧪 Running pre-commit on all files..."
if pre-commit run --all-files; then
    echo "✅ Pre-commit setup completed successfully!"
    echo ""
    echo "🎉 All checks passed! You're ready to commit."
    echo ""
    echo "📋 Available commands:"
    echo "   pre-commit run --all-files  # Run all hooks on all files"
    echo "   pre-commit run <hook_id>    # Run specific hook"
    echo "   pre-commit autoupdate       # Update hook versions"
    echo "   pre-commit clean            # Clean pre-commit cache"
else
    echo "⚠️  Some pre-commit hooks failed. Please fix the issues and run again."
    echo ""
    echo "💡 You can run the following to fix most issues automatically:"
    echo "   pre-commit run --all-files"
    exit 1
fi

echo ""
echo "🔧 Pre-commit is now configured and will run automatically on every commit."
echo "   To skip pre-commit hooks temporarily, use: git commit --no-verify"
