#!/bin/bash
set -euxo pipefail

export CURRENT_PATH=$PWD

set -ex

git clone \
  git@github.com:silimate/sv-tests-results.git \
  --single-branch \
  --depth 1 \
  --branch gh-pages \
  output

cd output || (echo "The output directory doesn't exist! Cloning the sv-tests-results repository failed, please check the ssh-key! Exiting"; exit 1)

rm -rf *
cp -a $CURRENT_PATH/out/report/* -t .
touch .nojekyll
git add .

GIT_MESSAGE_FILE=/tmp/git-message
  cat > $GIT_MESSAGE_FILE <<EOF
Deploy $GITHUB_REF (build $GITHUB_RUN_ID)
Build from $GITHUB_SHA
EOF

git config user.name "Silimate Robot"
git config user.email "sv-tests@silimate.com"

git commit -F $GIT_MESSAGE_FILE

git show -s

git push
