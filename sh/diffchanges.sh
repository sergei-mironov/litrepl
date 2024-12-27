#!/bin/sh

git log --oneline | grep 'Version [0-9]\+\.[0-9]\+\.[0-9]\+' >_versions.txt
HASH_LAST=`git rev-parse HEAD`
HASH_PREV=`head -n 1 _versions.txt | awk '{print $1}' `

# git log $HASH_PREV..$HASH_LAST --pretty=format:"%h %s" --patch -- python ':(exclude)README.md' ':(exclude)semver.txt' >_lastdiff.diff
git log $HASH_PREV..$HASH_LAST --pretty=format:"%h %s" -- python ':(exclude)README.md' ':(exclude)semver.txt' >_lastdiff.diff

cat >_mkchangelog.ai <<"EOF"
You task is to check the diff file and generate a text briefly describing the
changes in good English. Please try to group the changes into "Vim", "Python"
and environment groups.

For reference, consider the already existing changelog file:

```
/append file:CHANGELOG.md in
```

And here is the new diff:

``` diff
/append file:_lastdiff.diff in
```
/ask
EOF
aicli --keep-running _mkchangelog.ai

