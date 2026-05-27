package cloud.compliance

import rego.v1

resources := object.get(input, "resource_changes", [])

active_resource(resource) if {
	some i
	resource := resources[i]
	not is_delete_action(resource)
}

is_delete_action(resource) if {
	actions := object.get(object.get(resource, "change", {}), "actions", [])
	actions[_] == "delete"
}

resource_after(resource) := value if {
	value := object.get(object.get(resource, "change", {}), "after", {})
}

resource_exists(resource_type) if {
	active_resource(resource)
	resource.type == resource_type
}

resource_has_tag(resource_type, tag_key) if {
	active_resource(resource)
	resource.type == resource_type
	after_value := resource_after(resource)
	tags := object.get(after_value, "tags", {})
	tags[tag_key]
}

# --------------------------------------------------------------------
# S3 Controls
# --------------------------------------------------------------------

s3_public_block_enabled if {
	active_resource(resource)
	resource.type == "aws_s3_bucket_public_access_block"
	after_value := resource_after(resource)

	object.get(after_value, "block_public_acls", false) == true
	object.get(after_value, "block_public_policy", false) == true
	object.get(after_value, "ignore_public_acls", false) == true
	object.get(after_value, "restrict_public_buckets", false) == true
}

s3_encrypted if {
	resource_exists("aws_s3_bucket_server_side_encryption_configuration")
}

s3_versioning_enabled if {
	active_resource(resource)
	resource.type == "aws_s3_bucket_versioning"
	after_value := resource_after(resource)

	config := object.get(after_value, "versioning_configuration", [])
	config[_].status == "Enabled"
}

s3_logging_enabled if {
	resource_exists("aws_s3_bucket_logging")
}

s3_confidential_tag_present if {
	resource_has_tag("aws_s3_bucket", "Confidentiality")
}

# --------------------------------------------------------------------
# KMS Controls
# --------------------------------------------------------------------

kms_key_rotation_enabled if {
	active_resource(resource)
	resource.type == "aws_kms_key"
	after_value := resource_after(resource)

	object.get(after_value, "enable_key_rotation", false) == true
}

# --------------------------------------------------------------------
# IAM Controls
# --------------------------------------------------------------------

iam_role_exists if {
	resource_exists("aws_iam_role")
}

iam_instance_profile_exists if {
	resource_exists("aws_iam_instance_profile")
}

iam_no_admin_policy if {
	not iam_admin_policy_detected
}

iam_admin_policy_detected if {
	active_resource(resource)
	resource.type == "aws_iam_policy"
	after_value := resource_after(resource)

	policy := object.get(after_value, "policy", "")
	contains(policy, "\"Action\":\"*\"")
	contains(policy, "\"Resource\":\"*\"")
}

iam_admin_policy_detected if {
	active_resource(resource)
	resource.type == "aws_iam_policy"
	after_value := resource_after(resource)

	policy := object.get(after_value, "policy", "")
	contains(policy, "\"Action\": \"*\"")
	contains(policy, "\"Resource\": \"*\"")
}

# --------------------------------------------------------------------
# Logging and Monitoring Controls
# --------------------------------------------------------------------

cloudtrail_enabled if {
	resource_exists("aws_cloudtrail")
}

cloudtrail_multi_region_enabled if {
	active_resource(resource)
	resource.type == "aws_cloudtrail"
	after_value := resource_after(resource)

	object.get(after_value, "is_multi_region_trail", false) == true
}

cloudtrail_log_validation_enabled if {
	active_resource(resource)
	resource.type == "aws_cloudtrail"
	after_value := resource_after(resource)

	object.get(after_value, "enable_log_file_validation", false) == true
}

guardduty_enabled if {
	active_resource(resource)
	resource.type == "aws_guardduty_detector"
	after_value := resource_after(resource)

	object.get(after_value, "enable", true) == true
}

vpc_flow_logs_enabled if {
	resource_exists("aws_flow_log")
}

cloudwatch_log_retention_90_days if {
	active_resource(resource)
	resource.type == "aws_cloudwatch_log_group"
	after_value := resource_after(resource)

	object.get(after_value, "retention_in_days", 0) >= 90
}

cloudwatch_logs_encrypted if {
	active_resource(resource)
	resource.type == "aws_cloudwatch_log_group"
	after_value := resource_after(resource)

	object.get(after_value, "kms_key_id", "") != ""
}

# --------------------------------------------------------------------
# Backup Controls
# --------------------------------------------------------------------

backup_plan_exists if {
	resource_exists("aws_backup_plan")
}

backup_vault_encrypted if {
	active_resource(resource)
	resource.type == "aws_backup_vault"
	after_value := resource_after(resource)

	object.get(after_value, "kms_key_arn", "") != ""
}

# --------------------------------------------------------------------
# EC2 Controls
# --------------------------------------------------------------------

ec2_no_public_ip if {
	not ec2_public_ip_detected
}

ec2_public_ip_detected if {
	active_resource(resource)
	resource.type == "aws_instance"
	after_value := resource_after(resource)

	object.get(after_value, "associate_public_ip_address", false) == true
}

ec2_imdsv2_required if {
	active_resource(resource)
	resource.type == "aws_instance"
	after_value := resource_after(resource)

	metadata_options := object.get(after_value, "metadata_options", [])
	metadata_options[_].http_tokens == "required"
}

ec2_ebs_encrypted if {
	active_resource(resource)
	resource.type == "aws_instance"
	after_value := resource_after(resource)

	root_block_device := object.get(after_value, "root_block_device", [])
	root_block_device[_].encrypted == true
}

# --------------------------------------------------------------------
# Network Controls
# --------------------------------------------------------------------

security_group_no_ssh_world if {
	not sg_ingress_open_to_world("tcp", 22)
}

security_group_no_rdp_world if {
	not sg_ingress_open_to_world("tcp", 3389)
}

sg_ingress_open_to_world(protocol_name, port_number) if {
	active_resource(resource)
	resource.type == "aws_security_group"
	after_value := resource_after(resource)

	ingress_rules := object.get(after_value, "ingress", [])
	rule := ingress_rules[_]

	object.get(rule, "protocol", "") == protocol_name
	object.get(rule, "from_port", 0) <= port_number
	object.get(rule, "to_port", 0) >= port_number

	cidrs := object.get(rule, "cidr_blocks", [])
	cidrs[_] == "0.0.0.0/0"
}

private_subnet_no_public_ip_mapping if {
	not subnet_public_ip_mapping_detected
}

subnet_public_ip_mapping_detected if {
	active_resource(resource)
	resource.type == "aws_subnet"
	after_value := resource_after(resource)

	object.get(after_value, "map_public_ip_on_launch", false) == true
}

restricted_egress_only_https if {
	not unrestricted_non_https_egress_detected
}

unrestricted_non_https_egress_detected if {
	active_resource(resource)
	resource.type == "aws_security_group"
	after_value := resource_after(resource)

	egress_rules := object.get(after_value, "egress", [])
	rule := egress_rules[_]

	cidrs := object.get(rule, "cidr_blocks", [])
	cidrs[_] == "0.0.0.0/0"

	not https_only_egress(rule)
}

https_only_egress(rule) if {
	object.get(rule, "protocol", "") == "tcp"
	object.get(rule, "from_port", 0) == 443
	object.get(rule, "to_port", 0) == 443
}

# --------------------------------------------------------------------
# Tagging / Governance Controls
# --------------------------------------------------------------------

required_tags_present if {
	environment_tag_present
	owner_tag_present
	project_tag_present
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
