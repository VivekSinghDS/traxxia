To run the file, make sure to have the following key in your env

1. NEWSAPI_API_KEY=***
2. OPENAI_API_KEY="sk-**"

Then use docker commands as follows : 

`docker build -t simple-app:v1 .`

`docker run -it -p 8000:8000 simple-app:v1`

