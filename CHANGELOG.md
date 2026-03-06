# ChangeLog
All notable changes to this project will be documented in this file.

## [v1.0] 
### Basic Features
- Agent run on the terminal with `console`
- It use DB to answer questions about Pattreeya
- It can speak only English 

## [v2.0] 
### Basic Features
- Multilanguage support with deepgram/nova-3
- TTS default is cartesian/sonic-3
- Add avatar support for Beyound Presence, Tavus and Simli.

## [v2.1] 
### Backward Fix
- The code break in between .. we retrieve it back. 
- This version should be version v1.x, backend + frontend work together on firefox.

## [v3.0] 
### Use JS/TS for backend
- Use JS/TS for backend
- Use Next.js for frontend
- Use docker for containerization for both backend and frontend
- Use docker-compose for orchestration
- Use docker volume for persistent storage
- Use docker network for communication between backend and frontend
- ** This version should make the agent run faster and more stable **
- Problem from previous version: We use Python for backend, it is slow and unstable for room connection, so we switch to JS/TS for backend. (Experimental)
