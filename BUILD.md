# Prerequisite
## For Macbook, XCode Commandline Tools should be installed, so "make" "git" stuff is available
## python 3.11 and up installed. Xiang is using 3.12.10
## node 18 and up is installed. Xiang is using v20.19.4

# add a missing file that blocks dependency install later
touch README.md

# a terminal window that build and run backend
## list all options for "make"
make help
## initialize project in root folder of the project
make init
## setup env
make setup_env
## uv is a python package manager replacing pip
make setup_uv

## install backend dependencies
make install_backend
## run backend in development mode... wait for a minute or two first time as it loads things
make backend

# a 2nd terminal window running frontend server
## install frontend dependencies
make install_frontend
## run frontend in development mode... wait for a minute or two first time as it loads things
make frontend

# in browser go to http://localhost:3000

# another terminal window to run Claude Code. Below are some claude code prompt, navigating sqlite db

## in src/backend/base/langflow, lanflow.db is a sqlite db, can you output its schema?
Note the # of tables is fewer than the entities. Turns out component entity is encoded as json in data field of flow
## please list all users
## please list all flows
## please list all folders
Note: folder entity maps to "project" in UI
## can you list flow for "Xiang's test project"
## can you list the data field for the flow as well?

