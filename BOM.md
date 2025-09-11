# 📋 Bill of Materials (BOM) - BTL Platform

**Documento**: Bill of Materials  
**Projeto**: BTL - Back to the Loop
**Versão**: 1.0.0  
**Data**: 11 de Setembro de 2025  
**Descrição**: Plataforma completa para gestão de eventos Backyard Ultra  

---

## 🏗️ **Arquitetura da Aplicação**

### **Componentes Principais**
- **Frontend**: Interface web para atletas e público geral
- **Backoffice**: Sistema administrativo para organizadores
- **Database**: MariaDB para persistência de dados
- **Storage**: MinIO para armazenamento de imagens
- **Monitoring**: phpMyAdmin para administração do banco

### **Modelo de Deploy**
- **Containerização**: Docker & Docker Compose
- **Orquestração**: Docker Compose (desenvolvimento/produção)
- **Network**: Bridge network isolada (`btl_network`)

---

## 🐍 **Backend Dependencies (Python)**

### **Framework Principal**
| Componente | Versão | Backoffice | Frontend | Propósito |
|------------|---------|------------|----------|-----------|
| **Python** | 3.11-slim | ✅ | ✅ | Runtime base |
| **Flask** | 2.3.3 / 3.0.0 | ✅ | ✅ | Framework web |
| **Flask-SQLAlchemy** | 3.0.5 / 3.1.1 | ✅ | ✅ | ORM |
| **Flask-Login** | 0.6.3 | ✅ | ✅ | Autenticação |
| **Flask-WTF** | 1.1.1 | ✅ | ❌ | Forms & CSRF |
| **WTForms** | 3.0.1 | ✅ | ❌ | Validação de forms |

### **Database & Storage**
| Componente | Versão | Backoffice | Frontend | Propósito |
|------------|---------|------------|----------|-----------|
| **PyMySQL** | 1.1.0 | ✅ | ✅ | Driver MariaDB |
| **MinIO** | 7.2.0 | ✅ | ✅ | Cliente S3 |
| **cryptography** | 41.0.4 / 41.0.7 | ✅ | ✅ | Criptografia |

### **Utilities & Processing**
| Componente | Versão | Backoffice | Frontend | Propósito |
|------------|---------|------------|----------|-----------|
| **Pillow** | 10.0.1 / 10.1.0 | ✅ | ✅ | Processamento de imagens |
| **python-magic** | 0.4.27 | ✅ | ✅ | Detecção de tipos de arquivo |
| **python-dotenv** | 1.0.0 | ✅ | ❌ | Variáveis de ambiente |
| **email-validator** | 2.0.0 | ✅ | ❌ | Validação de email |

### **Production Server**
| Componente | Versão | Backoffice | Frontend | Propósito |
|------------|---------|------------|----------|-----------|
| **gunicorn** | 21.2.0 | ✅ | ❌ | WSGI Server |
| **Werkzeug** | 2.3.7 / 3.0.1 | ✅ | ✅ | WSGI utilities |

---

## 🐳 **Infrastructure & Containers**

### **Docker Images**
| Componente | Base Image | Versão | Recursos |
|------------|------------|---------|----------|
| **Application Containers** | `python:3.11-slim` | latest | Multi-stage, non-root user |
| **MariaDB** | `mariadb` | 11.4 | Persistência principal |
| **MinIO** | `minio/minio` | latest | Object storage |
| **phpMyAdmin** | `phpmyadmin/phpmyadmin` | latest | DB administration |

### **System Dependencies (apt-get)**
```bash
gcc                      # Compilador C
default-libmysqlclient-dev # Headers MySQL/MariaDB  
pkg-config              # Package configuration
curl                    # HTTP client
libmagic1               # File type detection
file                    # File utilities
```

### **Network & Volumes**
```yaml
Networks:
  - btl_network (bridge driver)

Volumes:
  - mariadb_data (database persistence)
  - minio_data (object storage persistence)
```

---

## 🎨 **Frontend Assets (JavaScript & CSS)**

### **CSS Frameworks & Libraries**
| Componente | Versão | Tamanho | Propósito |
|------------|---------|---------|-----------|
| **Bootstrap** | 5.x | ~200KB | Framework CSS principal |
| **Bootstrap Icons** | latest | ~200KB | Ícones |
| **AOS** | latest | ~15KB | Animações on scroll |
| **GLightbox** | latest | ~50KB | Lightbox para imagens |
| **Swiper** | latest | ~150KB | Carrossel/slider |

### **JavaScript Libraries**
| Componente | Versão | Tamanho | Propósito |
|------------|---------|---------|-----------|
| **Bootstrap Bundle** | 5.x | ~80KB | Interações Bootstrap |
| **Isotope Layout** | latest | ~50KB | Layout de grid |
| **ImagesLoaded** | latest | ~15KB | Carregamento de imagens |
| **PureCounter** | latest | ~10KB | Contador animado |

### **Custom Assets**
```
CSS:
  - main.css (tema personalizado)
  - bootstrap-custom.css (override de cores)

JavaScript:
  - main.js (funcionalidades globais)
  - password-validator.js (validação de senhas)
```

---

## 🧪 **Testing Dependencies**

### **Python Testing Stack**
| Componente | Versão | Propósito |
|------------|---------|-----------|
| **pytest** | 7.4.3 | Framework de testes |
| **pytest-flask** | 1.3.0 | Testes Flask |
| **pytest-cov** | 4.1.0 | Coverage |
| **pytest-mock** | 3.12.0 | Mocking |
| **pytest-xdist** | 3.5.0 | Testes paralelos |

### **Test Data & Utilities**
| Componente | Versão | Propósito |
|------------|---------|-----------|
| **factory-boy** | 3.3.0 | Factory de objetos |
| **faker** | 20.1.0 | Dados sintéticos |
| **pytest-postgresql** | 5.0.0 | DB temporário |
| **selenium** | 4.15.2 | Testes E2E |

### **JavaScript Testing**
| Componente | Versão | Propósito |
|------------|---------|-----------|
| **jest** | 29.7.0 | Framework de testes JS |
| **jest-environment-jsdom** | 29.7.0 | DOM simulation |
| **@testing-library/dom** | 9.3.3 | Testing utilities |
| **puppeteer** | 21.5.2 | Browser automation |

---

## 🗄️ **Database Schema**

### **Core Tables**
- **users** - Usuários do sistema
- **perfis** - Perfis/Roles
- **organizacoes** - Entidades organizadoras
- **backyards** - Eventos Backyard Ultra
- **atletas** - Atletas participantes
- **loops** - Voltas/loops dos eventos
- **atleta_backyard** - Inscrições
- **atleta_loop** - Participação em loops específicos

### **Storage Schema (MinIO)**
```
Bucket: btl-images
├── atletas/profile_picture/     # Fotos de perfil
├── backyards/images/           # Imagens dos eventos
└── organizacoes/logos/         # Logos das organizações
```

---

## 🔧 **Build & Deployment Tools**

### **Build Scripts**
| Script | Propósito |
|--------|-----------|
| **build.sh** | Build geral (backoffice) |
| **build_frontend.sh** | Build específico do frontend |
| **build_all.sh** | Build completo da plataforma |
| **cleanup_total.sh** | Limpeza completa |
| **setup_fresh.sh** | Setup inicial |

### **Testing Scripts**
| Script | Propósito |
|--------|-----------|
| **test_all.sh** | Execução de todos os testes |
| **tests/run_tests.sh** | Runner de testes isolado |

---

## 🌐 **Service Endpoints**

### **Development URLs**
| Serviço | URL | Propósito |
|---------|-----|-----------|
| **Frontend** | http://localhost:3000 | Interface pública |
| **Backoffice** | http://localhost:5555 | Administração |
| **MinIO Console** | http://localhost:9001 | Storage management |
| **phpMyAdmin** | http://localhost:8888 | DB administration |
| **MinIO API** | http://localhost:9000 | Object storage API |
| **MariaDB** | localhost:33066 | Database direct access |

---

## 📦 **Total Package Size Estimates**

| Categoria | Tamanho Estimado |
|-----------|------------------|
| **Python Dependencies** | ~150MB |
| **Docker Base Images** | ~500MB |
| **Frontend Assets** | ~2MB |
| **Static Images** | ~10MB |
| **Application Code** | ~5MB |
| **Total Runtime** | ~670MB |

---

## 🔐 **Security Components**

### **Authentication & Authorization**
- Flask-Login (session management)
- Password hashing (Werkzeug)
- CSRF protection (Flask-WTF)
- Role-based access control

### **Data Protection**
- SQL injection prevention (SQLAlchemy ORM)
- File upload validation (python-magic)
- Secure headers implementation
- Environment variable management

---

## 📄 **License & Attribution**

### **Open Source Components**
- **Flask**: BSD-3-Clause
- **Bootstrap**: MIT License
- **Docker**: Apache 2.0
- **MariaDB**: GPL v2
- **MinIO**: AGPL v3

### **Third-Party Assets**
- **Bootstrap Icons**: MIT License
- **AOS Library**: MIT License
- **Swiper**: MIT License
- **GLightbox**: MIT License

---

## 🚀 **Performance Characteristics**

### **Resource Requirements**
| Component | CPU | RAM | Storage |
|-----------|-----|-----|---------|
| **MariaDB** | 0.5 cores | 512MB | 2GB+ |
| **Backoffice** | 0.2 cores | 256MB | 100MB |
| **Frontend** | 0.2 cores | 256MB | 100MB |
| **MinIO** | 0.1 cores | 128MB | 1GB+ |

### **Scalability**
- **Horizontal**: Load balancer + multiple app instances
- **Vertical**: Resource increase per container
- **Database**: MariaDB clustering support
- **Storage**: MinIO distributed mode

---

**Gerado em**: 11/09/2025  
**Ferramenta**: BTL Platform BOM Generator  
**Contato**: Sistema BTL - Backyard Trail League
