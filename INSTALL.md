# 🚀 BTL (Backyard Trail League) - Guia de Instalação do Zero

Este guia detalha como instalar o sistema BTL completamente do zero, incluindo configuração de banco de dados, containers e dados iniciais.

## 📋 **Pré-requisitos**

- **Docker** versão 20.10 ou superior
- **Docker Compose** versão 2.0 ou superior
- **Git** para clonar o repositório

## 🔧 **Instalação Passo a Passo**

### **1. Clone o Repositório**
```bash
git clone <URL_DO_REPOSITORIO>
cd btl
```

### **2. Configuração dos Serviços**

O sistema utiliza os seguintes serviços:
- **MariaDB 11.4** - Banco de dados principal
- **MinIO** - Armazenamento de arquivos/imagens
- **phpMyAdmin** - Interface de administração do banco
- **BTL Backoffice** - Aplicação Flask principal

### **3. Build da Aplicação**

```bash
# Primeiro, construa a imagem da aplicação
docker build backoffice/ -t tcc-backoffice:latest --no-cache
```

### **4. Inicialização dos Containers**

```bash
# Suba todos os serviços
docker compose up -d
```

### **5. Verificação da Instalação**

Aguarde alguns segundos e verifique se todos os containers estão rodando:

```bash
docker compose ps
```

Você deve ver todos os containers com status "Up":
- `btl-mariadb`
- `btl-minio`
- `btl-phpmyadmin`
- `btl-backoffice`

## 🗄️ **Inicialização Automática do Banco de Dados**

### **O que acontece automaticamente:**

1. **Criação das Tabelas**: O arquivo `init_db.py` é executado automaticamente na inicialização
2. **Tabelas criadas**:
   - `profiles` - Perfis de usuário (Admin, Organizador)
   - `backend_users` - Usuários do sistema
   - `organizacoes` - Organizações
   - `backyards` - Eventos/Competições
   - `atletas` - Atletas participantes
   - `atleta_backyard` - Relação Many-to-Many entre atletas e backyards

3. **Dados Iniciais**:
   - **Perfil Admin** criado automaticamente
   - **Perfil Organizador** criado automaticamente
   - **Usuário Admin padrão** criado automaticamente

### **Credenciais do Usuário Admin Padrão:**
- **Email**: `admin@btl.com`
- **Senha**: `admin123`

## 🌐 **Acessos do Sistema**

Após a instalação, você pode acessar:

### **BTL Backoffice**
- **URL**: http://localhost:5555
- **Login**: admin@btl.com
- **Senha**: admin123

### **phpMyAdmin** (Administração do Banco)
- **URL**: http://localhost:8888
- **Host**: mariadb
- **Usuário**: btl_user
- **Senha**: btl_password

### **MinIO Console** (Armazenamento de Arquivos)
- **URL**: http://localhost:9001
- **Usuário**: minioadmin
- **Senha**: minioadmin123

## 🔧 **Configurações Importantes**

### **Variáveis de Ambiente (já configuradas no docker-compose.yaml):**

```yaml
# Banco de Dados
DB_HOST=mariadb
DB_PORT=3306
DB_USER=btl_user
DB_PASSWORD=btl_password
DB_NAME=btl_db

# MinIO (Armazenamento)
MINIO_ENDPOINT=minio:9000
MINIO_PUBLIC_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET=btl-images
```

## ✅ **Verificação da Instalação**

### **1. Teste de Conectividade**
```bash
# Verificar se a aplicação está respondendo
curl http://localhost:5555/health
```
Deve retornar: `OK`

### **2. Teste de Login**
1. Acesse http://localhost:5555
2. Faça login com admin@btl.com / admin123
3. Você deve ser redirecionado para o dashboard

### **3. Verificação do Banco**
```bash
# Executar comando no container do banco
docker compose exec mariadb mariadb -u btl_user -pbtl_password btl_db -e "SHOW TABLES;"
```

Deve mostrar todas as tabelas criadas.

## 🛠️ **Comandos Úteis**

### **Reiniciar apenas a aplicação:**
```bash
docker compose restart backoffice
```

### **Ver logs da aplicação:**
```bash
docker compose logs backoffice -f
```

### **Rebuild da aplicação após mudanças:**
```bash
docker build backoffice/ -t tcc-backoffice:latest --no-cache
docker compose restart backoffice
```

### **Parar todos os serviços:**
```bash
docker compose down
```

### **Parar e remover volumes (CUIDADO - perde dados!):**
```bash
docker compose down -v
```

## 🔄 **Processo de Inicialização Detalhado**

Quando você executa `docker compose up -d`, o seguinte acontece:

1. **MariaDB** inicia e cria o banco `btl_db`
2. **MinIO** inicia e fica disponível para armazenamento
3. **phpMyAdmin** se conecta ao MariaDB
4. **BTL Backoffice** inicia e:
   - Executa `python init_db.py` (cria tabelas e dados iniciais)
   - Inicia `python app.py` (servidor Flask)

## 🚨 **Solução de Problemas**

### **Problema: Container não inicia**
```bash
# Ver logs de erro
docker compose logs <nome_do_container>
```

### **Problema: Banco não conecta**
```bash
# Verificar se MariaDB está rodando
docker compose ps mariadb

# Testar conexão manual
docker compose exec mariadb mariadb -u btl_user -pbtl_password btl_db
```

### **Problema: Aplicação não carrega**
```bash
# Verificar logs da aplicação
docker compose logs backoffice

# Verificar se todas as dependências estão ok
docker compose ps
```

## 📊 **Estrutura Final**

Após instalação completa, você terá:

- ✅ **Sistema completo funcionando**
- ✅ **Banco de dados com todas as tabelas**
- ✅ **Usuário admin criado**
- ✅ **Armazenamento de imagens configurado**
- ✅ **Interface web acessível**

## 🎯 **Próximos Passos**

1. Faça login no sistema
2. Crie organizações
3. Crie backyards (eventos)
4. Cadastre atletas
5. Gerencie inscrições

---

### 💡 **Dica:**
Para uma instalação em produção, altere as senhas padrão e configure variáveis de ambiente seguras!
