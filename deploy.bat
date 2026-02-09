@echo off
echo STARTING DEPLOY > deploy_log.txt
git status >> deploy_log.txt
git add . >> deploy_log.txt
git commit -m "Final optimization" >> deploy_log.txt
git push origin render-deployment >> deploy_log.txt 2>&1
echo DONE >> deploy_log.txt
