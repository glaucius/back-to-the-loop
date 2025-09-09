#!/bin/bash
docker build backoffice/ -t tcc-backoffice:latest --no-cache
docker compose restart backoffice