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

data "azurerm_resource_group" "rg" {
  name = "academy-2021"
}


resource "azurerm_storage_account" "storage" {
  name                = "pspassengerkiosk"
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = data.azurerm_resource_group.rg.location
    account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    Owner   = "Philipp Schmalen"
    DueDate = "2022-03-01"
  }
}
