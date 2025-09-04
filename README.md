# BTL - Back to the Loop

## Sobre o Projeto

O **BTL (Back to the Loop)** é uma plataforma especializada para gerenciamento de corridas ultra backyard, desenvolvida como parte de um Trabalho de Conclusão de Curso (TCC). 

### O que são Backyard Ultras?

Backyard ultras são uma modalidade única de ultramaratona onde os competidores devem correr consecutivamente uma distância de **6,706 km (4,167 milhas)** em menos de uma hora. Eles devem repetir isso a cada hora até que apenas uma pessoa complete uma volta completa - o último em pé (last one standing).

Esta modalidade foi inventada por Gary "Lazarus Lake" Cantrell, também criador da famosa Barkley Marathons. O formato ganhou reputação por sua natureza brutal e imprevisível, além da camaraderie entre os participantes.

### Nossa Plataforma

O BTL facilita a organização e gestão destes eventos únicos, permitindo que organizadores criem e administrem corridas backyard ultra, controlem participantes, monitorem voltas e gerenciem todos os aspectos logísticos destes desafios de resistência extrema.

## Funcionalidades

### Backoffice (Painel Administrativo)
- **Gestão de Usuários**: Criação, edição e listagem de usuários do sistema
- **Gestão de Perfis**: Controle de permissões (Admin, Organizador)
- **Gestão de Organizações**: Cadastro e gerenciamento de organizações de corrida
- **Gestão de Backyards**: Criação e administração de eventos backyard ultra
  - Configuração de percursos de 6,706 km
  - Definição de horários de largada (a cada hora)
  - Controle de voltas e tempo limite
  - Monitoramento do "last one standing"
- **Sistema de Autenticação**: Login seguro com controle de acesso baseado em roles
- **Upload de Imagens**: Integração com MinIO para armazenamento de fotos dos eventos e logos
- **Dashboard**: Visão geral com estatísticas dos eventos e participantes

## Arquitetura

### Stack Tecnológica
- **Backend**: Python + Flask
- **Banco de Dados**: MariaDB 11.4
- **Armazenamento de Arquivos**: MinIO
- **Interface**: HTML + CSS + JavaScript (Bootstrap)
- **Containerização**: Docker + Docker Compose
- **ORM**: SQLAlchemy
- **Autenticação**: Flask-Login

### Estrutura do Projeto
```
btl/
├── backoffice/                 # Aplicação Flask do painel administrativo
│   ├── app.py                 # Aplicação principal Flask
│   ├── models.py              # Modelos do banco de dados
│   ├── init_db.py             # Script de inicialização do banco
│   ├── views/                 # Controllers organizados por módulos
│   │   ├── users.py           # Gestão de usuários
│   │   ├── profiles.py        # Gestão de perfis
│   │   ├── organizacoes.py    # Gestão de organizações
│   │   └── backyards.py       # Gestão de backyards
│   ├── templates/             # Templates HTML
│   ├── static/                # Arquivos estáticos (CSS, JS, imagens)
│   ├── services/              # Serviços (upload de imagens, etc.)
│   ├── requirements.txt       # Dependências Python
│   └── Dockerfile             # Configuração do container
├── docker-compose.yaml        # Orquestração dos serviços
└── README.md                  # Este arquivo
```

## Modelo de Dados

### Entidades Principais

**Backend_Users**
- Usuários do sistema administrativo
- Relacionamento com Profile (roles/permissões)

**Profile**
- Perfis de acesso (Admin, Organizador)
- Controla permissões no sistema

**Organizacao**
- Organizações esportivas
- Vinculadas a usuários organizadores

**Backyard**
- Eventos de corrida backyard ultra
- Vinculados a organizações
- Controle de percurso (6,706 km por volta)
- Gestão de horários (largadas a cada hora)
- Monitoramento de participantes e voltas
- Suporte a upload de fotos e logos do evento

## Pré-requisitos

- **Docker** e **Docker Compose** instalados
- **Git** para clonagem do repositório

## Instalação e Execução

### 1. Clone o Repositório
```bash
git clone <url-do-repositorio>
cd btl
```

### 2. Configure as Variáveis de Ambiente
Edite o arquivo `docker-compose.yaml` e ajuste as seguintes variáveis conforme necessário:
- `SECRET_KEY`: Chave secreta para o Flask (mude em produção)
- Credenciais do banco de dados MariaDB
- Credenciais do MinIO

### 3. Execute com Docker Compose
```bash
# Construir e iniciar todos os serviços
docker-compose up --build

# Para executar em background
docker-compose up -d --build
```

### 4. Acesse os Serviços

- **Backoffice**: http://localhost:5555
- **PhpMyAdmin**: http://localhost:8888
- **MinIO Console**: http://localhost:9001
- **MinIO API**: http://localhost:9000

## Serviços Disponíveis

### MariaDB
- **Porta**: 33066 (externa), 3306 (interna)
- **Banco**: btl_db
- **Usuário**: btl_user
- **Senha**: btl_password

### MinIO (Object Storage)
- **Console**: http://localhost:9001
- **API**: http://localhost:9000
- **Usuário**: minioadmin
- **Senha**: minioadmin123

### PhpMyAdmin
- **URL**: http://localhost:8888
- **Host**: mariadb
- **Usuário**: root
- **Senha**: rootpassword

### Backoffice Flask
- **URL**: http://localhost:5555
- **Health Check**: http://localhost:5555/health

## Desenvolvimento

### Instalação Local (sem Docker)
```bash
cd backoffice
pip install -r requirements.txt
python init_db.py
python app.py
```

### Estrutura de Desenvolvimento
- **Models**: Definidos em `models.py` usando SQLAlchemy
- **Views**: Organizadas em blueprints na pasta `views/`
- **Templates**: Jinja2 templates em `templates/`
- **Static Files**: CSS, JS e imagens em `static/`

### Autenticação e Autorização
- Sistema baseado em roles (Admin, Organizador)
- Decoradores para controle de acesso:
  - `@admin_required`: Apenas administradores
  - `@organizador_or_admin_required`: Organizadores e administradores

## Funcionalidades por Perfil

### Administrador
- Acesso completo a todas as funcionalidades
- Gestão de usuários, perfis, organizações e eventos backyard ultra
- Visualização de estatísticas globais de todos os eventos
- Supervisão de recordes e performances

### Organizador
- Gestão das próprias organizações de corrida
- Criação e gestão de eventos backyard ultra vinculados às suas organizações
- Configuração de percursos e horários dos eventos
- Monitoramento de participantes e voltas durante as corridas
- Visualização limitada no dashboard (apenas seus eventos)

## Backup e Manutenção

### Backup do Banco de Dados
```bash
docker exec btl-mariadb mysqldump -u btl_user -pbtl_password btl_db > backup.sql
```

### Backup do MinIO
Os dados do MinIO são persistidos no volume `minio_data`.

### Logs
```bash
# Ver logs do backoffice
docker-compose logs backoffice

# Ver logs de todos os serviços
docker-compose logs
```

## Troubleshooting

### Problemas Comuns

1. **Erro de conexão com banco**:
   - Verifique se o MariaDB está rodando
   - Confirme as credenciais no docker-compose.yaml

2. **Erro de upload de imagens**:
   - Verifique se o MinIO está acessível
   - Confirme as credenciais do MinIO

3. **Porta já em uso**:
   - Altere as portas no docker-compose.yaml se necessário

### Reinicialização Completa
```bash
docker-compose down -v  # Remove volumes
docker-compose up --build
```

## Contribuição

Este é um projeto acadêmico (TCC). Para contribuições:

1. Fork o repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## Licença

Este projeto é desenvolvido para fins acadêmicos como parte de um Trabalho de Conclusão de Curso.

## Contato

Para dúvidas sobre o projeto, entre em contato através dos canais acadêmicos apropriados.

---

**Versão**: 1.0  
**Data**: 2024  
**Tipo**: Trabalho de Conclusão de Curso (TCC)

---

## Referências

- [Backyard Ultra - Wikipedia](https://en.wikipedia.org/wiki/Backyard_ultra) - Informações sobre a modalidade esportiva
- Gary "Lazarus Lake" Cantrell - Criador do formato backyard ultra
- Big's Backyard Ultra - O evento original que inspirou a modalidade
