Commands to change project:
 
 * `gcloud config set core/project web-crawlers-forklifts`
 * `gcloud config set core/project web-crawlers-forklifts-demo`


Commands to deploy to dev:
 
 * `gcloud beta functions deploy crawl_manuvic --env-vars-file env.dev.yaml --memory=128MB --runtime python37 --trigger-http`
 * `gcloud beta functions deploy crawl_smforklift --env-vars-file env.dev.yaml --memory=128MB --runtime python37 --trigger-http`
 * `gcloud beta functions deploy crawl_valleesaintsauveur --env-vars-file env.dev.yaml --memory=128MB --runtime python37 --trigger-http`
 * `gcloud beta functions deploy crawl_a1machinery --env-vars-file env.dev.yaml --memory=128MB --runtime python37 --trigger-http`
 * `gcloud beta functions deploy crawl_ceqinc --env-vars-file env.dev.yaml --memory=128MB --runtime python37 --trigger-http`
 * `gcloud beta functions deploy crawl_gregorypoolelift --env-vars-file env.dev.yaml --memory=128MB --runtime python37 --trigger-http`
 * `gcloud beta functions deploy crawl_southeastforklifts --env-vars-file env.dev.yaml --memory=128MB --runtime python37 --trigger-http`
 * `gcloud beta functions deploy find_new_forklift_websites --env-vars-file env.dev.yaml --memory=128MB --runtime python37 --trigger-http`

Commands to deploy to prod:

 * `gcloud beta functions deploy crawl_manuvic --env-vars-file env.prod.yaml --memory=128MB --runtime python37 --trigger-http`
 * `gcloud beta functions deploy crawl_smforklift --env-vars-file env.prod.yaml --memory=128MB --runtime python37 --trigger-http`
 * `gcloud beta functions deploy crawl_valleesaintsauveur --env-vars-file env.prod.yaml --memory=128MB --runtime python37 --trigger-http`
 * `gcloud beta functions deploy crawl_a1machinery --env-vars-file env.prod.yaml --memory=128MB --runtime python37 --trigger-http`
 * `gcloud beta functions deploy crawl_ceqinc --env-vars-file env.prod.yaml --memory=128MB --runtime python37 --trigger-http`
 * `gcloud beta functions deploy crawl_gregorypoolelift --env-vars-file env.prod.yaml --memory=128MB --runtime python37 --trigger-http`
 * `gcloud beta functions deploy crawl_southeastforklifts --env-vars-file env.prod.yaml --memory=128MB --runtime python37 --trigger-http`
 * `gcloud beta functions deploy find_new_forklift_websites --env-vars-file env.prod.yaml --memory=128MB --runtime python37 --trigger-http`
