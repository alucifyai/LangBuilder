# **5\. Non-Functional Requirements (Cross-Epic Constraints)**

## **5.1 Performance & Latency**

* RBAC permission evaluation must add **≤100 ms (p95)** overhead to any API call.

* Cached decisions should add **≤10 ms (p95)** overhead.

* UI rendering must respect permissions dynamically without visible lag (\<200 ms).

## **5.2 Scalability**

* Support **100K active users**, **10K groups**, and **1M role bindings** per workspace.

* Handle **10K concurrent sessions** without degradation.

* Enforcement and audit logging must scale independently.

## **5.3 Security**

* **Deny-by-default**; no implicit access.

* **Explicit deny overrides allow**.

* All RBAC configurations encrypted **at rest (AES-256)** and **in transit (TLS 1.2+)**.

* Tokens are **short-lived**, rotatable, and revocable.

* Service accounts restricted to **least-privilege scopes**.

## **5.4 Privacy**

* Logs redact sensitive fields (tokens, passwords, PII).

* Support **GDPR/CCPA compliance**: allow data export and deletion.

* Personal identifiers masked in reports unless accessed by Admins or Auditors.

## **5.5 Compliance & Auditability**

* Support **SOC 2 / ISO 27001** controls.

* Immutable audit logs (WORM storage).

* All RBAC changes traceable (actor, subject, resource, action, timestamp).

* Exportable reports in **CSV/JSON** formats.

## **5.6 Reliability & Availability**

* RBAC service must maintain **99.9% uptime**.

* Outage fallback: **last known good policy cache** with audit warnings.

* Role/permission changes must be **atomic**.

## **5.7 Extensibility**

* Pluggable policy engine support (e.g., **OPA/Rego**).

* Webhook events for RBAC decisions (for SIEM/SOC integration).

* Support **just-in-time elevation** and **time-boxed grants**.