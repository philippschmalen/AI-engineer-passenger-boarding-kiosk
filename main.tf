terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 2.94"
    }
  }

  required_version = ">= 1.1.4"
}

provider "azurerm" {
  features {}
}


# resource group
data "azurerm_resource_group" "rg" {
  name = "psaiengineer"
}


# storage
resource "azurerm_storage_account" "storage" {
  name                     = "pspassengerkiosk"
  resource_group_name      = data.azurerm_resource_group.rg.name
  location                 = data.azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  blob_properties{
    cors_rule{
        allowed_headers = ["*"]
        allowed_methods = ["GET","HEAD","POST","PUT"]
        allowed_origins = ["*"]
        exposed_headers = ["*"]
        max_age_in_seconds = 3600
      }
    }

  tags = {
    Owner   = "Philipp Schmalen"
    DueDate = "2022-03-01"
  }
}


# container: dvc
resource "azurerm_storage_container" "dvc" {
  name                  = "dvc"
  storage_account_name  = azurerm_storage_account.storage.name
  container_access_type = "private"
}


# container: data
resource "azurerm_storage_container" "data" {
  name                  = "data"
  storage_account_name  = azurerm_storage_account.storage.name
  container_access_type = "private"
}


# container: model
resource "azurerm_storage_container" "model" {
  name                  = "model"
  storage_account_name  = azurerm_storage_account.storage.name
  container_access_type = "private"
}


# upload data/raw to data/
resource "null_resource" "upload-data-raw" {
    provisioner "local-exec" {
        command = "az storage blob upload-batch --account-name ${azurerm_storage_account.storage.name} --destination ${azurerm_storage_container.data.name} --source data/raw"
        #
    }
}


# upload data/raw to data/
resource "null_resource" "upload-model" {
    provisioner "local-exec" {
        command = "az storage blob upload-batch --account-name ${azurerm_storage_account.storage.name} --destination ${azurerm_storage_container.model.name} --source data/model"
    }
}


# face recognition
resource "azurerm_cognitive_account" "ca-face" {
  name                = "pspassengerkiosk-face"
  location            = data.azurerm_resource_group.rg.location
  resource_group_name = data.azurerm_resource_group.rg.name
  kind                = "Face"

  sku_name = "S0"

  tags = {
    Owner   = "Philipp Schmalen"
    DueDate = "2022-03-01"
  }
}


# form recognition
resource "azurerm_cognitive_account" "ca-form" {
  name                = "pspassengerkiosk-form"
  location            = data.azurerm_resource_group.rg.location
  resource_group_name = data.azurerm_resource_group.rg.name
  kind                = "FormRecognizer"

  sku_name = "S0"

  tags = {
    Owner   = "Philipp Schmalen"
    DueDate = "2022-03-01"
  }
}


# cv recognition
resource "azurerm_cognitive_account" "ca-cv" {
  name                = "pspassengerkiosk-cv"
  location            = data.azurerm_resource_group.rg.location
  resource_group_name = data.azurerm_resource_group.rg.name
  kind                = "ComputerVision"

  sku_name = "S1"

  tags = {
    Owner   = "Philipp Schmalen"
    DueDate = "2022-03-01"
  }
}


# video analyzer
resource "azurerm_user_assigned_identity" "identity" {
  name                = "pspassengerkiosk-identity"
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = data.azurerm_resource_group.rg.location
}

resource "azurerm_role_assignment" "contributor" {
  scope                = azurerm_storage_account.storage.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.identity.principal_id
}

resource "azurerm_role_assignment" "reader" {
  scope                = azurerm_storage_account.storage.id
  role_definition_name = "Reader"
  principal_id         = azurerm_user_assigned_identity.identity.principal_id
}

resource "azurerm_video_analyzer" "ca-video" {
  name                = "pspassengerkioskvideo"
  location            = data.azurerm_resource_group.rg.location
  resource_group_name = data.azurerm_resource_group.rg.name

  storage_account {
    id                        = azurerm_storage_account.storage.id
    user_assigned_identity_id = azurerm_user_assigned_identity.identity.id
  }

  identity {
    type = "UserAssigned"
    identity_ids = [
      azurerm_user_assigned_identity.identity.id
    ]
  }

  tags = {
    environment = "staging"
  }

  depends_on = [
    azurerm_role_assignment.contributor,
    azurerm_role_assignment.reader,
  ]
}
