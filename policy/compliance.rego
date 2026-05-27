package cloud.compliance

resources := input.resource_changes

resource_exists(type) if {
  some i
  resources[i].type == type
  resources[i].change.actions[_] != "delete"
}

resource_after(type, after) if {
  some i
  resources[i].type == type
  resources[i].change.actions[_] != "delete"
  after := resources[i].change.after
}

resource_has_tag(type, tag) if {
  resource_after(type, after)
  after.tags[tag]
}

s3_public_block_enabled if {
  some i
  resources[i].type == "aws_s3_bucket_public_access_block"
  resources[i].change.actions[_] != "delete"
  after := resources[i].change.after
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
  after.versioning_configuration[_].status == "Enabled"
}

ec2_no_public_ip if {
  not ec2_has_public_ip
}

ec2_has_public_ip if {
  resource_after("aws_instance", after)
  after.associate_public_ip_address == true
}

security_group_no_ssh_world if {
  not sg_ingress_open_world(22)
}

security_group_no_rdp_world if {
  not sg_ingress_open_world(3389)
}

sg_ingress_open_world(port) if {
  resource_after("aws_security_group", after)
  rule := after.ingress[_]
  rule.from_port <= port
  rule.to_port >= port
  rule.cidr_blocks[_] == "0.0.0.0/0"
}

iam_no_admin_policy if {
  not iam_admin_policy
}

iam_admin_policy if {
  resource_after("aws_iam_policy", after)
  contains(after.policy, "\"Action\":\"*\"")
  contains(after.policy, "\"Resource\":\"*\"")
}

iam_admin_policy if {
  resource_after("aws_iam_policy", after)
  contains(after.policy, "\"Action\": [\"*\"]")
  contains(after.policy, "\"Resource\": [\"*\"]")
}

cloudtrail_enabled if {
  resource_exists("aws_cloudtrail")
}

guardduty_enabled if {
  resource_exists("aws_guardduty_detector")
}

vpc_flow_logs_enabled if {
  resource_exists("aws_flow_log")
}

kms_key_exists if {
  resource_exists("aws_kms_key")
}

backup_plan_exists if {
  resource_exists("aws_backup_plan")
}

required_tags_present if {
  resource_has_tag("aws_instance", "Environment")
  resource_has_tag("aws_instance", "Owner")
  resource_has_tag("aws_instance", "Project")
  resource_has_tag("aws_s3_bucket", "Environment")
  resource_has_tag("aws_s3_bucket", "Owner")
  resource_has_tag("aws_s3_bucket", "Project")
}
