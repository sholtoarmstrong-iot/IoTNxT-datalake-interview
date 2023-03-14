# IoT.NxT Navigator Interview Template
## Introduction
You are tasked to create a backed for a very simplistic datalake. That datalake should allow users to upload files and get statistics on columns in the uploaded files. THe user will periodically want to run jobs to optimise the stored files and potentially remove old files. The datalake is required to store the data as raw files on the disk (Note the data does not need to remain in the original format and is preferable if it doesn't). 
## Tasks
1) Fork this repo into a github repo of your own
2) Setup your development environment and run the test code (You should have access to a swagger page located on http://localhost:8002/api/swagger)
3) Fill in the relevant TODO's located in lib/api/datalake.py
4) Create a unit tests directory and perform unit tests on the developed api
5) Complete the dockerfile
6) Complete the deployment pod