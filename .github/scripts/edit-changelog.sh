#!/bin/bash

version="$1"
TAG_PREFIX="$2"

prevVersion=$(
    cat CHANGELOG.md | \
    # get lines with version nums on them
    grep '## \[[0-9].*\] - [0-9]\{4\}\(-[0-9]\{2\}\)\{2\}' | \
    # extract version number
    grep -o '[0-9]\+\(\.[0-9]\+\)\{2\}' | \
    # get latest one
    head -n 1
)

# add new header for new version
awk -v version="$version" -v date="$(date +'%Y-%m-%d')" '
    1;/## \[Unreleased\]/{ print "\n\n## [" version "] - " date }
' CHANGELOG.md > CHANGELOG.md.temp

mv CHANGELOG.md.temp CHANGELOG.md

# update links
sed -ri 's|(\[unreleased\]: .*compare\/'$TAG_PREFIX')(.*)(\.\.\.HEAD)|\1'$version'\3|g' CHANGELOG.md

awk -v prev="$TAG_PREFIX$prevVersion" \
    -v prefix="$TAG_PREFIX" \
    -v version="$version" \
    -v repo="$GITHUB_REPOSITORY" '
    1;/\[unreleased\]: /{
        print "[" version "]: https://github.com/Crozzers/string-fixer/compare/" prev "..." prefix version
    }
    ' CHANGELOG.md > CHANGELOG.md.temp

mv CHANGELOG.md.temp CHANGELOG.md

echo "new changelog:"
echo "--------------"
cat CHANGELOG.md
