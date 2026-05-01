# 🧠 AI Money Brain

> **AI-powered personal finance copilot with multi-bank CSV support, GPT-4 categorization, and intelligent spending insights.**

[![Backend Tests](https://github.com/MohammedAhmeduddin/ai-money-brain/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/MohammedAhmeduddin/ai-money-brain/actions/workflows/backend-tests.yml)
[![Release](https://img.shields.io/github/v/release/MohammedAhmeduddin/ai-money-brain?style=flat-square)](https://github.com/MohammedAhmeduddin/ai-money-brain/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg?style=flat-square&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-316192.svg?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-412991.svg?style=flat-square&logo=openai&logoColor=white)](https://openai.com/)

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Demo](#-demo)
- [Quick Start](#-quick-start)
- [Supported Banks](#-supported-banks)
- [API Documentation](#-api-documentation)
- [Tech Stack](#️-tech-stack)
- [Project Structure](#-project-structure)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)

---

## 🎯 Overview

**AI Money Brain** transforms bank transaction data into actionable financial intelligence. Unlike traditional finance apps that only show charts, we explain **why** your spending changed and tell you **what to do next**.

### The Problem We Solve

| Traditional Apps              | AI Money Brain                                                                                                                      |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| "You spent $2,340 this month" | "Your spending increased by $687 (22%). Food delivery jumped from $180 to $520 - mostly weekend orders. Here's how to save $300..." |
| Charts and graphs             | Plain English explanations with actionable insights                                                                                 |
| Manual categorization         | AI-powered automatic categorization                                                                                                 |
| Single bank support           | Universal CSV parser for any bank                                                                                                   |

---

## ✨ Features

### 🎯 v0.2.0 - Current Release

#### **🏦 Multi-Bank CSV Upload**

- ✅ **Universal CSV parser** - Works with any bank format
- ✅ **Tested with 5+ banks** - Chase, Wells Fargo, Capital One, Amex, Bank of America
- ✅ **Auto-column detection** - Intelligently maps 30+ column name patterns
- ✅ **Smart date parsing** - Handles 12+ date formats (US, EU, ISO)
- ✅ **Currency support** - $, €, £, and more

#### **🤖 AI-Powered Categorization**

- ✅ **GPT-4 integration** - Automatic transaction categorization
- ✅ **100% accuracy** on test data
- ✅ **13 categories** - Groceries, Dining, Transportation, Shopping, etc.
- ✅ **Merchant cleaning** - Removes payment processor prefixes (SQ*, TST*, UBER\*)
- ✅ **Subscription detection** - Automatically identifies recurring charges

#### **🔒 Secure Authentication**

- ✅ **JWT tokens** - 7-day expiry with refresh capability
- ✅ **Bcrypt hashing** - Industry-standard password security
- ✅ **Protected routes** - Bearer token authentication
- ✅ **Email validation** - Pydantic-based input validation

#### **💾 Transaction Management**

- ✅ **CRUD operations** - Create, Read, Update, Delete transactions
- ✅ **PostgreSQL storage** - Reliable and scalable
- ✅ **Pagination** - Handle thousands of transactions
- ✅ **Filtering** - By category, date range, merchant

#### **📊 Developer Experience**

- ✅ **Swagger UI** - Interactive API documentation
- ✅ **Docker support** - One-command database setup
- ✅ **Alembic migrations** - Version-controlled database schema
- ✅ **GitHub Actions CI** - Automated testing on every push
- ✅ **Professional Git workflow** - Semantic versioning and releases

---

## 🎬 Demo

### API Endpoints in Action

```bash
# 1. Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "name": "John Doe",
    "password": "password123"
  }'

# Response:
{
  "email": "john@example.com",
  "name": "John Doe",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-04-28T12:00:00Z"
}

# 2. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "password123"
  }'

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}

# 3. Upload CSV with AI categorization
curl -X POST http://localhost:8000/api/v1/transactions/upload \
  -H "Authorization: Bearer {token}" \
  -F "file=@transactions.csv"

# Response:
{
  "total_uploaded": 127,
  "total_categorized": 127,
  "status": "success",
  "message": "Successfully imported 127 transactions. 127 automatically categorized by AI."
}
```
