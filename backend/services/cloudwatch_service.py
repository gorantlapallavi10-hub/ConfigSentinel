"""
AWS CloudWatch Integration
----------------------------
Fetches basic EC2 health/metric data for the dashboard:
  - CPU utilization
  - Instance status checks
  - (optional) memory utilization, if the CloudWatch Agent is installed
    on the instance and publishing the custom "CWAgent" namespace metric

This module is read-only: it only calls Get*/Describe* CloudWatch and
EC2 APIs, never anything that modifies infrastructure.
"""
from datetime import datetime, timedelta
from typing import Optional
from config import settings

try:
    import boto3
except ImportError:  # boto3 not installed in a pure-demo setup
    boto3 = None


def get_ec2_cpu_utilization(instance_id: str, minutes: int = 10) -> Optional[float]:
    """Returns the latest average CPU utilization percentage for an EC2 instance."""
    if boto3 is None or not instance_id:
        return None

    client = boto3.client("cloudwatch", region_name=settings.AWS_REGION)
    end = datetime.utcnow()
    start = end - timedelta(minutes=minutes)

    response = client.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
        StartTime=start,
        EndTime=end,
        Period=300,
        Statistics=["Average"],
    )
    datapoints = sorted(response.get("Datapoints", []), key=lambda d: d["Timestamp"])
    if not datapoints:
        return None
    return round(datapoints[-1]["Average"], 2)


def get_instance_status(instance_id: str) -> str:
    """Returns 'running', 'stopped', 'impaired', etc. via EC2 DescribeInstanceStatus."""
    if boto3 is None or not instance_id:
        return "unknown"

    ec2 = boto3.client("ec2", region_name=settings.AWS_REGION)
    resp = ec2.describe_instance_status(InstanceIds=[instance_id])
    statuses = resp.get("InstanceStatuses", [])
    if not statuses:
        return "unknown"
    return statuses[0]["InstanceState"]["Name"]


def get_memory_utilization(instance_id: str, minutes: int = 10) -> Optional[float]:
    """
    Reads the custom 'mem_used_percent' metric published by the CloudWatch
    Agent (namespace 'CWAgent'). Requires the agent to be configured on the
    EC2 instance; see terraform/ for the IAM role that permits this.
    """
    if boto3 is None or not instance_id:
        return None

    client = boto3.client("cloudwatch", region_name=settings.AWS_REGION)
    end = datetime.utcnow()
    start = end - timedelta(minutes=minutes)

    response = client.get_metric_statistics(
        Namespace="CWAgent",
        MetricName="mem_used_percent",
        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
        StartTime=start,
        EndTime=end,
        Period=300,
        Statistics=["Average"],
    )
    datapoints = sorted(response.get("Datapoints", []), key=lambda d: d["Timestamp"])
    if not datapoints:
        return None
    return round(datapoints[-1]["Average"], 2)
