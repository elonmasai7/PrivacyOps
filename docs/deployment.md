# Deployment Guide

## Container deployment

- Build with `docker compose build`
- Start with `docker compose up -d`

## Required production components

- Managed PostgreSQL
- Redis
- S3-compatible object storage for uploads/exports
- Email provider
- Monitoring and error tracking

## Secrets

- Store `JWT_SECRET`, database credentials, API tokens, and payment keys in a secrets manager.
