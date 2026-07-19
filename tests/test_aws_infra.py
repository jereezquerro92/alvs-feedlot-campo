
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    if os.environ.get("_T1_UV_BOOTSTRAPPED"):
        print("FAIL: boto3 unavailable even after uv bootstrap", file=sys.stderr)
        sys.exit(2)
    os.environ["_T1_UV_BOOTSTRAPPED"] = "1"
    os.execvp(
        "uv",
        ["uv", "run", "--with", "boto3", "python3", *sys.argv],
    )

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs" / "INVENTORY.md"

PROFILE = os.environ.get("AWS_PROFILE", "kodex")
REGION = os.environ.get("AWS_REGION", "us-east-1")
ACCOUNT = "789650504128"
PROJECT = os.environ.get("PROJECT_SLUG", "astro-drf-aws")
POOL_ID = "us-east-1_IzUPE4fDV"

REQUIRED_TAGS = {"project": PROJECT, "env": "prod", "lifecycle": "ephemeral"}

SESSION = boto3.Session(profile_name=PROFILE, region_name=REGION)


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise AssertionError(msg)


def ok(msg: str) -> None:
    print(f"ok    {msg}")


def skip(msg: str) -> None:
    print(f"skip  {msg}")


def read_inventory() -> str:
    if not INVENTORY.is_file():
        fail(f"missing {INVENTORY.relative_to(ROOT)}")
    return INVENTORY.read_text(encoding="utf-8")


TAGGABLE = [
    (f"secret alvs/prod/{PROJECT}/django", f"secret:alvs/prod/{PROJECT}/django"),
    (f"secret alvs/prod/{PROJECT}/db", f"secret:alvs/prod/{PROJECT}/db"),
    (f"secret alvs/prod/{PROJECT}/cognito", f"secret:alvs/prod/{PROJECT}/cognito"),
    (f"secret alvs/prod/{PROJECT}/s3", f"secret:alvs/prod/{PROJECT}/s3"),
    ("cognito pool us-east-1_IzUPE4fDV", "userpool/us-east-1_IzUPE4fDV"),
    ("rds subnet group", f"subgrp:alvs-prod-{PROJECT}-subnets"),
    (f"rds instance alvs-prod-{PROJECT}-pg", f"db:alvs-prod-{PROJECT}-pg"),
    ("s3 media bucket", f":alvs-{PROJECT}-media-prod"),
    ("ecr backend", f"repository/alvs/{PROJECT}-backend"),
    ("ecr frontend", f"repository/alvs/{PROJECT}-frontend"),
    ("acm cert", "certificate/26dc1f46"),
    ("target group backend", f"targetgroup/tg-{PROJECT}-backend-prod"),
    ("target group frontend", f"targetgroup/tg-{PROJECT}-frontend-prod"),
    ("cloud map namespace", "servicediscovery:us-east-1:789650504128:namespace/"),
    ("log group backend-prod", f"log-group:/alvs/{PROJECT}/backend-prod"),
    ("log group frontend-prod", f"log-group:/alvs/{PROJECT}/frontend-prod"),
]

INVENTORY_TOKENS = [
    f"alvs/prod/{PROJECT}/django",
    f"alvs/prod/{PROJECT}/db",
    f"alvs/prod/{PROJECT}/cognito",
    f"alvs/prod/{PROJECT}/s3",
    "us-east-1_IzUPE4fDV",
    f"alvs-prod-{PROJECT}-subnets",
    f"alvs-prod-{PROJECT}-pg",
    f"alvs-{PROJECT}-media-prod",
    f"alvs/{PROJECT}-backend",
    f"alvs/{PROJECT}-frontend",
    f"tg-{PROJECT}-backend-prod",
    f"tg-{PROJECT}-frontend-prod",
    f"{PROJECT}-prod.local",
    f"/alvs/{PROJECT}/{{backend,frontend}}-prod",
]

IAM_ROLES = [
    f"alvs-prod-{PROJECT}-backend-exec-role",
    f"alvs-prod-{PROJECT}-backend-task-role",
    f"alvs-prod-{PROJECT}-frontend-exec-role",
    f"alvs-prod-{PROJECT}-frontend-task-role",
]


def tagging_map(tag_filters: list[dict]) -> dict[str, dict[str, str]]:
    client = SESSION.client("resourcegroupstaggingapi")
    out: dict[str, dict[str, str]] = {}
    paginator = client.get_paginator("get_resources")
    for page in paginator.paginate(TagFilters=tag_filters):
        for m in page["ResourceTagMappingList"]:
            out[m["ResourceARN"]] = {t["Key"]: t["Value"] for t in m["Tags"]}
    return out


def test_inventory_drift() -> None:
    text = read_inventory()
    missing = [t for t in INVENTORY_TOKENS if t not in text]
    if missing:
        fail(f"INVENTORY.md missing expected ephemeral identifiers: {missing}")
    ok("INVENTORY.md documents every expected ephemeral resource")


def test_taggable_resources_exist_and_tagged() -> None:
    tags_by_arn = tagging_map([{"Key": "project", "Values": [PROJECT]}])
    if not tags_by_arn:
        fail(f"Tagging API returned no resources for project={PROJECT}")

    for label, fragment in TAGGABLE:
        matches = [arn for arn in tags_by_arn if fragment in arn]
        if not matches:
            fail(f"{label}: no tagged resource ARN contains '{fragment}'")
        for arn in matches:
            tags = tags_by_arn[arn]
            for key, val in REQUIRED_TAGS.items():
                if tags.get(key) != val:
                    fail(f"{label} ({arn}): tag {key}={tags.get(key)!r}, want {val!r}")
        ok(f"{label}: exists + carries project/env/lifecycle tags")

    skip("Route 53 records — shared-attachment, not an ephemeral resource")
    skip("gha-deploy-prod trust entry — pending owner run of staged script")
    skip("ALB host + path rules — pending owner run of staged script")


def test_iam_roles_tagged() -> None:
    iam = SESSION.client("iam")
    for role in IAM_ROLES:
        try:
            resp = iam.list_role_tags(RoleName=role)
        except ClientError as exc:
            fail(f"IAM role {role} not found: {exc}")
        tags = {t["Key"]: t["Value"] for t in resp["Tags"]}
        for key, val in REQUIRED_TAGS.items():
            if tags.get(key) != val:
                fail(f"IAM role {role}: tag {key}={tags.get(key)!r}, want {val!r}")
        ok(f"IAM role {role}: exists + carries project/env/lifecycle tags")


def test_cognito_jwks() -> None:
    url = f"https://cognito-idp.{REGION}.amazonaws.com/{POOL_ID}/.well-known/jwks.json"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        fail(f"Cognito JWKS fetch failed ({url}): {exc}")
    keys = body.get("keys")
    if not keys:
        fail(f"Cognito JWKS at {url} served no keys")
    ok(f"Cognito pool {POOL_ID} JWKS serves {len(keys)} key(s)")


def _role_secret_actions(iam, role: str) -> list[str]:
    actions: list[str] = []

    def scan(doc: dict) -> None:
        stmts = doc.get("Statement", [])
        if isinstance(stmts, dict):
            stmts = [stmts]
        for st in stmts:
            if st.get("Effect") != "Allow":
                continue
            acts = st.get("Action", [])
            if isinstance(acts, str):
                acts = [acts]
            for a in acts:
                if a == "*" or a.lower().startswith("secretsmanager"):
                    actions.append(a)

    for p in iam.list_role_policies(RoleName=role)["PolicyNames"]:
        doc = iam.get_role_policy(RoleName=role, PolicyName=p)["PolicyDocument"]
        scan(doc)
    for ap in iam.list_attached_role_policies(RoleName=role)["AttachedPolicies"]:
        arn = ap["PolicyArn"]
        ver = iam.get_policy(PolicyArn=arn)["Policy"]["DefaultVersionId"]
        doc = iam.get_policy_version(PolicyArn=arn, VersionId=ver)[
            "PolicyVersion"
        ]["Document"]
        scan(doc)
    return actions


def test_secrets_and_access() -> None:
    sm = SESSION.client("secretsmanager")
    for comp in ("django", "db", "cognito", "s3"):
        name = f"alvs/prod/{PROJECT}/{comp}"
        try:
            sm.describe_secret(SecretId=name)
        except ClientError as exc:
            fail(f"secret {name} not found: {exc}")
    ok("all four project secrets exist (metadata only)")

    iam = SESSION.client("iam")
    exec_role = f"alvs-prod-{PROJECT}-backend-exec-role"
    found_prefix_grant = False
    for p in iam.list_role_policies(RoleName=exec_role)["PolicyNames"]:
        doc = iam.get_role_policy(RoleName=exec_role, PolicyName=p)["PolicyDocument"]
        stmts = doc.get("Statement", [])
        if isinstance(stmts, dict):
            stmts = [stmts]
        for st in stmts:
            acts = st.get("Action", [])
            if isinstance(acts, str):
                acts = [acts]
            res = st.get("Resource", [])
            if isinstance(res, str):
                res = [res]
            grants_get = any(
                a in ("secretsmanager:GetSecretValue", "secretsmanager:*", "*")
                for a in acts
            )
            scoped = any(f"alvs/prod/{PROJECT}/" in r for r in res)
            if st.get("Effect") == "Allow" and grants_get and scoped:
                found_prefix_grant = True
    if not found_prefix_grant:
        fail(f"{exec_role} lacks GetSecretValue on alvs/prod/{PROJECT}/* prefix")
    ok(f"{exec_role} grants GetSecretValue on alvs/prod/{PROJECT}/* prefix")

    for role in (
        f"alvs-prod-{PROJECT}-frontend-exec-role",
        f"alvs-prod-{PROJECT}-frontend-task-role",
    ):
        acts = _role_secret_actions(iam, role)
        if acts:
            fail(f"{role} unexpectedly grants secret access: {acts}")
        ok(f"{role} has zero secretsmanager permissions")


def test_rds_spec() -> None:
    rds = SESSION.client("rds")
    try:
        inst = rds.describe_db_instances(
            DBInstanceIdentifier=f"alvs-prod-{PROJECT}-pg"
        )["DBInstances"][0]
    except ClientError as exc:
        fail(f"RDS instance alvs-prod-{PROJECT}-pg not found: {exc}")

    if inst["Engine"] != "postgres":
        fail(f"RDS engine {inst['Engine']!r}, want 'postgres'")
    if not inst["EngineVersion"].startswith("17."):
        fail(f"RDS EngineVersion {inst['EngineVersion']!r}, want 17.x")
    if inst["DBInstanceClass"] != "db.t4g.micro":
        fail(f"RDS class {inst['DBInstanceClass']!r}, want db.t4g.micro")
    if inst["PubliclyAccessible"]:
        fail("RDS instance is publicly accessible; must be private")
    if inst["MultiAZ"]:
        fail("RDS instance is Multi-AZ; must be single-AZ (cost)")
    ok(
        f"RDS PostgreSQL {inst['EngineVersion']} db.t4g.micro "
        "single-AZ, not public"
    )
    skip("RDS live connection — EICE tunnel not automated (adr-12 / BD.md)")


def test_cost_no_nat() -> None:
    ec2 = SESSION.client("ec2")
    nats = ec2.describe_nat_gateways(
        Filters=[
            {"Name": "tag:project", "Values": [PROJECT]},
            {"Name": "state", "Values": ["pending", "available"]},
        ]
    )["NatGateways"]
    if nats:
        ids = [n["NatGatewayId"] for n in nats]
        fail(f"cost violation: NAT gateway(s) tagged to project: {ids}")
    ok("cost sanity: no NAT gateways tagged to this project")


def test_absent() -> None:
    tags_by_arn = tagging_map(
        [
            {"Key": "project", "Values": [PROJECT]},
            {"Key": "lifecycle", "Values": ["ephemeral"]},
        ]
    )
    if tags_by_arn:
        arns = "\n  ".join(sorted(tags_by_arn))
        fail(
            f"{len(tags_by_arn)} ephemeral resource(s) still tagged "
            f"project={PROJECT} lifecycle=ephemeral:\n  {arns}"
        )
    ok(f"T8: zero resources tagged project={PROJECT} lifecycle=ephemeral")

    iam = SESSION.client("iam")
    survivors = []
    for role in IAM_ROLES:
        try:
            iam.get_role(RoleName=role)
            survivors.append(role)
        except ClientError:
            pass
    if survivors:
        fail(f"T8: IAM roles still present: {survivors}")
    ok("T8: project IAM roles destroyed")


def main() -> int:
    absent = "--absent" in sys.argv[1:]

    if absent:
        tests = [test_absent]
    else:
        tests = [
            test_inventory_drift,
            test_taggable_resources_exist_and_tagged,
            test_iam_roles_tagged,
            test_cognito_jwks,
            test_secrets_and_access,
            test_rds_spec,
            test_cost_no_nat,
        ]

    print(f"profile={PROFILE} region={REGION} account={ACCOUNT} "
          f"mode={'absent (T8)' if absent else 'present (T1)'}\n")

    failed = 0
    for fn in tests:
        try:
            fn()
        except AssertionError:
            failed += 1
        except Exception as exc:
            print(f"FAIL: {fn.__name__}: {exc}", file=sys.stderr)
            failed += 1

    if failed:
        print(f"\n{failed} test(s) failed", file=sys.stderr)
        return 1
    print(f"\nall {len(tests)} test(s) passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
