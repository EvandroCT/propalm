Steps To Populate data Folder
=============================

1. Download compressed file which stores the folder content
 
    `wget -c 'https://api.onedrive.com/v1.0/shares/u!aHR0cHM6Ly8xZHJ2Lm1zL3UvcyFBblUxNkM2cVBWc1hoRFctZG1XQVk2QWt6UDdL/root/content' -O data.tar.gz`
 
 2. Extract it 
 
    `tar xvf data.tar.gz`
 
 3. Remove compressed file
 
    `rm data.tar.gz`