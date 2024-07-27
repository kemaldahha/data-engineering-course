terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.38.0"
    }
  }
}

provider "google" {
  credentials = "./keys/my-creds.json"
  project     = "dtc-de-course-430705"
  region      = "us-central1"
}

resource "google_storage_bucket" "demo-bucket" {
  name          = "dtc-de-course-430705-terra-bucket"
  location      = "US"
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}