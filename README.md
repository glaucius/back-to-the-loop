# BTL - Back to the Loop

## Sobre o Projeto

O **BTL (Back to the Loop)** é uma plataforma especializada para gerenciamento de corridas ultra backyard, desenvolvida como parte de um Trabalho de Conclusão de Curso (TCC). 

### O que são Backyard Ultras?

Backyard ultras são uma modalidade única de ultramaratona onde os competidores devem correr consecutivamente uma distância de **6,706 km (4,167 milhas)** em menos de uma hora. Eles devem repetir isso a cada hora até que apenas uma pessoa complete uma volta completa - o último em pé (last one standing).

Esta modalidade foi inventada por Gary "Lazarus Lake" Cantrell, também criador da famosa Barkley Marathons. O formato ganhou reputação por sua natureza brutal e imprevisível, além da camaraderie entre os participantes.

### Nossa Plataforma

O BTL facilita a organização e gestão destes eventos únicos, permitindo que organizadores criem e administrem corridas backyard ultra, controlem participantes, monitorem voltas e gerenciem todos os aspectos logísticos destes desafios de resistência extrema.

## 🚀 Funcionalidades

### Sistema de Gerenciamento Completo

#### 👥 **Gestão de Usuários e Perfis**
- **Usuários**: Criação, edição e listagem de usuários do sistema
- **Perfis**: Controle de permissões (Admin, Organizador)
- **Autenticação**: Login seguro com hash de senhas
- **Autorização**: Controle de acesso baseado em roles

#### 🏢 **Gestão de Organizações**
- Cadastro e gerenciamento de organizações de corrida
- Vinculação com usuários organizadores
- Controle de acesso por organização

#### 🏃‍♂️ **Sistema Completo de Backyard Ultras**

##### **Gestão de Eventos**
- **Criação de Backyards**: Configuração completa de eventos
- **Status em Tempo Real**: PREPARAÇÃO → ATIVO → FINALIZADO
- **Configuração de Percurso**: Distância padrão de 6,706 km
- **Gestão de Localização**: Endereço completo e georeferenciamento
- **Upload de Imagens**: Logos e fotos dos eventos via MinIO

##### **🎽 Sistema de Números de Peito**
- **Capacidade de Atletas**: Definição de máximo de participantes
- **Numeração Automática**: Atribuição sequencial de números
- **Número Inicial Configurável**: Flexibilidade na numeração (ex: 1, 100, 1001)
- **Geração sob Demanda**: Botão para gerar números quando necessário
- **Controle Visual**: Badges com números dos atletas

##### **⏱️ Gestão de Loops (Voltas)**
- **Controle de Voltas**: Loops sequenciais numerados
- **Timer Automático**: Cálculo preciso de tempos
- **Status por Loop**: PREPARAÇÃO → ATIVO → FINALIZADO
- **Qualificação Automática**: Apenas quem completa avança

##### **🏆 Sistema de Atletas**
- **Inscrições**: Relacionamento atletas ↔ backyards
- **Status em Tempo Real**:
  - ✅ **ATIVO**: Correndo o loop atual
  - 🏁 **CONCLUÍDO**: Terminou no tempo
  - ❌ **ELIMINADO**: Não completou no tempo
  - 🚪 **DESISTÊNCIA**: Saída voluntária
- **Controle de Chegada**: Botão "Chegou" com timestamp
- **Controle de Eliminação**: Botão "Eliminar" atleta

##### **🏅 Regras do Backyard Ultra**
- **Last One Standing**: Implementação fiel das regras oficiais
- **Loop Solo**: Evento só termina quando um atleta completa sozinho
- **Qualificação Automática**: Sistema inteligente de avanço
- **Cronometragem Precisa**: Tempos reais calculados automaticamente

#### 📊 **Dashboard e Monitoramento**
- **Painel ao Vivo**: Status em tempo real dos eventos
- **Estatísticas**: Métricas de atletas, loops e organizações
- **Filtros Inteligentes**: 
  - 🟢 Eventos AO VIVO (prioridade)
  - 🟡 Eventos em PREPARAÇÃO
  - 📅 Eventos futuros cronológicos
  - 📁 Eventos passados (filtro opcional)

#### 🎨 **Interface Moderna**
- **Design Responsivo**: AdminLTE Bootstrap
- **Tradução Completa**: Interface em Português Brasileiro
- **UX Otimizada**: Navegação intuitiva e eficiente
- **Feedback Visual**: Badges, cores e ícones informativos

#### 🆕 **Frontend para Atletas**
- **Portal Público**: Interface moderna e responsiva para atletas
- **Sistema de Cadastro**: Registro completo com validações
- **Login de Atletas**: Autenticação independente do backoffice
- **Upload de Fotos**: Imagens de perfil via MinIO
- **Dashboard Pessoal**: Painel com inscrições e estatísticas

#### 🆕 **Sistema de Inscrições Online**
- **Inscrições Abertas**: Atletas podem se inscrever em backyards disponíveis
- **Status de Inscrição**: inscrito, pendente, cancelado
- **Números de Peito**: Atribuição automática na inscrição
- **Gestão de Vagas**: Controle de capacidade máxima
- **Minhas Inscrições**: Visualização completa das participações

#### 🆕 **Visualização em Tempo Real**
- **Página Live**: Acompanhamento ao vivo de backyards ativas
- **Status dos Atletas**: 
  - 🏃 **CORRENDO**: Atletas ativos no loop atual
  - 🏁 **CHEGOU**: Atletas que completaram o loop (no topo)
  - ❌ **ELIMINADOS**: Histórico de eliminações
- **Detalhes dos Loops**: Visualização específica de cada volta
- **Estatísticas Dinâmicas**: Contadores em tempo real
- **Histórico Completo**: Todos os loops anteriores organizados

## 🏗️ Arquitetura

### Stack Tecnológica
- **Backend**: Python 3.11 + Flask
- **Banco de Dados**: MariaDB 11.4 + SQLAlchemy ORM
- **Armazenamento**: MinIO (S3-compatible)
- **Frontend**: HTML5 + CSS3 + JavaScript + Bootstrap 4
- **Containerização**: Docker + Docker Compose
- **Autenticação**: Flask-Login + Werkzeug Security

### Estrutura do Projeto
```
btl/
├── backoffice/                 # Aplicação Flask do painel administrativo
│   ├── app.py                 # Aplicação principal Flask
│   ├── models.py              # Modelos do banco de dados (SQLAlchemy)
│   ├── init_db.py             # Script de inicialização automática do banco
│   ├── init_minio.py          # Script de configuração do MinIO
│   ├── views/                 # Controllers organizados por módulos
│   │   ├── users.py           # Gestão de usuários
│   │   ├── profiles.py        # Gestão de perfis
│   │   ├── organizacoes.py    # Gestão de organizações
│   │   ├── backyards.py       # Gestão de backyards
│   │   ├── atletas.py         # Gestão de atletas
│   │   └── loops.py           # Gestão de loops e corridas
│   ├── templates/             # Templates HTML (Jinja2)
│   │   ├── base.html          # Template base
│   │   ├── dashboard.html     # Dashboard principal
│   │   ├── backyards/         # Templates de backyards
│   │   ├── loops/             # Templates de gestão de loops
│   │   ├── atletas/           # Templates de atletas
│   │   └── ...
│   ├── static/                # Arquivos estáticos
│   │   ├── css/               # Estilos customizados
│   │   ├── js/                # JavaScript
│   │   └── img/               # Imagens locais
│   ├── services/              # Serviços (upload, etc.)
│   │   └── image_service.py   # Integração com MinIO
│   ├── requirements.txt       # Dependências Python
│   └── Dockerfile             # Configuração do container
├── frontend/                   # 🆕 Aplicação Flask para atletas
│   ├── app.py                 # Aplicação principal do frontend
│   ├── models.py              # Modelos compartilhados com backoffice
│   ├── views/                 # Controllers do frontend
│   │   ├── auth.py            # Autenticação de atletas
│   │   ├── home.py            # Páginas públicas
│   │   ├── profile.py         # Perfil do atleta
│   │   └── backyards.py       # Visualização de eventos
│   ├── templates/             # Templates HTML modernas
│   │   ├── base.html          # Template base responsivo
│   │   ├── home/              # Páginas públicas
│   │   ├── auth/              # Login e registro
│   │   ├── profile/           # Dashboard do atleta
│   │   └── backyards/         # Visualizações de eventos
│   ├── static/                # Arquivos estáticos modernos
│   │   ├── css/               # Bootstrap customizado
│   │   ├── js/                # JavaScript interativo
│   │   └── vendor/            # Bibliotecas externas
│   ├── requirements.txt       # Dependências Python
│   └── Dockerfile             # Configuração do container
├── 🛠️ Scripts Utilitários:
├── setup_fresh.sh             # Setup completo do zero
├── build.sh                   # Rebuild rápido da aplicação
├── cleanup_total.sh           # Limpeza total do sistema Docker
├── test_minio.py              # Teste de configuração do MinIO
├── 📄 Documentação:
├── docker-compose.yaml        # Orquestração dos serviços
├── datamodel.txt              # Documentação do modelo de dados
├── INSTALL.md                 # Guia detalhado de instalação
├── APIS_GRATUITAS.md          # APIs utilizadas no projeto
└── README.md                  # Este arquivo
```

## 📋 Modelo de Dados

### Entidades Principais

#### **Backend_Users** (Usuários do Sistema)
- Controle de acesso administrativo
- Relacionamento com Profile (Admin/Organizador)
- Autenticação segura com hash de senhas

#### **Atleta** (Competidores)
- Dados pessoais completos
- Sistema próprio de autenticação
- Profile pictures via MinIO

#### **Backyard** (Eventos)
- Informações completas do evento
- **Campos de Números de Peito**:
  - `capacidade`: Máximo de atletas
  - `numero_inicial`: Primeiro número a ser atribuído
- Status do evento (PREPARACAO, ATIVO, FINALIZADO)
- Localização e imagens

#### **AtletaBackyard** (Inscrições)
- Relacionamento Many-to-Many atletas ↔ backyards
- **`numero_peito`**: Número único do atleta na prova
- Controle de inscrições

#### **Loop** (Voltas)
- Controle sequencial de loops (1, 2, 3...)
- Status e timestamps precisos
- Relacionamento com backyard

#### **AtletaLoop** (Participação)
- Participação de cada atleta em cada loop
- **Status detalhado**: ATIVO, CONCLUIDO, ELIMINADO, DESISTENCIA
- **Cronometragem**: `tempo_total_segundos` calculado automaticamente

### Enums de Status
```python
BackyardStatus: PREPARACAO, ATIVO, PAUSADO, FINALIZADO
LoopStatus: PREPARACAO, ATIVO, FINALIZADO  
AtletaLoopStatus: ATIVO, CONCLUIDO, ELIMINADO, DESISTENCIA
```

## 🚀 Instalação e Execução

### Pré-requisitos
- **Docker** e **Docker Compose** instalados
- **Git** para clonagem do repositório

### 1. Clone o Repositório
```bash
git clone <url-do-repositorio>
cd btl
```

### 2. Setup Automático (Recomendado)
```bash
# Setup completo do zero com aguardo de serviços
./setup_fresh.sh
```

**OU execução manual:**
```bash
# Construir e iniciar todos os serviços
docker compose up --build

# Para executar em background
docker compose up -d --build
```

> **🎯 Inicialização Automática**: O sistema cria automaticamente:
> - Todas as tabelas do banco de dados
> - Perfis padrão (Admin, Organizador)
> - Usuário admin: `admin@btl.com` / `admin123`
> - Bucket MinIO público configurado
> - Estrutura de pastas para imagens

### 3. Acesse os Serviços

- **🖥️ Backoffice** (Organizadores): http://localhost:5555
- **🏃‍♂️ Frontend** (Atletas): http://localhost:3000 🆕
- **🗄️ PhpMyAdmin**: http://localhost:8888
- **📁 MinIO Console**: http://localhost:9001
- **🔌 MinIO API**: http://localhost:9000

## 🔧 Configuração dos Serviços

### MariaDB
- **Porta Externa**: 33066
- **Banco**: btl_db
- **Usuário**: btl_user
- **Senha**: btl_password

### MinIO (Object Storage)
- **Console**: http://localhost:9001
- **API**: http://localhost:9000
- **Usuário**: minioadmin
- **Senha**: minioadmin123
- **Bucket**: btl-images (configurado automaticamente como público)
- **Estrutura de pastas**:
  ```
  btl-images/
  ├── backyards/profile_picture/
  ├── backyards/logo/
  ├── atletas/profile_picture/
  └── organizacoes/logo/
  ```

### PhpMyAdmin
- **URL**: http://localhost:8888
- **Usuário**: root
- **Senha**: rootpassword

## 👨‍💻 Desenvolvimento

### 🚀 Workflow de Desenvolvimento

#### **Setup Inicial (Primeira vez)**
```bash
# 1. Clone e entre no diretório
git clone <url-do-repositorio>
cd btl

# 2. Setup completo automático
./setup_fresh.sh

# 3. Acesse: http://localhost:5555
# Login: admin@btl.com / admin123
```

#### **Desenvolvimento Diário**
```bash
# Fazer mudanças no código...

# Rebuild rápido
./build.sh

# Ver logs se necessário
docker compose logs backoffice -f

# Teste funcionalidades
# Acesse: http://localhost:5555
```

#### **Quando algo der errado**
```bash
# 1. Restart simples
docker compose restart

# 2. Se persistir, rebuild completo
docker compose down
./setup_fresh.sh

# 3. Se ainda persistir, limpeza total
./cleanup_total.sh
./setup_fresh.sh
```

### Instalação Local (Desenvolvimento sem Docker)
```bash
cd backoffice
pip install -r requirements.txt
python init_minio.py  # Configurar MinIO
python init_db.py     # Inicializar banco
python app.py         # Executar aplicação
```

### 🛠️ Scripts Utilitários

O projeto inclui vários scripts para facilitar o desenvolvimento e manutenção:

#### **🚀 Scripts de Build e Deploy**
```bash
# Setup completo do zero (recomendado)
./setup_fresh.sh

# Rebuild rápido de ambas aplicações
./build_all.sh

# Rebuild apenas do backoffice
./build.sh

# Rebuild apenas do frontend 🆕
./build_frontend.sh

# Inicialização automática (já incluída no setup_fresh.sh)
docker compose up --build
```

#### **🧹 Scripts de Limpeza**
```bash
# Limpeza total do sistema Docker
./cleanup_total.sh

# Limpeza de volumes específicos
docker compose down -v
```

#### **📊 Scripts de Monitoramento**
```bash
# Logs da aplicação
docker compose logs backoffice

# Logs de todos os serviços
docker compose logs

# Status dos containers
docker compose ps

# Teste de conectividade MinIO
python test_minio.py
```

#### **💾 Scripts de Backup**
```bash
# Backup do banco de dados
docker exec btl-mariadb mysqldump -u btl_user -pbtl_password btl_db > backup.sql

# Backup completo com timestamp
docker exec btl-mariadb mysqldump -u btl_user -pbtl_password btl_db > "backup_$(date +%Y%m%d_%H%M%S).sql"
```

## 🔐 Controle de Acesso

### Perfis do Sistema

#### **👑 Administrador**
- ✅ Acesso completo a todas as funcionalidades
- ✅ Gestão de usuários, perfis, organizações
- ✅ Visualização global de todos os eventos
- ✅ Controle total do sistema

#### **🏃‍♂️ Organizador**
- ✅ Gestão das próprias organizações
- ✅ Criação e gestão de backyards vinculadas
- ✅ Controle completo de seus eventos
- ✅ Dashboard limitado aos seus dados

### Decoradores de Autorização
```python
@login_required                    # Usuário logado
@admin_required                   # Apenas administradores
@organizador_or_admin_required    # Organizadores e admins
```

## 🏃‍♂️ Regras do Backyard Ultra

### Funcionamento
1. **Loop Padrão**: 6,706 km em até 1 hora
2. **Largadas**: A cada hora em ponto
3. **Eliminação**: Quem não completa no tempo
4. **Qualificação**: Apenas quem termina avança
5. **Vitória**: Último atleta que completa um loop **sozinho**

### Implementação no Sistema
- ✅ **Cronometragem Automática**: Cálculo preciso de tempos
- ✅ **Regra do Loop Solo**: Vitória apenas com loop completado sozinho
- ✅ **Qualificação Automática**: Sistema inteligente de avanço
- ✅ **Status em Tempo Real**: Monitoramento contínuo

## 🎯 Funcionalidades por Tela

### 🖥️ **Backoffice** (http://localhost:5555)

#### 📊 Dashboard (`/`)
- Estatísticas gerais do sistema
- Ações rápidas (criar usuário, organização, backyard)
- Widgets com dados em tempo real

#### 🏃‍♂️ Gestão de Backyards (`/backyards/`)
- **Lista**: Filtros inteligentes, ordenação por prioridade
- **Criar**: Formulário completo com números de peito
- **Editar**: Atualização de todos os campos
- **Visualizar**: Detalhes completos em cards organizados

#### ⏱️ Gestão de Loops (`/loops/backyard/<id>`)
- **Painel ao Vivo**: Status em tempo real
- **Controle de Atletas**: Botões "Chegou" e "Eliminar"
- **Números de Peito**: Sistema visual com badges
- **Histórico**: Loops anteriores em ordem cronológica
- **Geração de Números**: Atribuição automática sob demanda

### 🏃‍♂️ **Frontend para Atletas** (http://localhost:3000) 🆕

#### 🏠 Home (`/`)
- **Landing Page**: Informações sobre backyard ultras
- **Próximos Eventos**: Lista de backyards disponíveis
- **Sobre**: Explicação da modalidade
- **Contato**: Formulário de contato

#### 🔐 Autenticação (`/auth/`)
- **Login** (`/auth/login`): Acesso de atletas cadastrados
- **Registro** (`/auth/register`): Cadastro completo com validações
- **Logout**: Encerramento seguro da sessão

#### 📋 Backyards (`/backyards/`)
- **Lista** (`/backyards/`): Eventos disponíveis para inscrição
- **Detalhes** (`/backyards/<id>`): Informações completas + inscrição
- **Live** (`/backyards/<id>/live`): Visualização em tempo real 🔥
- **Loop Específico** (`/backyards/<id>/loop/<loop_id>`): Detalhes do loop

#### 👤 Perfil (`/profile/`)
- **Dashboard** (`/profile/dashboard`): Resumo pessoal do atleta
- **Editar Perfil** (`/profile/edit`): Atualização de dados + foto
- **Minhas Inscrições** (`/profile/my-backyards`): Lista de participações
- **Alterar Senha** (`/profile/change-password`): Segurança da conta

## 🛠️ Troubleshooting

### Problemas Comuns

1. **Erro de conexão com banco**:
   ```bash
   docker compose logs mariadb
   ```

2. **Erro de upload de imagens**:
   ```bash
   docker compose logs minio
   ```

3. **Aplicação não inicia**:
   ```bash
   docker compose logs backoffice
   ```

### 🔄 Reinicialização e Limpeza

#### **Reinicialização Simples**
```bash
# Rebuild rápido da aplicação
./build.sh

# Restart apenas dos containers
docker compose restart
```

#### **Reinicialização Completa**
```bash
# Para volumes corrompidos ou problemas persistentes
docker compose down -v
docker compose up --build

# Setup completo do zero (recomendado)
./setup_fresh.sh
```

#### **Limpeza Total do Sistema**
```bash
# Remove TUDO: containers, volumes, networks, cache
./cleanup_total.sh

# Depois de limpar, recriar do zero
./setup_fresh.sh
```

> **⚠️ Atenção**: O `cleanup_total.sh` remove **TODOS** os containers, volumes e imagens Docker do sistema, não apenas do BTL!

## 📈 Roadmap

### ✅ Funcionalidades Implementadas
- [x] Sistema completo de usuários e perfis
- [x] Gestão de organizações
- [x] CRUD completo de backyards
- [x] Sistema de números de peito
- [x] Gestão de loops e cronometragem
- [x] Regras do Backyard Ultra
- [x] Interface traduzida para português
- [x] Upload de imagens via MinIO
- [x] Dashboard com estatísticas
- [x] **Frontend público para atletas** 🆕
- [x] **Sistema de inscrições online** 🆕
- [x] **Visualização em tempo real** 🆕
- [x] **Interface moderna para atletas** 🆕

### 🎯 Próximas Funcionalidades
- [ ] Relatórios em PDF
- [ ] API REST para integrações
- [ ] Notificações em tempo real
- [ ] Sistema de ranking
- [ ] Aplicativo móvel
- [ ] Streaming ao vivo

## 📄 Documentação

- **`datamodel.txt`**: Modelo de dados completo
- **`INSTALL.md`**: Instruções detalhadas de instalação
- **`APIS_GRATUITAS.md`**: APIs utilizadas no projeto
- **Código**: Comentários em português em todo o código

## 🏆 Licença

Este projeto é desenvolvido para fins acadêmicos como parte de um Trabalho de Conclusão de Curso (TCC).

---

**⚡ Versão**: 2.0  
**📅 Data**: 2024  
**🎓 Tipo**: Trabalho de Conclusão de Curso (TCC)  
**🇧🇷 Idioma**: Português Brasileiro

---

## 📚 Referências

- [Backyard Ultra Official Rules](https://backyardultra.com/) - Regras oficiais da modalidade
- Gary "Lazarus Lake" Cantrell - Criador do formato backyard ultra
- Big's Backyard Ultra - O evento original que inspirou a modalidade
- [Barkley Marathons](https://en.wikipedia.org/wiki/Barkley_Marathons) - Outro evento criado por Lazarus Lake