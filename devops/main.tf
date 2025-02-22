module "app-dev-ctx" {
  source = "git::https://github.com/QualityUnit/idp.git//modules/app-dev-ctx?ref=main"
  # tflint-ignore: terraform_module_pinned_source #ToDo pin version to tag

  name      = "la-visitor-tracker"
  repo      = "LiveAgent-VisitorTracker"
  repo_path = trimprefix(abspath(path.root), dirname(dirname(abspath(path.module))))
}

module "ecr-repository" {
  source = "git::https://github.com/QualityUnit/idp.git//modules/ecr-public-repository?ref=main"
  # tflint-ignore: terraform_module_pinned_source #ToDo pin version to tag

  image       = "app"
  app_dev_ctx = module.app-dev-ctx
  providers   = {
    aws.shared-ue1 = aws.shared-ue1
  }
}
