#!/bin/bash

# ContextKeeper v3.0 - Branch Cleanup Script
# This script helps clean up branches after pull requests are merged

set -e

echo "🧹 ContextKeeper v3.0 - Branch Cleanup Script"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository. Please run this script from the project root."
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
print_status "Current branch: $CURRENT_BRANCH"

# Check if we're on master/main branch
if [[ "$CURRENT_BRANCH" != "master" && "$CURRENT_BRANCH" != "main" ]]; then
    print_warning "You're not on the master/main branch. Switching to master..."
    git checkout master
    CURRENT_BRANCH="master"
fi

# Update local repository
print_status "Updating local repository..."
git fetch --all --prune

# Get list of local branches (excluding current branch)
LOCAL_BRANCHES=$(git branch | grep -v "^\*" | sed 's/^[[:space:]]*//')

# Get list of remote branches that have been merged
MERGED_REMOTE_BRANCHES=$(git branch -r --merged | grep -v "origin/master" | grep -v "origin/main" | sed 's/origin\///')

print_status "Found local branches:"
echo "$LOCAL_BRANCHES" | while read branch; do
    if [[ -n "$branch" ]]; then
        echo "  - $branch"
    fi
done

print_status "Found merged remote branches:"
echo "$MERGED_REMOTE_BRANCHES" | while read branch; do
    if [[ -n "$branch" ]]; then
        echo "  - $branch"
    fi
done

# Ask for confirmation
echo
print_warning "This script will delete the following branches:"
echo "  - feature/analytics-dashboard-fix (if merged)"
echo "  - Any other merged feature branches"
echo
read -p "Do you want to proceed with cleanup? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Proceeding with branch cleanup..."
    
    # Delete feature/analytics-dashboard-fix if it exists locally
    if git show-ref --verify --quiet refs/heads/feature/analytics-dashboard-fix; then
        print_status "Deleting local feature/analytics-dashboard-fix branch..."
        git branch -d feature/analytics-dashboard-fix
        print_success "Deleted local feature/analytics-dashboard-fix branch"
    fi
    
    # Delete remote feature/analytics-dashboard-fix if it exists
    if git ls-remote --heads origin feature/analytics-dashboard-fix | grep -q feature/analytics-dashboard-fix; then
        print_status "Deleting remote feature/analytics-dashboard-fix branch..."
        git push origin --delete feature/analytics-dashboard-fix
        print_success "Deleted remote feature/analytics-dashboard-fix branch"
    fi
    
    # Clean up other merged feature branches
    echo "$LOCAL_BRANCHES" | while read branch; do
        if [[ -n "$branch" && "$branch" =~ ^feature/ ]]; then
            print_status "Checking if $branch is merged..."
            if git branch --merged | grep -q "$branch"; then
                print_status "Deleting merged local branch: $branch"
                git branch -d "$branch"
                print_success "Deleted local branch: $branch"
            fi
        fi
    done
    
    # Clean up merged remote branches
    echo "$MERGED_REMOTE_BRANCHES" | while read branch; do
        if [[ -n "$branch" && "$branch" =~ ^feature/ ]]; then
            print_status "Deleting merged remote branch: $branch"
            git push origin --delete "$branch" 2>/dev/null || print_warning "Could not delete remote branch $branch (may already be deleted)"
        fi
    done
    
    print_success "Branch cleanup completed!"
    
else
    print_warning "Branch cleanup cancelled."
fi

echo
print_status "Current branch status:"
git branch -a

echo
print_success "Cleanup script completed!" 