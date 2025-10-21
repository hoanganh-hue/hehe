# GIẢI PHÁP: CERTBOT KHÔNG KHỞI CHẠY

## VẤN ĐỀ

Container ID: `0fa3f83b1cf320cc34e639f847dcfb5b8930bb4a089f9f0f792a3f5993bda3f0`  
Container Name: **certbot**  
Status: **Exited (1)** - Không thể khởi chạy  

## NGUYÊN NHÂN

### Certbot đang cố obtain SSL certificate từ Let's Encrypt:

```
Command: certonly --webroot --webroot-path=/var/www/certbot 
         --email ${SSL_EMAIL} --agree-tos --no-eff-email 
         -d zalopaymerchan.com -d www.zalopaymerchan.com
```

### Lỗi xảy ra:

```
Domain: zalopaymerchan.com
Type: unauthorized
Detail: 221.120.163.129: Invalid response from 
        http://zalopaymerchan.com/.well-known/acme-challenge/...: 404

Hint: The Certificate Authority failed to download 
      the temporary challenge files
```

### Tại sao fail?

```
1. Đây là LOCAL DEVELOPMENT machine (IP: 192.168.110.191)
2. Domain zalopaymerchan.com trỏ đến PRODUCTION server (IP: 221.120.163.129)
3. Let's Encrypt cố verify domain qua internet
4. Request đi đến production server (221.120.163.129), không phải local
5. Challenge file không tìm thấy → 404 error
6. Certification failed → Container exit (1)
```

## HIỂU VỀ CERTBOT

### Certbot là gì?

- **ONE-TIME SERVICE** để obtain SSL certificates
- Không phải long-running service
- Chạy một lần, obtain cert, rồi exit

### Khi nào Certbot thành công?

**Certbot chỉ thành công KHI:**

✅ Domain accessible từ internet  
✅ Domain trỏ đến đúng server đang chạy Certbot  
✅ Nginx serving `/.well-known/acme-challenge/`  
✅ Firewall allow port 80  
✅ DNS đã propagate  

### Tại sao local development fail?

❌ Domain trỏ đến production server khác  
❌ Let's Encrypt không thể verify từ local  
❌ Challenge file không accessible từ internet  

## GIẢI PHÁP

### 🔧 Option 1: DISABLE Certbot cho Local Development (KHUYẾN NGHỊ)

**Lý do:**
- Local development **không cần SSL certificate**
- Sử dụng HTTP (localhost) là đủ
- Tránh spam Let's Encrypt với failed requests

**Cách 1: Comment out trong docker-compose.yml**

```yaml
# docker-compose.yml

# Comment out certbot service for local dev
#  certbot:
#    image: certbot/certbot
#    container_name: certbot
#    restart: "no"
#    volumes:
#      - certbot_conf:/etc/letsencrypt
#      - certbot_www:/var/www/certbot
#    command: certonly --webroot --webroot-path=/var/www/certbot --email ${SSL_EMAIL} --agree-tos --no-eff-email -d ${DOMAIN} -d www.${DOMAIN}
#    networks:
#      - frontend_network
```

**Sau đó rebuild:**
```bash
docker-compose down
docker-compose up -d
```

**Cách 2: Sử dụng override file**

Tạo `docker-compose.override.yml`:
```yaml
version: '3.8'

# Override for local development
# This file disables certbot service

services:
  certbot:
    deploy:
      replicas: 0  # Don't run this service
```

**Cách 3: Profile-based (Khuyến nghị nhất)**

Sửa `docker-compose.yml`:
```yaml
certbot:
  image: certbot/certbot
  container_name: certbot
  restart: "no"
  profiles:
    - production  # Only run in production
  volumes:
    - certbot_conf:/etc/letsencrypt
    - certbot_www:/var/www/certbot
  command: certonly --webroot --webroot-path=/var/www/certbot --email ${SSL_EMAIL} --agree-tos --no-eff-email -d ${DOMAIN} -d www.${DOMAIN}
  networks:
    - frontend_network
```

**Chạy local (không có certbot):**
```bash
docker-compose up -d
```

**Chạy production (có certbot):**
```bash
docker-compose --profile production up -d
```

---

### 🚀 Option 2: GIỮ Certbot nhưng ACCEPT Failed Status

**Lý do:**
- Container exit (1) là EXPECTED cho local dev
- Không ảnh hưởng đến functionality
- Sẵn sàng cho production

**Action:**
- ✅ Không làm gì
- ✅ Accept status "Exited (1)"
- ✅ Certbot sẽ work khi deploy production

**Impact:**
- Zero impact on system
- All core services working
- Certbot ready for production

---

### 🌐 Option 3: DEPLOY LÊN PRODUCTION để Certbot Thành Công

**Điều kiện:**
- ✅ Server có IP public: 221.120.163.129
- ✅ Domain trỏ đến server đó
- ✅ Nginx đã configure /.well-known/acme-challenge/
- ✅ Firewall allow port 80 & 443

**Steps:**

1. **Transfer files lên production server:**
```bash
# Trên local machine
.\transfer-to-production.ps1
```

2. **Trên production server, chạy deployment script:**
```bash
# SSH vào server 221.120.163.129
ssh user@221.120.163.129

# Navigate to project
cd /opt/zalopay_phishing_platform

# Run deployment
chmod +x deploy-to-production.sh
./deploy-to-production.sh
```

3. **Script sẽ tự động:**
- ✅ Start Nginx (HTTP mode)
- ✅ Run Certbot to obtain SSL
- ✅ Certificates saved to `/etc/letsencrypt/`
- ✅ Enable HTTPS configuration
- ✅ Reload Nginx with SSL

4. **Kết quả:**
```
✓ SSL certificate obtained successfully
✓ HTTPS enabled at https://zalopaymerchan.com
✓ Auto-renewal configured
✓ Certbot status: Success
```

---

## KHUYẾN NGHỊ

### ✅ CHO LOCAL DEVELOPMENT

**Sử dụng Option 1 - Cách 3 (Profile-based):**

1. Thêm `profiles: [production]` vào certbot service
2. Local dev: `docker-compose up -d` (no certbot)
3. Production: `docker-compose --profile production up -d`

**Hoặc Option 2 - Accept failed status:**

1. Không làm gì
2. Accept certbot status "Exited (1)"
3. Hệ thống vẫn 100% functional

### ✅ CHO PRODUCTION DEPLOYMENT

**Deploy lên server 221.120.163.129:**

1. Use automated script: `deploy-to-production.sh`
2. Certbot sẽ obtain SSL tự động
3. HTTPS enabled
4. Auto-renewal configured

---

## IMPLEMENTATION

### CÁCH NHANH NHẤT: Disable Certbot cho Local

```bash
# Stop all containers
docker-compose down

# Thêm profiles vào docker-compose.yml
# (xem code below)

# Start lại (không có certbot)
docker-compose up -d

# Verify
docker-compose ps
# → certbot không hiện trong list
```

### Code để thêm profile:

```yaml
# docker-compose.yml
# Tìm section certbot và thêm profiles:

certbot:
  image: certbot/certbot
  container_name: certbot
  restart: "no"
  profiles:
    - production  # ADD THIS LINE
  volumes:
    - certbot_conf:/etc/letsencrypt
    - certbot_www:/var/www/certbot
  command: certonly --webroot --webroot-path=/var/www/certbot --email ${SSL_EMAIL} --agree-tos --no-eff-email -d ${DOMAIN} -d www.${DOMAIN}
  networks:
    - frontend_network
```

---

## VERIFICATION

### Sau khi disable certbot:

```bash
# Kiểm tra services
docker-compose ps

# Expected output:
# - backend: Up (healthy)
# - frontend: Up (healthy)
# - nginx: Up (healthy)
# - mongodb-primary: Up (healthy)
# - mongodb-secondary-1: Up
# - mongodb-secondary-2: Up
# - redis-primary: Up (healthy)
# - redis-replica: Up
# - influxdb: Up (healthy)
# - certbot: NOT LISTED (disabled)

# Test functionality
curl http://localhost/health
# → healthy

curl http://localhost:8000/health
# → {"status":"healthy"}
```

---

## TÓM TẮT

```
╔══════════════════════════════════════════════════════╗
║  CERTBOT KHÔNG KHỞI CHẠY - GIẢI PHÁP                 ║
╚══════════════════════════════════════════════════════╝

NGUYÊN NHÂN:
  - Certbot cố obtain SSL certificate
  - Fail vì đây là LOCAL DEVELOPMENT
  - Domain trỏ đến production server khác
  - Exit (1) là EXPECTED

GIẢI PHÁP:

Option 1: DISABLE cho local (KHUYẾN NGHỊ)
  → Thêm profiles: [production]
  → Local không chạy certbot
  → Production sẽ chạy certbot

Option 2: ACCEPT failed status
  → Không làm gì
  → Certbot failed là normal cho local
  → Zero impact on system

Option 3: DEPLOY production
  → Deploy lên server 221.120.163.129
  → Certbot sẽ thành công
  → HTTPS enabled

KHUYẾN NGHỊ:
  ✓ Local: Use Option 1 (disable certbot)
  ✓ Production: Use Option 3 (deploy script)
  ✓ Quick fix: Use Option 2 (accept failed)
```

---

## NEXT STEPS

### Nếu muốn fix ngay:

1. **Add profile to certbot** (5 seconds)
2. **Restart containers** (30 seconds)
3. **Verify** (10 seconds)

### Nếu muốn deploy production:

1. **Transfer files** (5 minutes)
2. **Run deployment script** (10 minutes)
3. **SSL obtained automatically** (2 minutes)
4. **HTTPS working** ✓

---

**Document Created:** 2025-10-20  
**Issue:** Certbot container không khởi chạy (Exit 1)  
**Status:** ✅ Solution provided  
**Impact:** Zero (system 100% functional without certbot on local)

