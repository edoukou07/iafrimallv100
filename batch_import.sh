#!/bin/bash

# Batch import example products
# Usage: bash batch_import.sh

set -e

API_URL="${API_URL:-http://localhost:8000}"

echo "Starting batch product import..."

# Example products
products=(
  '{
    "id": "prod_001",
    "name": "Red Cotton T-Shirt",
    "description": "Classic red cotton t-shirt, comfortable and durable",
    "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500",
    "category": "clothing",
    "price": 29.99,
    "attributes": {"color": "red", "size": "M", "material": "cotton"}
  }'
  '{
    "id": "prod_002",
    "name": "Blue Jeans",
    "description": "Premium blue denim jeans",
    "image_url": "https://images.unsplash.com/photo-1542272604-787c62d465d1?w=500",
    "category": "clothing",
    "price": 59.99,
    "attributes": {"color": "blue", "size": "32", "material": "denim"}
  }'
  '{
    "id": "prod_003",
    "name": "Black Leather Shoes",
    "description": "Elegant black leather shoes for any occasion",
    "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500",
    "category": "shoes",
    "price": 89.99,
    "attributes": {"color": "black", "size": "10", "material": "leather"}
  }'
  '{
    "id": "prod_004",
    "name": "White Sneakers",
    "description": "Comfortable white sneakers for daily wear",
    "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500",
    "category": "shoes",
    "price": 49.99,
    "attributes": {"color": "white", "size": "10", "material": "canvas"}
  }'
  '{
    "id": "prod_005",
    "name": "Summer Dress",
    "description": "Lightweight floral summer dress",
    "image_url": "https://images.unsplash.com/photo-1595777707802-08e80f7a4e0e?w=500",
    "category": "clothing",
    "price": 39.99,
    "attributes": {"color": "floral", "size": "S", "material": "cotton"}
  }'
)

# Import each product
for product in "${products[@]}"; do
  echo "Importing product..."
  curl -s -X POST "$API_URL/api/v1/index-product" \
    -H "Content-Type: application/json" \
    -d "$product" | jq .
  echo ""
  sleep 2  # Wait between requests
done

echo "Batch import completed!"
