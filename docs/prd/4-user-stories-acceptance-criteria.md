# **4\. User Stories & Acceptance Criteria**

**Epic 1: Permission Model & Enforcement Rules**

**`Feature: Story 1.1 – Permission Catalog (CRUD + Extended) and Basic Enforcement`**

  `As a Security Engineer`
  `I want a simple permission catalog with CRUD and a few extended actions`
  `So that roles can be built consistently and critical actions are gated`

  `Background:`
    `Given the system exposes a permission catalog used by the Role Builder and enforcement`
    `And permissions can be granted at an appropriate scope per resource`

  `@AC1 Scenario: Catalog includes CRUD and the specified extended permissions`
    `When I query the permission catalog`
    `Then it contains CRUD actions: "create","read","update","delete" for core resources (e.g., flows, components)`
    `And it contains extended actions:`
      `| id                         |`
      `| export_flow                |`
      `| deploy_environment         |`
      `| invite_users               |`
      `| modify_component_settings  |`
      `| manage_tokens              |`

  `@AC2 Scenario: Role builder only accepts known permission IDs`
    `Given I attempt to create a role with ["export_flow","unknown permission"]`
    `When I save the role`
    `Then I see an error "Unknown permission id: unknown:perm"`
    `And the role is not created`

  `@AC3 Scenario: Enforcement — export flow requires export_flow`
    `Given user Jo has "can_export_flow" on Flow=F123`
    `When Jo exports Flow=F123`
    `Then the export succeeds`
    `When Jo exports Flow=F124`
    `Then access is denied with "permission_required: export_flow"`

  `@AC4 Scenario: Enforcement — deploy requires deploy_environment`
    `Given user Alex has "deploy_environment" on Environment=Staging`
    `When Alex deploys to Staging`
    `Then the deployment is queued`
    `When Alex deploys to Production without that permission`
    `Then access is denied with "permission_required: deploy_environment"`

  `@AC5 Scenario: Enforcement — inviting users requires invite_users`
    `Given user Pat has "invite_users" at Workspace=WB1`
    `When Pat invites "new@acme.com" to a project under WB1`
    `Then the invite is sent`
    `When Pat invites a user to a different workspace without that permission`
    `Then access is denied with "permission_required:invite_users"`

`@AC6`
`Scenario: Enforcement — only the invited user can accept`
  `Given an invite INV1 exists for "new@acme.com" to Workspace=WB1 with status "pending" and not expired`
  `And user New is authenticated as "new@acme.com"`
  `When New accepts INV1`
  `Then membership is granted to WB1 per the invite role/scope`
  `And INV1 status becomes "accepted"`

  `When user Eve authenticated as "eve@acme.com" attempts to accept INV1`
  `Then access is denied with "invite_not_for_user"`
  `And INV1 status remains "pending"`

  `@AC7 Scenario: Enforcement — modifying a component requires modify_component permission`
    `Given user Lee has "modify_component" on Component=C9 in Flow=F7`
    `When Lee modifies settings of Component=C9`
    `Then the change is saved`
    `When Lee modifies settings of Component=C10`
    `Then access is denied with "permission_required: modify_component"`

  `@AC8 Scenario: Enforcement — managing tokens requires manage_tokens`
    `Given user Kim has "manage_tokens" at Project=PRJ1`
    `When Kim creates an API token scoped to PRJ1`
    `Then the token is created`
    `When Kim revokes a token in PRJ2 without that permission`

##     `Then access is denied with "permission_required: manage_tokens"`

**`Feature: Story 1.2 – Create and Manage Custom Roles`**
  `As an Admin`
  `I want to define custom roles with specific permissions`
  `So that I can tailor access control to my team’s workflows`

  `Background:`
    `Given I am logged in as an Admin`
    `And I am on the Role Management page`

  `@AC1 : Scenario: Successful creation of a custom role`
    `Given I enter role name "Deployer"`
    `And I select permissions ["deploy_environment","read"]`
    `When I save the role`
    `Then a role named "Deployer" is created`
    `And it is available for assignment to users or groups`

  `@AC2 : Scenario: Prevent duplicate role names`
    `Given a role "Editor" already exists`
    `When I try to create another role named "Editor"`
    `Then I see an error "Role name must be unique"`
    `And the role is not created`

  `@AC3 : Scenario: Edit role and track version`
    `Given a role "Deployer" with permissions ["deploy_environment"]`
    `When I add "read" to the role`
    `Then the updated role is saved as a new version`
    `And the audit log shows before and after states`

---

## **Epic 2: Identity Management & Role Assignment**

**`Feature: Story 2.1 – Assign Roles to Users and Groups within a Scope`**
  `As an Admin`
  `I want to assign existing roles to users and groups within a scope`
  `So that access is limited to the correct resource`

  `Background:`
    `Given a role "Deployer" exists`
    `And a group "Platform" exists with user Sam`

  `@AC1 Scenario: Assign role to a group within a scope`
    `When I assign role "Deployer" to group "Platform" in Project=PRJ1`
    `Then all members of "Platform" inherit the "Deployer" role in PRJ1`

  `@AC2 Scenario: Remove role assignment`
    `Given Sam has role "Deployer" in PRJ1 via group "Platform"`
    `When I remove "Platform" from "Deployer" in PRJ1`
    `Then Sam no longer has the "Deployer" role in PRJ1`

 `@AC Scenario: Static scope hierarchy is defined and immutable at runtime`
    `Given LangBuilder publishes a canonical scope hierarchy aligned to its concept model`
    `Then the hierarchy order is:`
      `| rank | scope       |`
      `| 1    | Workspace   |`
      `| 2    | Project     |`
      `| 3    | Environment |`
      `| 4    | Flow        |`
      `| 5    | Component   |`
    `And API/Token scopes MUST be bound to one of the above scopes as their resource context`
    `And Org Admins cannot change this hierarchy via settings or API`

`@AC4 Scenario: Higher-scope grants cascade to lower scopes (inheritance)`
    `Given Mia has role "Editor" at Workspace=WB1`
    `When Mia edits a flow in Project=PRJ1 under WB1`
    `Then the edit is allowed`

`@AC5 Feature: Permission precedence across scopes`

`Background:`
    `Given the scope hierarchy is Workspace > Project > Flow`
    `And effective permissions are determined by:`
      `| order | rule                         |`
      `| 1     | closest matching allow wins  |`
      `| 2     | default deny (no match)      |`

  `Scenario: Closest scope allow overrides inherited grant`
    `Given Workspace=WB1 grants "read" to Lee`
    `And Project=PRJ2 grants "edit" to Lee`
    `When Lee edits a flow in PRJ2`
    `Then the edit is allowed`
    `And Lee still cannot edit flows in PRJ3 (no project-level grant)`

  `Scenario: Inherited allow applies if no closer grant exists`
    `Given Workspace=WB1 grants "read" to Lee`
    `And Project=PRJ2 has no grant for "read" to Lee`
    `When Lee reads a flow in PRJ2`
    `Then the read is allowed`

  `Scenario: Default deny when no grant at any scope`
    `Given Workspace=WB1 has no grant for "delete" to Lee`
    `And Project=PRJ2 has no grant for "delete" to Lee`
    `And Flow=F9 has no grant for "delete" to Lee`
    `When Lee deletes flow F9`
    `Then the delete is denied`


  `@AC7 Scenario: Component-level permissions restrict access to the specified component only`
    `Given Jo has "modify" on Component=C9 within Flow=F7`
    `When Jo modifies Component=C9`
    `Then the change is saved`
    `When Jo modifies Component=C10 within the same flow`
    `Then access is denied with "permission_required: components:modify"`

  `@AC8 Scenario: Environment-level scoping restricts actions by environment`
    `Given Alex has "deploy" on Environment=Staging in Project=PRJ1`
    `When Alex deploys to Staging in PRJ1`
    `Then the deployment is queued`
    `When Alex deploys to Production in PRJ1`
    `Then access is denied with "permission_required: deploy"`

  `@AC9 Scenario: API/Token scopes bind to a concrete resource scope and do not expand access`
    `Given a service token T1 is created with actions ["read"] scoped to Project=PRJ1`
    `When T1 is used to read flows in PRJ1`
    `Then the request succeeds`
    `When T1 is used to read flows in PRJ2`
    `Then the request is denied with "token_scope_violation"`

**`Feature: Story 2.2 – Authenticate via Single Sign-On (SSO)`**
  `As a User`
  `I want to log in to LangBuilder using my company Identity Provider (IdP)`
  `So that I don’t need a separate LangBuilder password and my org’s auth policies are enforced`

  `Background:`
    `Given the organization has configured SSO with an IdP supporting OIDC or SAML`
    `And the SSO configuration has been validated with a successful metadata discovery`
    `And the SSO connection is set to either "Optional" or "Enforce SSO"`

  `@AC1 Scenario: Successful SSO authentication (IdP-initiated)`
    `Given I start from the IdP app launcher and select the LangBuilder application`
    `When the IdP authenticates me successfully`
    `Then I am redirected to LangBuilder with a valid assertion`
    `And I am logged in to my existing LangBuilder account mapped by my email`
    `And my session is established with the org’s configured timeout`

  `@AC2 Scenario: Successful SSO authentication (SP-initiated)`
    `Given I open the LangBuilder login page`
    `When I click "Sign in with SSO" and enter my company domain`
    `And I am redirected to the IdP and authenticate successfully`
    `Then I am redirected back to LangBuilder and logged in`

  `@AC3 Scenario: Account not provisioned blocks access`
    `Given I authenticate successfully at the IdP`
    `And my user does not exist in LangBuilder`
    `When I return to LangBuilder`
    `Then I see the error "Your account is not provisioned in LangBuilder"`
    `And I am not logged in`

  `@AC4 Scenario: Enforce SSO disables local password login`
    `Given the organization setting "Enforce SSO" is enabled`
    `When I open the LangBuilder login page`
    `Then the username/password form is hidden or disabled`
    `And only "Sign in with SSO" is available`

  `@AC5 Scenario: MFA is enforced by the IdP and honored by LangBuilder`
    `Given the IdP requires MFA for my account`
    `When I complete MFA successfully at the IdP`
    `Then I am logged into LangBuilder without an additional MFA prompt`
    `And the audit log records MFA="passed" from IdP context`

  `@AC6 Scenario: Attribute mapping populates user profile`
    `Given the IdP assertion includes "email", "name", and "groups"`
    `And the org has mapped IdP "groups" to LangBuilder groups`
    `When I log in via SSO`
    `Then my LangBuilder profile shows the mapped name and email`
    `And my LangBuilder group memberships match the mapped IdP groups`

  `@AC7 Scenario: Invalid or expired SSO assertion is rejected`
    `Given the IdP posts an assertion with an invalid signature or outside the allowed time window`
    `When LangBuilder validates the assertion`
    `Then access is denied with HTTP 401 and error "invalid_sso_assertion"`
    `And the event is recorded in the audit log with reason`

  `@AC8 Scenario: Replay protection prevents reused assertions`
    `Given an SSO assertion with ID "ABC123" was already accepted`
    `When the same assertion ID is received again`
    `Then access is denied with error "replay_detected"`
    `And the event is recorded in the audit log`

  `@AC9 Scenario: Small clock skew tolerated during assertion validation`
    `Given the assertion NotBefore/NotOnOrAfter window allows ±5 minutes clock skew`
    `When the assertion timestamp is within the skew tolerance`
    `Then the assertion is accepted`
    `And I am logged in`

  ~~`@AC10 Scenario: Single Logout (SLO) ends LangBuilder session`~~
    ~~`Given the organization enabled SLO`~~
    ~~`And I am logged into LangBuilder via SSO`~~
    ~~`When I sign out from the IdP`~~
    ~~`Then my LangBuilder session is terminated on next back-channel or front-channel SLO signal`~~
    ~~`And I am redirected to the post-logout URL`~~

  `@AC11 Scenario: Fallback when SSO is unavailable and break-glass is enabled`
    `Given the IdP is unreachable`
    `And the organization has configured a break-glass admin account`
    `When the break-glass admin signs in with a one-time password`
    `Then access is granted only to that admin account for a limited window`
    `And the event is flagged in the audit log with reason "break_glass"`

**`Feature: Story 2.3 – Provision Users and Groups via SSO/SCIM`** `(System for Cross-domain Identity Management)`
  `As an Admin`
  `I want users and groups to be provisioned automatically from my IdP`
  `So that onboarding and offboarding are automated`

  `Background:`
    `Given SCIM integration is enabled with my IdP`

  `@AC1 Scenario: New user provisioned`
    `Given HR adds "ana@acme.com" to the "Data Team" group in Okta`
    `When SCIM syncs`
    `Then a new user "ana@acme.com" is created in LangBuilder`
    `And the user is assigned the default "Viewer" role in the "Data Team" project`

  `@AC2 Scenario: User de-provisioned`
    `Given "bob@acme.com" is removed from the IdP`
    `When SCIM syncs`
    `Then "bob@acme.com" is disabled in LangBuilder`
    `And cannot log in`

  `@AC3 Scenario: Group membership drives roles`
    `Given "Data Team" group is mapped to role "Editor" in Project=PRJ1`
    `When HR adds "carol@acme.com" to the "Data Team"`
    `Then Carol automatically gets the "Editor" role in PRJ1`

**`Feature: Story 2.4 – Manage Service Accounts`**
  `As an Admin`
  `I want to create service accounts with scoped permissions`
  `So that automated systems can interact securely with LangBuilder`

  `@AC1 Scenario: Create service account with scope`
    `Given I am an Org Admin`
    `When I create service account "ci-bot" with scope Workspace=WB1 and permissions ["read","deploy_environment"]`
    `Then "ci-bot" can authenticate using a token`
    `And "ci-bot" cannot access resources outside Workspace=WB1`

---

## **Epic 3: Policy Management Interfaces**

**`Feature: Story 3.1 – Manage Roles via Admin UI`**
  `As an Admin`
  `I want to manage roles and permissions through a visual UI`
  `So that I can configure access without coding`

  `Background:`
    `Given I am logged in as an Admin`

  `@AC1 Scenario: Create role through UI`
    `When I open the Roles page and add role "Auditor" with actions ["read","export_flow"]`
    `Then the role appears in the roles table with those actions`

**`Feature: Story 3.2 – Manage Roles via API`**
  `As a DevOps Engineer`
  `I want to create and manage roles through APIs`
  `So that I can integrate RBAC into automation pipelines`

  `@AC1 Scenario: Create role via API`
    `Given I have an Admin API token`
    `When I POST /api/admin/roles with body {name:"QALead", actions:["read","deploy_environment"]}`
    `Then response is 201 with role_id`
    `And GET /api/admin/roles/{role_id} returns the same actions`

**`Feature: Story 3.3 – Manage Roles via IaC`**
  `As a DevOps Engineer`
  `I want to define roles in YAML/Terraform`
  `So that RBAC policies can be version-controlled and automated`

  `@AC1 Scenario: Apply YAML policy`
    `Given I have a YAML file defining role "Ops" with actions ["deploy_environment"]`
    `When I apply the YAML`
    `Then "Ops" exists with those actions`

**Story 3.4 – Assign Roles to Principals via Admin UI**

`As an Admin I want to assign roles to users/groups/service tokens at a workspace/project/flow/environment scope so that access can be configured without code.`

`ACs`
`@AC1 Assign role to user at project scope`

 `Given user "carol@acme.com" exists`
`And role "Editor" exists`
`When I assign "Editor" to Carol at Project=PRJ1`
`Then Carol has "Editor" in PRJ1`
`And Carol does not have "Editor" in PRJ2`

`@AC2 Assign role to group`

 `Given group "Data Team" exists`
`When I assign "Viewer" to "Data Team" at Workspace=WB1`
`Then members of "Data Team" have "Viewer" in WB1`

`@AC3 Time-bound grant (optional but valuable)`

 `When I assign "Deploy" to "ops@acme.com" in PRJ1 with expires_at=2025-09-30`
`Then the grant is active before 2025-09-30 and inactive after`

`@AC4 Revoke / replace`

 `Given Carol has "Editor" in PRJ1`
`When I revoke the grant`
`Then Carol no longer has "Editor" in PRJ1`

**Story 3.5 – Assign Roles via API**

`As a DevOps Engineer I want to bind roles to principals via API so I can automate RBAC.`
`ACs`
`@AC1 Create grant`

 `Given Admin API token`
`When POST /api/admin/grants {principal:"user:carol@acme.com", role:"Editor", scope:{project:"PRJ1"}}`
`Then response 201 with grant_id`
`And GET /api/admin/grants/{grant_id} shows the same binding`

`@AC2 Revoke grant`

 `When DELETE /api/admin/grants/{grant_id}`
`Then response 204`
`And subsequent GET shows the grant is gone`

**Story 3.6 – Assign Roles via IaC (YAML/Terraform)**

`As a DevOps Engineer I want to declare role bindings as code so they’re version-controlled.`
`ACs`
`@AC1 Apply bindings`

 `Given YAML:`
  `grants:`
    `- principal: user:carol@acme.com`
      `role: Editor`
      `scope: { project: PRJ1 }`
    `- principal: group:Data Team`
      `role: Viewer`
      `scope: { workspace: WB1 }`
`When I apply the YAML`
`Then both grants exist`

---

## **Epic 4: Runtime Enforcement & Security Controls**

**`Feature: Story 4.1 – Deny by Default`**
  `As a Security Engineer`
  `I want actions denied unless explicitly permitted`
  `So that no unintended access is granted`

  `Background:`
    `Given user Kai has no roles on Project=PRJ1`

  `@AC1`
  `Scenario: Attempt action without role`
    `When Kai tries to view flows in PRJ1`
    `Then access is denied with HTTP 403 "rbac_denied"`

**`Feature: Story 4.2 – Token Scope Enforcement`**
  `As a Developer`
  `I want API tokens scoped to roles and resources`
  `So that tokens cannot be misused`

  `Background:`
    `Given user Pat has permission to create tokens`

  `@AC1`
  `Scenario: Scoped token access`
    `When Pat creates a token with actions ["read"] scoped to PRJ1`
    `Then the token only works for reading flows in PRJ1`
    `And access outside PRJ1 is denied`

---

## **Epic 5: Auditability & Compliance**

**`Feature: Story 5.1 – Log All RBAC Changes`**
  `As a Compliance Officer`
  `I want all role assignments and changes logged`
  `So that audits can be performed`

  `@AC1 Scenario: Log role assignment`
    `Given I assign role "Editor" to user "ana@acme.com" at Project=PRJ1`
    `Then an audit entry is recorded with actor, subject, role, scope, and timestamp`

**`Feature: Story 5.2 – Export Compliance Report`**
  `As an Auditor`
  `I want to export access reports`
  `So that I can review effective permissions`

  `@AC1 Scenario: Export user access report`
    `Given I am an Auditor`
    `When I export the "User Access" report for Workspace=WB1`
    `Then I receive a CSV with users, groups, roles, scopes, and effective permissions`

---
