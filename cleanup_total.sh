#!/bin/bash

echo "💥 BTL - LIMPEZA TOTAL DO SISTEMA"
echo "================================="
echo "⚠️  ATENÇÃO: Isso vai remover TUDO relacionado ao Docker!"
echo "   - Todos os containers"
echo "   - Todos os volumes"
echo "   - Todas as networks"
echo "   - Todo o cache de build"
echo "   - Todas as imagens não utilizadas"
echo ""

# Confirmação do usuário
read -p "🤔 Tem certeza que deseja continuar? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Operação cancelada."
    exit 1
fi

echo ""
echo "🚀 Iniciando limpeza total..."

# 1. Parar e remover todos os containers do projeto
echo "📦 1/7 - Parando containers do BTL..."
docker compose down -v 2>/dev/null || echo "   ⚠️  Nenhum container BTL encontrado"

# 2. Parar TODOS os containers em execução
echo "🛑 2/7 - Parando TODOS os containers..."
docker stop $(docker ps -aq) 2>/dev/null || echo "   ⚠️  Nenhum container em execução"

# 3. Remover TODOS os containers
echo "🗑️  3/7 - Removendo TODOS os containers..."
docker rm $(docker ps -aq) 2>/dev/null || echo "   ⚠️  Nenhum container para remover"

# 4. Remover TODOS os volumes
echo "💾 4/7 - Removendo TODOS os volumes..."
docker volume prune -f
echo "   📁 Removendo volumes nomeados do BTL..."
docker volume rm btl_mariadb_data btl_minio_data 2>/dev/null || echo "   ⚠️  Volumes BTL já removidos"

# 5. Remover TODAS as networks
echo "🌐 5/7 - Removendo TODAS as networks..."
docker network prune -f

# 6. Remover TODAS as imagens não utilizadas
echo "🖼️  6/7 - Removendo imagens não utilizadas..."
docker image prune -af

# 7. Limpar cache de build
echo "🔧 7/7 - Limpando cache de build..."
docker system prune -af

echo ""
echo "✅ LIMPEZA TOTAL CONCLUÍDA!"
echo ""
echo "📊 Espaço liberado:"
docker system df
echo ""
echo "🎯 Para recriar tudo do zero, execute:"
echo "   ./setup_fresh.sh"
echo ""
echo "💡 Ou para um rebuild rápido:"
echo "   bash bash.bash"
echo ""
