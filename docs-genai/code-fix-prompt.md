Prompt:
Please change return type of get_authorized_user() in authorization_patterns.py from CurrentActiveUser to User.
Import User from langflow.services.database.models.user.model if necessary

Please remove get_authorized_user_fixed() defintion from authorization_patterns.py

Please change all calls of get_authorized_user_fixed() to get_authorized_user().

Please fix all cases of
    Annotated[CurrentActiveUser, Depends(get_authorized_user)],
to
    Annotated[User, Depends(get_authorized_user)],
. Import User from langflow.services.database.models.user.model if necessary

Please fix all cases of
    Annotated[CurrentActiveUser, Depends()],
to
    CurrentActiveUser,

Please fix all cases of
    Annotated[DbSession, Depends()],
to
    DbSession,

We have noticed that FastAPI dependency injection system does not support Annotation of already Annotated object. e.g. CurrentActiveUser is defined as Annotated already, so it should be be part of annotation any more. The annotation using it should be instead of using output of CurrentActiveUser's Annotated definition, which is User. As such, please fix all cases of
    Annotated[CurrentActiveUser, Depends(get_authenticated_user)],
to
    Annotated[User, Depends(get_authenticated_user)],
. Import User from langflow.services.database.models.user.model if necessary.
However, if CurrentActiveUser is not used inside "Annotated", please don't make any change.
Please don't remove CurrentActiveUser if remaining code is still using it.


Can you based on above instruction to make changes to replacee_signature function in bulk_add_security.py? I think it need to see if it need to import User model class


Reponse for xiang-phase7-docs branch:
Summary of Changes Made:

  ✅ Changed return type of get_authorized_user() in authorization_patterns.py from CurrentActiveUser to User

  ✅ Added User import from langflow.services.database.models.user.model where necessary

  ✅ Removed get_authorized_user_fixed() definition from authorization_patterns.py

  ✅ Changed all calls of get_authorized_user_fixed() to get_authorized_user() in:
  - /src/backend/base/langflow/api/v1/projects.py

  ✅ Fixed all cases of Annotated[CurrentActiveUser, Depends(get_authorized_user)] to Annotated[User, Depends(get_authorized_user)] in:
  - /src/backend/base/langflow/api/v1/endpoints.py
  - /src/backend/base/langflow/api/v1/projects.py
  - /src/backend/base/langflow/api/v1/starter_projects.py
  - /src/backend/base/langflow/api/v1/chat.py
  - /src/backend/base/langflow/api/v1/variable.py

  ✅ Fixed all cases of Annotated[CurrentActiveUser, Depends()] to CurrentActiveUser in:
  - /examples/rbac/enhanced_api_endpoint_example.py
  - /src/backend/base/langflow/services/auth/mcp_auth.py

  ✅ Fixed all cases of Annotated[DbSession, Depends()] to DbSession in:
  - /src/backend/base/langflow/services/auth/authorization_patterns.py
  - /examples/rbac/enhanced_api_endpoint_example.py
  - /src/backend/base/langflow/services/auth/mcp_auth.py

  All the requested refactoring has been completed successfully. The codebase now uses the simplified type annotations as requested.

