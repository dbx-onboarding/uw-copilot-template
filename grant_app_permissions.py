# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Grant UW CoPilot App Permissions
# MAGIC %md
# MAGIC # 🔑 Grant UW CoPilot App Permissions
# MAGIC
# MAGIC Run **all 3 cells** to wire the new app SP to all required resources.
# MAGIC
# MAGIC **App SP:** `075574b1-1aea-4d9d-9dce-ee77ac770210`
# MAGIC
# MAGIC | Resource | Permission |
# MAGIC |---|---|
# MAGIC | Warehouse `a829316f6b992da1` | `CAN_USE` |
# MAGIC | Serving endpoint `atlas_insurance_rag_endpoint` | `CAN_QUERY` |
# MAGIC | Catalog `atlas` | `USE CATALOG` |
# MAGIC | Schema `atlas.atlas_insurance_rag` | `USE SCHEMA` + `SELECT` |

# COMMAND ----------

# DBTITLE 1,1 — Warehouse + Serving Endpoint (SDK)
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import WarehouseAccessControlRequest, WarehousePermissionLevel
from databricks.sdk.service.serving import ServingEndpointAccessControlRequest, ServingEndpointPermissionLevel

w  = WorkspaceClient()
SP = "075574b1-1aea-4d9d-9dce-ee77ac770210"

# Warehouse
w.warehouses.update_permissions(
    warehouse_id="a829316f6b992da1",
    access_control_list=[WarehouseAccessControlRequest(
        service_principal_name=SP,
        permission_level=WarehousePermissionLevel.CAN_USE
    )]
)
print("✅ Warehouse CAN_USE granted")

# Serving endpoint — look up the numeric ID first; the permissions API requires it
ep = w.serving_endpoints.get(name="atlas_insurance_rag_endpoint")
w.serving_endpoints.update_permissions(
    serving_endpoint_id=ep.id,
    access_control_list=[ServingEndpointAccessControlRequest(
        service_principal_name=SP,
        permission_level=ServingEndpointPermissionLevel.CAN_QUERY
    )]
)
print("✅ Serving endpoint CAN_QUERY granted")

# COMMAND ----------

# DBTITLE 1,2 — Unity Catalog (SDK)
from databricks.sdk.service.catalog import PermissionsChange, Privilege, SecurableType

SP = "075574b1-1aea-4d9d-9dce-ee77ac770210"

# Catalog
w.grants.update(
    securable_type="catalog",
    full_name="atlas",
    changes=[PermissionsChange(add=[Privilege.USE_CATALOG], principal=SP)]
)
print("✅ USE CATALOG atlas granted")

# Schema
w.grants.update(
    securable_type="schema",
    full_name="atlas.atlas_insurance_rag",
    changes=[PermissionsChange(
        add=[Privilege.USE_SCHEMA, Privilege.SELECT],
        principal=SP
    )]
)
print("✅ USE SCHEMA + SELECT on atlas.atlas_insurance_rag granted")

# COMMAND ----------

# DBTITLE 1,3 — Verify all permissions landed
SP = "075574b1-1aea-4d9d-9dce-ee77ac770210"

print("=" * 55)
print("Warehouse permissions:")
wh = w.warehouses.get_permissions(warehouse_id="a829316f6b992da1")
for acl in (wh.access_control_list or []):
    sp_name = getattr(acl, 'service_principal_name', None)
    if sp_name == SP:
        print(f"  ✅ {sp_name} → {[p.permission_level.value for p in (acl.all_permissions or [])]}")

print("\nServing endpoint permissions:")
ep_id = w.serving_endpoints.get(name="atlas_insurance_rag_endpoint").id
ep = w.serving_endpoints.get_permissions(serving_endpoint_id=ep_id)
for acl in (ep.access_control_list or []):
    sp_name = getattr(acl, 'service_principal_name', None)
    if sp_name == SP:
        print(f"  ✅ {sp_name} → {[p.permission_level.value for p in (acl.all_permissions or [])]}")

print("\nUC grants — catalog atlas:")
catalog_grants = w.grants.get(securable_type="catalog", full_name="atlas")
for g in (getattr(catalog_grants, 'privilege_assignments', None) or []):
    if g.principal == SP:
        print(f"  ✅ {g.principal} → {g.privileges}")

print("\nUC grants — schema atlas.atlas_insurance_rag:")
schema_grants = w.grants.get(securable_type="schema", full_name="atlas.atlas_insurance_rag")
for g in (getattr(schema_grants, 'privilege_assignments', None) or []):
    if g.principal == SP:
        print(f"  ✅ {g.principal} → {g.privileges}")

print("\nDone — all permissions verified.")
