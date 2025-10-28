# 🚀 Guia de Deploy - Sistema SSO

## Deploy Local (Desenvolvimento)

### 1. Configuração Inicial
```bash
# Clone o repositório
git clone <repository-url>
cd sso-monitor

# Execute o script de setup
python setup.py

# Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas credenciais do Supabase
```

### 2. Configuração do Supabase
1. Acesse [supabase.com](https://supabase.com) e crie um projeto
2. Execute o script `database_setup.sql` no SQL Editor
3. Configure o Storage:
   - Crie um bucket chamado `evidencias`
   - Configure como privado
   - Limite de 50MB por arquivo
4. Configure OAuth Google (opcional):
   - Vá em Authentication > Providers > Google
   - Ative e configure com Client ID e Secret

### 3. Executar o Sistema
```bash
# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
streamlit run app.py
```

## Deploy no Streamlit Cloud

### 1. Preparação
1. Faça push do código para um repositório Git (GitHub, GitLab, etc.)
2. Certifique-se de que o arquivo `requirements.txt` está na raiz
3. Configure as variáveis de ambiente no Streamlit Cloud

### 2. Configuração no Streamlit Cloud
1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Conecte seu repositório
3. Configure as variáveis de ambiente:
   - `SUPABASE_URL`: Sua URL do Supabase
   - `SUPABASE_ANON_KEY`: Sua chave anônima do Supabase
4. Deploy!

### 3. Configuração de Secrets (Alternativa)
Crie um arquivo `.streamlit/secrets.toml` no repositório:

```toml
[supabase]
url = "https://your-project.supabase.co"
anon_key = "your-anon-key-here"
```

## Deploy em Servidor Próprio

### 1. Preparação do Servidor
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip nginx

# CentOS/RHEL
sudo yum install python3 python3-pip nginx
```

### 2. Configuração da Aplicação
```bash
# Clone o repositório
git clone <repository-url>
cd sso-monitor

# Instalar dependências
pip3 install -r requirements.txt

# Configurar variáveis de ambiente
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-key-here"
```

### 3. Configuração do Nginx
Crie `/etc/nginx/sites-available/sso-monitor`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Ative o site:
```bash
sudo ln -s /etc/nginx/sites-available/sso-monitor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Configuração do Systemd
Crie `/etc/systemd/system/sso-monitor.service`:

```ini
[Unit]
Description=Sistema SSO Monitor
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/sso-monitor
Environment=SUPABASE_URL=https://your-project.supabase.co
Environment=SUPABASE_ANON_KEY=your-anon-key-here
ExecStart=/usr/bin/python3 -m streamlit run app.py --server.port 8501
Restart=always

[Install]
WantedBy=multi-user.target
```

Ative o serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl enable sso-monitor
sudo systemctl start sso-monitor
```

## Deploy com Docker

### 1. Dockerfile
Crie um `Dockerfile` na raiz do projeto:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 2. Docker Compose
Crie `docker-compose.yml`:

```yaml
version: '3.8'

services:
  sso-monitor:
    build: .
    ports:
      - "8501:8501"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

### 3. Executar
```bash
# Construir e executar
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar
docker-compose down
```

## Deploy com Kubernetes

### 1. ConfigMap
Crie `k8s/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: sso-monitor-config
data:
  SUPABASE_URL: "https://your-project.supabase.co"
  SUPABASE_ANON_KEY: "your-anon-key-here"
```

### 2. Deployment
Crie `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sso-monitor
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sso-monitor
  template:
    metadata:
      labels:
        app: sso-monitor
    spec:
      containers:
      - name: sso-monitor
        image: your-registry/sso-monitor:latest
        ports:
        - containerPort: 8501
        envFrom:
        - configMapRef:
            name: sso-monitor-config
```

### 3. Service
Crie `k8s/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sso-monitor-service
spec:
  selector:
    app: sso-monitor
  ports:
  - port: 80
    targetPort: 8501
  type: LoadBalancer
```

## Monitoramento e Logs

### 1. Logs da Aplicação
```bash
# Streamlit logs
tail -f ~/.streamlit/logs/streamlit.log

# Systemd logs
journalctl -u sso-monitor -f

# Docker logs
docker logs -f sso-monitor
```

### 2. Métricas do Supabase
- Acesse o Dashboard do Supabase
- Monitore queries, storage, auth
- Configure alertas

### 3. Health Checks
```bash
# Verificar se a aplicação está rodando
curl http://localhost:8501/_stcore/health

# Verificar conectividade com Supabase
# Teste manual das funcionalidades do sistema
```

## Backup e Recuperação

### 1. Backup do Banco de Dados
```bash
# Via Supabase CLI
supabase db dump --file backup.sql

# Via pg_dump
pg_dump $DATABASE_URL > backup.sql
```

### 2. Backup do Storage
```bash
# Download de arquivos do bucket
gsutil -m cp -r gs://your-bucket/evidencias ./backup/
```

### 3. Backup do Código
```bash
# Git backup
git push origin main

# Tarball
tar -czf sso-monitor-$(date +%Y%m%d).tar.gz .
```

## Troubleshooting

### Problemas Comuns

1. **Erro de conexão com Supabase**
   - Verifique as variáveis de ambiente
   - Teste a conectividade de rede
   - Verifique as políticas RLS

2. **Erro de upload de arquivos**
   - Verifique o bucket do Storage
   - Verifique as permissões
   - Verifique o tamanho dos arquivos

3. **Performance lenta**
   - Verifique os índices do banco
   - Monitore o uso de memória
   - Otimize as queries

4. **Erro de autenticação**
   - Verifique as configurações OAuth
   - Verifique as políticas RLS
   - Verifique os tokens JWT

### Comandos Úteis

```bash
# Verificar status do serviço
systemctl status sso-monitor

# Reiniciar serviço
systemctl restart sso-monitor

# Ver logs em tempo real
journalctl -u sso-monitor -f

# Testar conectividade
# Execute o sistema e verifique as funcionalidades manualmente

# Verificar uso de recursos
htop
df -h
free -h
```

## Segurança

### 1. HTTPS
Configure SSL/TLS para produção:

```bash
# Certbot para Let's Encrypt
sudo certbot --nginx -d your-domain.com
```

### 2. Firewall
```bash
# UFW
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 3. Variáveis de Ambiente
- Nunca commite credenciais no Git
- Use secrets management
- Rotacione chaves regularmente

## Escalabilidade

### 1. Load Balancer
Configure nginx como load balancer:

```nginx
upstream sso_backend {
    server 127.0.0.1:8501;
    server 127.0.0.1:8502;
    server 127.0.0.1:8503;
}

server {
    listen 80;
    location / {
        proxy_pass http://sso_backend;
    }
}
```

### 2. Auto Scaling
Configure auto scaling no Kubernetes ou use ferramentas como:
- Horizontal Pod Autoscaler (K8s)
- AWS Auto Scaling Groups
- Google Cloud Auto Scaling

### 3. Cache
Implemente cache Redis para melhorar performance:

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_cached_data(key):
    cached = redis_client.get(key)
    return json.loads(cached) if cached else None

def set_cached_data(key, data, ttl=3600):
    redis_client.setex(key, ttl, json.dumps(data))
```
