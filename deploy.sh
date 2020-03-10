#!/usr/bin/env bash

# Accepts `mode` as a startup argument

if [[ $1 == "dev" ]]; then
    PROJECT="web-crawlers-forklifts-demo"
    MODE=$1
elif [[ $1 == "prod" ]]; then
    PROJECT="web-crawlers-forklifts"
    MODE=$1
else
    echo "Set mode"
    exit
fi

echo "Setting project to ${PROJECT}"
gcloud config set core/project ${PROJECT}
echo "Deploying crawl_manuvic to ${MODE}"
gcloud beta functions deploy crawl_manuvic --env-vars-file env.${MODE}.yaml --runtime python37 --trigger-http
echo "Deploying crawl_smforklift to ${MODE}"
gcloud beta functions deploy crawl_smforklift --env-vars-file env.${MODE}.yaml --runtime python37 --trigger-http
echo "Deploying crawl_valleesaintsauveur to ${MODE}"
gcloud beta functions deploy crawl_valleesaintsauveur --env-vars-file env.${MODE}.yaml --runtime python37 --trigger-http
echo "Deploying crawl_a1machinery to ${MODE}"
gcloud beta functions deploy crawl_a1machinery --env-vars-file env.${MODE}.yaml --runtime python37 --trigger-http
echo "Deploying crawl_ceqinc to ${MODE}"
gcloud beta functions deploy crawl_ceqinc --env-vars-file env.${MODE}.yaml --runtime python37 --trigger-http
echo "Deploying crawl_gregorypoolelift to ${MODE}"
gcloud beta functions deploy crawl_gregorypoolelift --env-vars-file env.${MODE}.yaml --runtime python37 --trigger-http
echo "Deploying crawl_southeastforklifts to ${MODE}"
gcloud beta functions deploy crawl_southeastforklifts --env-vars-file env.${MODE}.yaml --runtime python37 --trigger-http
echo "Deploying find_new_forklift_websites to ${MODE}"
gcloud beta functions deploy find_new_forklift_websites --env-vars-file env.${MODE}.yaml --runtime python37 --trigger-http
