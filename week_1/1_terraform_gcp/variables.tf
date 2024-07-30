variable "credentials" {
    description = "My Credentials"
    default = "./keys/my-creds.json"
}

variable "project" {
    description = "Project Description"
    default = "dtc-de-course-430705"
}

variable "region" {
    description = "Region"
    default = "us-central1"
}

variable "location" {
    description = "Project Location"
    default = "US"
}

variable "bq_dataset_name" {
    description = "My BigQuery Dataset Name"
    default = "demo_dataset"
}

variable "gcs_bucket_name" {
    description = "My Storage Bucket Name"
    default = "dtc-de-course-430705-terra-bucket"
}

variable "gcs_storage_class" {
  description = "Bucket Storage Class"
  default = "STANDARD"
}
