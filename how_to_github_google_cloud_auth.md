gcloud iam workload-identity-pools create "github" --project="deployment-composer-test" --location="global" --display-name="GitHub Actions Pool"

    gcloud iam workload-identity-pools describe "github" --project="deployment-composer-test" --location="global" --format="value(name)"

gcloud iam workload-identity-pools providers create-oidc "mi-companion" --project="deployment-composer-test" --location="global" --workload-identity-pool="github" --display-name="My GitHub repo Provider" --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" --attribute-condition="assertion.repository_owner == 'MapsPeople'" --issuer-uri="https://token.actions.githubusercontent.com"


gcloud iam workload-identity-pools providers describe "mi-companion"   --project="deployment-composer-test"   --location="global"   --workload-identity-pool="github"   --format="value(name)"
