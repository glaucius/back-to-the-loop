#!/bin/bash

echo "🚀 BTL - Setup Completo do Zero"
echo "================================"

# 1. Parar todos os serviços
echo "📦 Parando containers existentes..."
docker compose down

# 2. Remover volumes (reset completo)
echo "🗑️  Removendo volumes antigos..."
docker volume rm btl_mariadb_data btl_minio_data 2>/dev/null || true

# 3. Build da aplicação
echo "🔨 Construindo aplicação..."
echo "🔨 Construindo backoffice..."
docker build backoffice/ -t tcc-backoffice:latest --no-cache
echo "🔨 Construindo frontend..."
docker build frontend/ -t tcc-frontend:latest --no-cache

# 4. Iniciar serviços
echo "🚀 Iniciando todos os serviços..."
docker compose up -d

# 5. Aguardar MinIO ficar pronto
echo "⏳ Aguardando MinIO ficar pronto..."
sleep 10

# 6. Aguardar MariaDB ficar pronto
echo "⏳ Aguardando MariaDB ficar pronto..."
sleep 10

# 7. Aguardar aplicação inicializar
echo "⏳ Aguardando aplicação inicializar..."
sleep 15

echo ""
echo "✅ Setup concluído!"
echo ""
echo "🌐 Serviços disponíveis:"
echo "   Backoffice:  http://localhost:5555"
echo "   Frontend:  http://localhost:3000"
echo "   PhpMyAdmin:  http://localhost:8888"
echo "   MinIO:       http://localhost:9001"
echo ""
echo "🔑 Credenciais padrão:"
echo "   Admin: admin@btl.com / admin123"
echo "   MinIO: minioadmin / minioadmin123"
echo ""
echo ""
