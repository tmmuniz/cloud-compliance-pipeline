package cloud.compliance

import rego.v1

resources := object.get(input, "resource_changes", [])

active_resources := [r |
	some i
	r := resources[i]
	not is_delete_action(r)
]

is_delete_action(r) if {
	actions := object.get(object.get(r, "change", {}), "actions", [])
	actions[_] == "delete"
}

resource_after(r) := value if {
	value := object.get(object.get(r, "change", {}), "after", {})
}

resource_exists(resource_type) if {
	r := active_resources[_]
	r.type == resource_type
}

resource_has_tag(resource_type, tag_key) if {
	r := active_resources[_]
	r.type == resource_type
	after_value := resource_after(r)
	tags := object.get(after_value, "tags", {})
	tags[tag_key]
}

# --------------------------------------------------------------------
# S3 Controls
# --------------------------------------------------------------------

s3_public_block_enabled if {
	r := active_resources[_]
	r.type == "aws_s3_bucket_public_access_block"
	after_value := resource_after(r)
	object.get(after_value, "block_public_acls", false) == true
	object.get(after_value, "block_public_policy", false) == true
	object.get(after_value, "ignore_public_acls", false) == true
	object.get(after_value, "restrict_public_buckets", false) == true
}

s3_encrypted if {
	resource_exists("aws_s3_bucket_server_side_encryption_configuration")
}

s3_bucket_key_enabled if {
	r := active_resources[_]
	r.type == "aws_s3_bucket_server_side_encryption_configuration"
	after_value := resource_after(r)
	rules := object.get(after_value, "rule", [])
	rule := rules[_]
	apply := object.get(rule, "apply_server_side_encryption_by_default", [])
	count(apply) > 0
	object.get(rule, "bucket_key_enabled", false) == true
}

s3_versioning_enabled if {
	r := active_resources[_]
	r.type == "aws_s3_bucket_versioning"
	after_value := resource_after(r)
	config := object.get(after_value, "versioning_configuration", [])
	config[_].status == "Enabled"
}

s3_logging_enabled if {
	resource_exists("aws_s3_bucket_logging")
}

s3_object_lock_enabled if {
	resource_exists("aws_s3_bucket_object_lock_configuration")
}

s3_confidential_tag_present if {
	resource_has_tag("aws_s3_bucket", "Confidentiality")
}

# --------------------------------------------------------------------
# KMS / Secrets Controls
# --------------------------------------------------------------------

kms_key_rotation_enabled if {
	r := active_resources[_]
	r.type == "aws_kms_key"
	after_value := resource_after(r)
	object.get(after_value, "enable_key_rotation", false) == true
}

secrets_manager_secret_encrypted if {
	r := active_resources[_]
	r.type == "aws_secretsmanager_secret"
	after_value := resource_after(r)
	object.get(after_value, "kms_key_id", "") != ""
}

secrets_manager_rotation_enabled if {
	resource_exists("aws_secretsmanager_secret_rotation")
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
	r := active_resources[_]
	r.type == "aws_iam_policy"
	after_value := resource_after(r)
	policy := object.get(after_value, "policy", "")
	contains(policy, "\"Action\":\"*\"")
	contains(policy, "\"Resource\":\"*\"")
}

iam_admin_policy_detected if {
	r := active_resources[_]
	r.type == "aws_iam_policy"
	after_value := resource_after(r)
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
	r := active_resources[_]
	r.type == "aws_cloudtrail"
	after_value := resource_after(r)
	object.get(after_value, "is_multi_region_trail", false) == true
}

cloudtrail_log_validation_enabled if {
	r := active_resources[_]
	r.type == "aws_cloudtrail"
	after_value := resource_after(r)
	object.get(after_value, "enable_log_file_validation", false) == true
}

cloudtrail_kms_encrypted if {
	r := active_resources[_]
	r.type == "aws_cloudtrail"
	after_value := resource_after(r)
	object.get(after_value, "kms_key_id", "") != ""
}

guardduty_enabled if {
	r := active_resources[_]
	r.type == "aws_guardduty_detector"
	after_value := resource_after(r)
	object.get(after_value, "enable", true) == true
}

config_recorder_enabled if {
	resource_exists("aws_config_configuration_recorder")
}

vpc_flow_logs_enabled if {
	resource_exists("aws_flow_log")
}

cloudwatch_log_retention_90_days if {
	r := active_resources[_]
	r.type == "aws_cloudwatch_log_group"
	after_value := resource_after(r)
	object.get(after_value, "retention_in_days", 0) >= 90
}

cloudwatch_logs_encrypted if {
	r := active_resources[_]
	r.type == "aws_cloudwatch_log_group"
	after_value := resource_after(r)
	object.get(after_value, "kms_key_id", "") != ""
}

# --------------------------------------------------------------------
# Backup Controls
# --------------------------------------------------------------------

backup_plan_exists if {
	resource_exists("aws_backup_plan")
}

backup_vault_encrypted if {
	r := active_resources[_]
	r.type == "aws_backup_vault"
	after_value := resource_after(r)
	object.get(after_value, "kms_key_arn", "") != ""
}

# --------------------------------------------------------------------
# EC2 / Network Controls
# --------------------------------------------------------------------

ec2_no_public_ip if {
	not ec2_public_ip_detected
}

ec2_public_ip_detected if {
	r := active_resources[_]
	r.type == "aws_instance"
	after_value := resource_after(r)
	object.get(after_value, "associate_public_ip_address", false) == true
}

ec2_imdsv2_required if {
	r := active_resources[_]
	r.type == "aws_instance"
	after_value := resource_after(r)
	metadata_options := object.get(after_value, "metadata_options", [])
	metadata_options[_].http_tokens == "required"
}

ec2_ebs_encrypted if {
	r := active_resources[_]
	r.type == "aws_instance"
	after_value := resource_after(r)
	root_block_device := object.get(after_value, "root_block_device", [])
	root_block_device[_].encrypted == true
}

security_group_no_ssh_world if {
	not sg_ingress_open_to_world("tcp", 22)
}

security_group_no_rdp_world if {
	not sg_ingress_open_to_world("tcp", 3389)
}

sg_ingress_open_to_world(protocol_name, port_number) if {
	r := active_resources[_]
	r.type == "aws_security_group"
	after_value := resource_after(r)
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
	r := active_resources[_]
	r.type == "aws_subnet"
	after_value := resource_after(r)
	object.get(after_value, "map_public_ip_on_launch", false) == true
}

restricted_egress_only_https if {
	not unrestricted_non_https_egress_detected
}

unrestricted_non_https_egress_detected if {
	r := active_resources[_]
	r.type == "aws_security_group"
	after_value := resource_after(r)
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

alb_deletion_protection_enabled if {
	r := active_resources[_]
	r.type == "aws_lb"
	after_value := resource_after(r)
	object.get(after_value, "enable_deletion_protection", false) == true
}

lb_https_listener if {
	r := active_resources[_]
	r.type == "aws_lb_listener"
	after_value := resource_after(r)
	object.get(after_value, "port", 0) == 443
}

waf_web_acl_exists if {
	resource_exists("aws_wafv2_web_acl")
}

waf_associated_to_alb if {
	resource_exists("aws_wafv2_web_acl_association")
}

# --------------------------------------------------------------------
# API / Open Finance-oriented Controls
# --------------------------------------------------------------------

api_gateway_access_logs_enabled if {
	r := active_resources[_]
	r.type == "aws_api_gateway_stage"
	after_value := resource_after(r)
	access_log_settings := object.get(after_value, "access_log_settings", [])
	count(access_log_settings) > 0
}

api_gateway_access_logs_enabled if {
	r := active_resources[_]
	r.type == "aws_apigatewayv2_stage"
	after_value := resource_after(r)
	access_log_settings := object.get(after_value, "access_log_settings", [])
	count(access_log_settings) > 0
}

api_gateway_xray_enabled if {
	r := active_resources[_]
	r.type == "aws_api_gateway_stage"
	after_value := resource_after(r)
	object.get(after_value, "xray_tracing_enabled", false) == true
}

api_gateway_authorizer_configured if {
	resource_exists("aws_api_gateway_authorizer")
}

api_gateway_authorizer_configured if {
	resource_exists("aws_apigatewayv2_authorizer")
}

acm_certificate_exists if {
	resource_exists("aws_acm_certificate")
}

# --------------------------------------------------------------------
# Database / Container / Messaging Controls
# --------------------------------------------------------------------

rds_encrypted if {
	r := active_resources[_]
	r.type == "aws_db_instance"
	after_value := resource_after(r)
	object.get(after_value, "storage_encrypted", false) == true
}

rds_backup_retention_enabled if {
	r := active_resources[_]
	r.type == "aws_db_instance"
	after_value := resource_after(r)
	object.get(after_value, "backup_retention_period", 0) > 0
}

rds_deletion_protection_enabled if {
	r := active_resources[_]
	r.type == "aws_db_instance"
	after_value := resource_after(r)
	object.get(after_value, "deletion_protection", false) == true
}

ecr_scan_on_push_enabled if {
	r := active_resources[_]
	r.type == "aws_ecr_repository"
	after_value := resource_after(r)
	config := object.get(after_value, "image_scanning_configuration", [])
	config[_].scan_on_push == true
}

ecr_image_tag_immutable if {
	r := active_resources[_]
	r.type == "aws_ecr_repository"
	after_value := resource_after(r)
	object.get(after_value, "image_tag_mutability", "") == "IMMUTABLE"
}

sns_encrypted if {
	r := active_resources[_]
	r.type == "aws_sns_topic"
	after_value := resource_after(r)
	object.get(after_value, "kms_master_key_id", "") != ""
}

sqs_encrypted if {
	r := active_resources[_]
	r.type == "aws_sqs_queue"
	after_value := resource_after(r)
	object.get(after_value, "kms_master_key_id", "") != ""
}

sqs_encrypted if {
	r := active_resources[_]
	r.type == "aws_sqs_queue"
	after_value := resource_after(r)
	object.get(after_value, "sqs_managed_sse_enabled", false) == true
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
