terraform {
  backend "azurerm" {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "sttfstatezerotrust"
    container_name       = "tfstate"
    key                  = "zero-trust.terraform.tfstate"
  }
}
