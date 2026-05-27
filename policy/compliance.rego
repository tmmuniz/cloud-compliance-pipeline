package cloud.compliance

resources := object.get(input, "resource_changes", [])

resource_exists(type) if {
  some i
  resources[i].type == type
  resources[i].change.after != null
}

resource_after(type, after) if {
  some i
  resources[i].type == type
  resources[i].change.after != null
  after := resources[i].change.after
}

resource_has_tag(type, tag) if {
  resource_after(type, after)
  tags := object.get(after, "tags", {})
  tags[tag]
}

resource_has_tag(type, tag) if {
  resource_after(type, after)
  tags_all := object.get(after, "tags_all", {})
  tags_all[tag]
}

resource_tag_equals(type, tag, expected) if {
  resource_after(type, after)
  tags := object.get(after, "tags", {})
  tags[tag] == expected
}

resource_tag_equals(type, tag, expected) if {
  resource_after(type, after)
  tags_all := object.get(after, "tags_all", {})
  tags_all[tag] == expected
}

# Identity and access
iam_no_admin_policy if {
  not iam_admin_policy
}

iam_admin_policy if {
  resource_after("aws_iam_policy", after)
  policy := json.unmarshal(after.policy)
  statement := policy.Statement[_]
  wildcard_action(statement.Action)
  wildcard_resource(statement.Resource)
}

wildcard_action(action) if {
  action == "*"
}

wildcard_action(action) if {
  action[_] == "*"
}

wildcard_resource(resource) if {
  resource == "*"
}

wildcard_resource(resource) if {
  resource[_] == "*"
}

iam_role_exists if {
  resource_exists("aws_iam_role")
}

iam_instance_profile_exists if {
  resource_exists("aws_iam_instance_profile")
}

# S3 and data protection
s3_bucket_exists if {
  resource_exists("aws_s3_bucket")
}

s3_public_block_enabled if {
  resource_after("aws_s3_bucket_public_access_block", after)
  after.block_public_acls == true
  after.block_public_policy == true
  after.ignore_public_acls == true
  after.restrict_public_buckets == true
}

s3_encrypted if {
  resource_exists("aws_s3_bucket_server_side_encryption_configuration")
}

s3_versioning_enabled if {
  resource_after("aws_s3_bucket_versioning", after)
  after.versioning_configuration[0].status == "Enabled"
}

s3_logging_enabled if {
  resource_exists("aws_s3_bucket_logging")
}

s3_confidential_tag_present if {
  resource_has_tag("aws_s3_bucket", "DataClass")
}

# Encryption and key management
kms_key_exists if {
  resource_exists("aws_kms_key")
}

kms_key_rotation_enabled if {
  resource_after("aws_kms_key", after)
  after.enable_key_rotation == true
}

# Network security
ec2_no_public_ip if {
  not ec2_public_ip_enabled
}

ec2_public_ip_enabled if {
  resource_after("aws_instance", after)
  after.associate_public_ip_address == true
}

security_group_no_ssh_world if {
  not sg_ingress_open_to_world("tcp", 22)
}

security_group_no_rdp_world if {
  not sg_ingress_open_to_world("tcp", 3389)
}

security_group_no_all_ports_world if {
  not sg_all_ports_world
}

sg_all_ports_world if {
  resource_after("aws_security_group", after)
  rule := after.ingress[_]
  rule.from_port == 0
  rule.to_port == 0
  rule.cidr_blocks[_] == "0.0.0.0/0"
}

sg_ingress_open_to_world(protocol, port) if {
  resource_after("aws_security_group", after)
  rule := after.ingress[_]
  rule.protocol == protocol
  rule.from_port <= port
  rule.to_port >= port
  rule.cidr_blocks[_] == "0.0.0.0/0"
}

vpc_exists if {
  resource_exists("aws_vpc")
}

private_subnet_no_public_ip_mapping if {
  resource_after("aws_subnet", after)
  after.map_public_ip_on_launch == false
}

vpc_flow_logs_enabled if {
  resource_exists("aws_flow_log")
}

restricted_egress_only_https if {
  resource_after("aws_security_group", after)
  rule := after.egress[_]
  rule.from_port == 443
  rule.to_port == 443
  rule.protocol == "tcp"
}

# Monitoring, detection and audit
cloudtrail_enabled if {
  resource_exists("aws_cloudtrail")
}

cloudtrail_multi_region_enabled if {
  resource_after("aws_cloudtrail", after)
  after.is_multi_region_trail == true
}

cloudtrail_log_validation_enabled if {
  resource_after("aws_cloudtrail", after)
  after.enable_log_file_validation == true
}

cloudtrail_management_events_enabled if {
  resource_after("aws_cloudtrail", after)
  after.event_selector[0].include_management_events == true
}

guardduty_enabled if {
  resource_after("aws_guardduty_detector", after)
  after.enable == true
}

cloudwatch_log_group_exists if {
  resource_exists("aws_cloudwatch_log_group")
}

cloudwatch_log_retention_90_days if {
  resource_after("aws_cloudwatch_log_group", after)
  after.retention_in_days >= 90
}

cloudwatch_logs_encrypted if {
  resource_after("aws_cloudwatch_log_group", after)
  after.kms_key_id != ""
}

# Resilience and recovery
backup_plan_exists if {
  resource_exists("aws_backup_plan")
}

backup_vault_exists if {
  resource_exists("aws_backup_vault")
}

backup_vault_encrypted if {
  resource_after("aws_backup_vault", after)
  after.kms_key_arn != ""
}

# Compute hardening
ec2_imdsv2_required if {
  resource_after("aws_instance", after)
  after.metadata_options[0].http_tokens == "required"
}

ec2_ebs_encrypted if {
  resource_after("aws_instance", after)
  after.root_block_device[0].encrypted == true
}

ec2_detailed_monitoring_enabled if {
  resource_after("aws_instance", after)
  after.monitoring == true
}

# Governance and tagging
required_tags_present if {
  resource_has_tag("aws_instance", "Environment")
  resource_has_tag("aws_instance", "Owner")
  resource_has_tag("aws_instance", "Project")
  resource_has_tag("aws_s3_bucket", "Environment")
  resource_has_tag("aws_s3_bucket", "Owner")
  resource_has_tag("aws_s3_bucket", "Project")
}

environment_tag_present if {
  resource_has_tag("aws_instance", "Environment")
}

owner_tag_present if {
  resource_has_tag("aws_instance", "Owner")
}

project_tag_present if {
  resource_has_tag("aws_instance", "Project")
}

managed_by_terraform_tag_present if {
  resource_has_tag("aws_instance", "ManagedBy")
}
