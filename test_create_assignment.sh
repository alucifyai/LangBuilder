#!/bin/bash
# Test creating a new assignment

# First login to get a token
echo "Logging in..."
TOKEN=$(curl -s -X POST "http://localhost:7860/api/v1/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=langbuilder&password=langbuilder" | jq -r '.access_token')

echo "Token: ${TOKEN:0:20}..."

# Get user ID
USER_ID="9cff7d8a-adb2-4e6f-bd2e-b838481b6b5e"

# Get role ID for "Viewer" role
VIEWER_ROLE_ID="bcd941dc-1d8a-440d-84a0-35bf819c2b6a"

# Get flow ID for "Basic Prompting"
FLOW_ID="b841a738-5681-49ef-9211-49459aabdf82"

# Create a new assignment
echo -e "\nCreating new assignment (User: langbuilder, Role: Viewer, Scope: Flow - Basic Prompting)..."
curl -s -X POST "http://localhost:7860/api/v1/rbac/assignments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"role_id\": \"$VIEWER_ROLE_ID\",
    \"scope_type\": \"Flow\",
    \"scope_id\": \"$FLOW_ID\",
    \"is_immutable\": false
  }" | jq '.'
