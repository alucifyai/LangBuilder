# Implementation observation

1. In api/v1/project.py's get project object for a project id, while the folder model has flows as one of the fields, its select is not filling tlows field through ORM. Instead, it separately query flows for this folder id and then put flows as a separate top field in parallel with folder field.



# RBAC Admin Issues

1. Role creation is broken on UI. It seems not even making any request to server. Purely frontend react code broken.

2. Workspace listing api seems have at 3 workspaces in mocked return, whlie the workspace table actually have zero rows.

3. Current code in api/v1/rbac/ has both workspace.py and simple-workspace.py both using Workspace table. The frontend UI in phase 8 seems to be using /simple-workspace api. The simple-workspace api does not have any authentication, which means http://localhost:7860/api/v1/rbac/simple-workspaces/?page=1&page_size=50 can work for any user without login


Fixing project listing api by restoring code that commented out for debugging. Also added space to be allowed character for project name. This validation happened too late in project ceration as the project is already in DB and it only affects when we list out project, whose name has a space or other invalid character. bad design!!

4. api/v1/rbac/roles.py has create and update project's securitysecure_endpoint commented out to get it working. Need to undeerstad