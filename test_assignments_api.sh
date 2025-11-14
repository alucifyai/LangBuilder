#!/bin/bash
# Test the assignments API endpoint

# First login to get a token
echo "Logging in..."
TOKEN=$(curl -s -X POST "http://localhost:7860/api/v1/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=langbuilder&password=langbuilder" | jq -r '.access_token')

echo "Token: ${TOKEN:0:20}..."

# Test assignments endpoint
echo -e "\nFetching assignments..."
curl -s -X GET "http://localhost:7860/api/v1/rbac/assignments" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
